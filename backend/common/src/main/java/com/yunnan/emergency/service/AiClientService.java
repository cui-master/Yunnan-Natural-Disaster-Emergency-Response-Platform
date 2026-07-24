package com.yunnan.emergency.service;

import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.AiPlan;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.IncidentReport;
import com.yunnan.emergency.entity.Location;
import com.yunnan.emergency.mapper.IncidentReportMapper;
import com.yunnan.emergency.mapper.LocationMapper;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.client.SimpleClientHttpRequestFactory;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * AI 服务调用客户端（独立 @Service，手动异常重试）。
 *
 * 对齐说明：组员的 AI_service 实际暴露的是
 *   POST /api/v1/workflow/run  (WorkflowRunRequest -> WorkflowRunResponse{result})
 * 并非最初约定的 /api/plan/generate。因此这里改为调用真实端点，
 * 并把返回的 result 文本映射为后端所需的 AiPlan（其余结构化字段留空，
 * PlanService 仅整体序列化 AiPlan 存 content，可容忍空字段）。
 *
 * 连接/读取超时 5s/120s（qwen-max 生成较慢，需放宽读超时），最多重试 3 次，退避 1s→2s→4s，
 * 耗尽后抛 BizException(502)，由调用方统一处理。
 */
@Service
public class AiClientService {

    @Value("${ai.service.url:http://localhost:8001}")
    private String aiUrl;

    @Autowired
    private LocationMapper locationMapper;
    @Autowired
    private IncidentReportMapper reportMapper;

    private RestTemplate buildRestTemplate() {
        SimpleClientHttpRequestFactory factory = new SimpleClientHttpRequestFactory();
        // qwen-max 预防方案 LLM 生成约 20~30s，读超时需放宽到 120s（匹配 SSE emitter 120s）
        factory.setConnectTimeout(5000);
        factory.setReadTimeout(120000);
        return new RestTemplate(factory);
    }

    public AiPlan call(Incident inc) {
        final int maxAttempts = 3;
        final long[] backoff = {1000, 2000, 4000};
        Exception last = null;
        for (int i = 0; i < maxAttempts; i++) {
            try {
                RestTemplate rt = buildRestTemplate();
                Map<String, Object> body = new HashMap<>();
                body.put("area_name", resolveAreaName(inc));
                body.put("disaster_type", inc.getType());
                body.put("risk_level", inc.getLevel());
                body.put("input_risk_info", buildRiskInfo(inc));
                body.put("vision_text", null);

                // 对齐 AI_service 真实端点：POST /api/v1/workflow/run
                Map resp = rt.postForObject(aiUrl + "/api/v1/workflow/run", body, Map.class);
                if (resp == null) {
                    throw new BizException(502, "AI 服务返回为空");
                }
                Object resultObj = resp.get("result");
                String result = resultObj == null ? null : resultObj.toString();
                if (result == null || result.isEmpty()) {
                    throw new BizException(502, "AI 服务未返回方案内容");
                }
                AiPlan ai = new AiPlan();
                ai.setTitle(inc.getTitle());
                ai.setContent(result);
                ai.setSteps(new ArrayList<>());
                ai.setResourceSuggestions(new ArrayList<>());
                ai.setCitations(new ArrayList<>());
                return ai;
            } catch (BizException be) {
                // 业务异常直接抛出，不参与重试
                throw be;
            } catch (Exception e) {
                last = e;
                if (i < maxAttempts - 1) {
                    try {
                        Thread.sleep(backoff[i]);
                    } catch (InterruptedException ignored) {
                        Thread.currentThread().interrupt();
                    }
                }
            }
        }
        throw new BizException(502, "AI 服务调用失败(已重试3次): " + (last == null ? "" : last.getMessage()));
    }

    /**
     * 解析灾情区域名（兜底链，确保 AI 收到的 area_name 不为空）：
     *   1) incident.locationId -> locations.name（若上报时未关联 location，则为 null）
     *   2) incident.reportId   -> incident_reports.location_text（前端填的 州市+区/县+具体位置）
     *   3) 最后回退到 incident.title
     */
    private String resolveAreaName(Incident inc) {
        if (inc.getLocationId() != null) {
            try {
                Location loc = locationMapper.selectById(inc.getLocationId());
                if (loc != null && loc.getName() != null && !loc.getName().isEmpty()) {
                    return loc.getName();
                }
            } catch (Exception ignored) {
                // 关联查不到不影响主流程
            }
        }
        if (inc.getReportId() != null) {
            try {
                IncidentReport rep = reportMapper.selectById(inc.getReportId());
                if (rep != null && rep.getLocationText() != null && !rep.getLocationText().isEmpty()) {
                    return rep.getLocationText();
                }
            } catch (Exception ignored) {
                // 查不到回退标题
            }
        }
        return inc.getTitle() != null ? inc.getTitle() : "";
    }

    /** 把标题+描述拼成 AI 需要的 input_risk_info */
    private String buildRiskInfo(Incident inc) {
        StringBuilder sb = new StringBuilder();
        if (inc.getTitle() != null) {
            sb.append(inc.getTitle()).append("。");
        }
        if (inc.getDescription() != null) {
            sb.append(inc.getDescription());
        }
        return sb.toString();
    }
}
