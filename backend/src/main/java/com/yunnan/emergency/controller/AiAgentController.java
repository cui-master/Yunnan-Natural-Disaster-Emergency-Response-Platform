package com.yunnan.emergency.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.service.AiAgentService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * AI Agent 控制器
 *
 * 暴露三类 AI 任务的异步（带 SSE 进度）和同步接口：
 *   1. 事件抽取（extract-incident）
 *   2. 预案检索（retrieve-plans）
 *   3. 方案审查（review-plan）
 *
 * 异步接口返回 taskId，前端通过 SSE 订阅进度：
 *   EventSource('/api/sse/progress/{taskId}')
 */
@Tag(name = "AI Agent", description = "事件抽取、预案检索、方案审查")
@RestController
@RequestMapping("/ai/agent")
public class AiAgentController {
    public AiAgentController(AiAgentService aiAgentService) {
        this.aiAgentService = aiAgentService;
    }


    private static final Logger log = LoggerFactory.getLogger(AiAgentController.class);

    private final AiAgentService aiAgentService;

    // ========== 异步接口（带 SSE 进度推送） ==========

    @Operation(summary = "事件抽取（异步，返回 taskId 用于 SSE 订阅）")
    @PostMapping("/extract-incident")
    @PreAuthorize("hasAnyRole('REPORTER','COMMANDER')")
    public Result<Map<String, Object>> extractIncident(@RequestBody Map<String, String> body) {
        String text = body.get("text");
        if (text == null || text.isEmpty()) {
            return Result.error("文本内容不能为空");
        }
        String taskId = aiAgentService.extractIncident(text);
        Map<String, Object> data = new HashMap<>();
        data.put("taskId", taskId);
        data.put("sseUrl", "/sse/progress/" + taskId);
        return Result.success("事件抽取任务已提交", data);
    }

    @Operation(summary = "预案检索（异步，返回 taskId 用于 SSE 订阅）")
    @PostMapping("/retrieve-plans")
    @PreAuthorize("hasAnyRole('COMMANDER','ADMIN')")
    public Result<Map<String, Object>> retrievePlans(@RequestBody Map<String, Object> body) {
        String query = (String) body.get("query");
        Integer topK = body.get("top_k") != null ? ((Number) body.get("top_k")).intValue() : 5;
        if (query == null || query.isEmpty()) {
            return Result.error("查询条件不能为空");
        }
        String taskId = aiAgentService.retrievePlans(query, topK);
        Map<String, Object> data = new HashMap<>();
        data.put("taskId", taskId);
        data.put("sseUrl", "/sse/progress/" + taskId);
        return Result.success("预案检索任务已提交", data);
    }

    @Operation(summary = "方案审查（异步，返回 taskId 用于 SSE 订阅）")
    @PostMapping("/review-plan")
    @PreAuthorize("hasAnyRole('COMMANDER','ADMIN')")
    public Result<Map<String, Object>> reviewPlan(@RequestBody Map<String, Object> body) {
        String planContent = (String) body.get("plan_content");
        Long incidentId = body.get("incident_id") != null ? ((Number) body.get("incident_id")).longValue() : null;
        if (planContent == null || planContent.isEmpty()) {
            return Result.error("方案内容不能为空");
        }
        String taskId = aiAgentService.reviewPlan(planContent, incidentId);
        Map<String, Object> data = new HashMap<>();
        data.put("taskId", taskId);
        data.put("sseUrl", "/sse/progress/" + taskId);
        return Result.success("方案审查任务已提交", data);
    }

    // ========== 同步接口（直接返回结果） ==========

    @Operation(summary = "事件抽取（同步，直接返回结果）")
    @PostMapping("/extract-incident/sync")
    @PreAuthorize("hasAnyRole('REPORTER','COMMANDER')")
    public Result<Map<String, Object>> extractIncidentSync(@RequestBody Map<String, String> body) {
        String text = body.get("text");
        if (text == null || text.isEmpty()) {
            return Result.error("文本内容不能为空");
        }
        return Result.success(aiAgentService.extractIncidentSync(text));
    }

    @Operation(summary = "预案检索（同步，直接返回结果）")
    @PostMapping("/retrieve-plans/sync")
    @PreAuthorize("hasAnyRole('COMMANDER','ADMIN')")
    public Result<Map<String, Object>> retrievePlansSync(@RequestBody Map<String, Object> body) {
        String query = (String) body.get("query");
        Integer topK = body.get("top_k") != null ? ((Number) body.get("top_k")).intValue() : 5;
        if (query == null || query.isEmpty()) {
            return Result.error("查询条件不能为空");
        }
        return Result.success(aiAgentService.retrievePlansSync(query, topK));
    }

    @Operation(summary = "方案审查（同步，直接返回结果）")
    @PostMapping("/review-plan/sync")
    @PreAuthorize("hasAnyRole('COMMANDER','ADMIN')")
    public Result<Map<String, Object>> reviewPlanSync(@RequestBody Map<String, Object> body) {
        String planContent = (String) body.get("plan_content");
        Long incidentId = body.get("incident_id") != null ? ((Number) body.get("incident_id")).longValue() : null;
        if (planContent == null || planContent.isEmpty()) {
            return Result.error("方案内容不能为空");
        }
        return Result.success(aiAgentService.reviewPlanSync(planContent, incidentId));
    }

    @Operation(summary = "风险评估（同步，直接返回结果）")
    @PostMapping("/risk-assess/sync")
    @PreAuthorize("hasAnyRole('COMMANDER','ADMIN')")
    public Result<Map<String, Object>> riskAssessSync(@RequestBody Map<String, Object> body) {
        if (body == null || body.isEmpty()) {
            return Result.error("灾情信息不能为空");
        }
        return Result.success(aiAgentService.riskAssessSync(body));
    }
}
