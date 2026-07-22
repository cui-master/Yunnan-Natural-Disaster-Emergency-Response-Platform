package com.yunnan.emergency.service;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.AiPlan;
import com.yunnan.emergency.dto.PlanApproveRequest;
import com.yunnan.emergency.entity.EmergencyPlan;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.mapper.EmergencyPlanMapper;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.security.Authz;
import com.yunnan.emergency.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.stereotype.Service;
import org.springframework.web.client.RestTemplate;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

@Service
public class PlanService {

    @Autowired
    private EmergencyPlanMapper planMapper;
    @Autowired
    private IncidentMapper incidentMapper;
    @Autowired
    private WebSocketService webSocketService;
    @Autowired
    private AuditService audit;

    @Value("${ai.service.url:http://localhost:8001}")
    private String aiUrl;

    private final ObjectMapper mapper = new ObjectMapper();

    public void generatePlanAsync(Long incidentId, Long operatorId, SseEmitter emitter) {
        new Thread(() -> {
            try {
                Incident inc = incidentMapper.selectById(incidentId);
                if (inc == null) {
                    emitter.send(SseEmitter.event().name("error").data("事件不存在"));
                    emitter.complete();
                    return;
                }
                emitter.send(SseEmitter.event().name("progress").data("正在核验事件信息..."));
                Thread.sleep(400);
                emitter.send(SseEmitter.event().name("progress").data("正在检索应急预案库(RAG)..."));
                Thread.sleep(400);
                AiPlan ai = callAi(inc);
                emitter.send(SseEmitter.event().name("progress").data("Agent 正在生成处置方案..."));
                Thread.sleep(300);
                EmergencyPlan plan = new EmergencyPlan();
                plan.setIncidentId(incidentId);
                plan.setTitle(ai.getTitle());
                plan.setContent(mapper.writeValueAsString(ai));
                plan.setStatus("DRAFT");
                plan.setGeneratedBy(operatorId);
                plan.setCreatedAt(LocalDateTime.now());
                planMapper.insert(plan);
                audit.log("PLAN_GENERATE", "plan:" + plan.getId(), "AI 生成处置方案");
                webSocketService.broadcast("PLAN_GENERATED", plan);
                emitter.send(SseEmitter.event().name("done").data(plan.getId()));
                emitter.complete();
            } catch (Exception e) {
                try {
                    emitter.send(SseEmitter.event().name("error").data(e.getMessage()));
                } catch (Exception ignored) {
                }
                emitter.completeWithError(e);
            }
        }).start();
    }

    public EmergencyPlan approve(Long id, String content) {
        Authz.require("ROLE_COMMANDER");
        EmergencyPlan p = planMapper.selectById(id);
        if (p == null) {
            throw new BizException(404, "方案不存在");
        }
        if (!"DRAFT".equals(p.getStatus())) {
            throw new BizException(400, "仅[草稿]方案可审批");
        }
        p.setContent(content);
        p.setStatus("APPROVED");
        p.setApprovedBy(UserContext.getUserId());
        p.setApprovedAt(LocalDateTime.now());
        planMapper.updateById(p);
        audit.log("PLAN_APPROVE", "plan:" + id, "审批处置方案");
        return p;
    }

    public EmergencyPlan detail(Long id) {
        return planMapper.selectById(id);
    }

    private AiPlan callAi(Incident inc) {
        RestTemplate rt = new RestTemplate();
        Map<String, Object> body = new HashMap<>();
        body.put("incidentId", inc.getId());
        body.put("title", inc.getTitle());
        body.put("type", inc.getType());
        body.put("level", inc.getLevel());
        body.put("description", inc.getDescription());
        try {
            return rt.postForEntity(aiUrl + "/api/plan/generate", body, AiPlan.class).getBody();
        } catch (Exception e) {
            throw new BizException(502, "AI 服务调用失败: " + e.getMessage());
        }
    }
}
