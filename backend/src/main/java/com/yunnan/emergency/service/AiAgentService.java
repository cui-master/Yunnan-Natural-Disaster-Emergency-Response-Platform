package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import org.springframework.stereotype.Service;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * AI Agent 服务
 *
 * 编排三类 AI 任务，并通过 SSE 推送生成进度：
 *   1. 事件抽取（extract-incident）：从自然语言文本抽取结构化灾情事件
 *   2. 预案检索（retrieve-plans）：从知识库检索相关应急预案
 *   3. 方案审查（review-plan）：对生成的应急方案进行合规性与可行性审查
 *
 * 每个任务生成唯一 taskId，前端通过 SSE 订阅进度。
 * 调用 FastAPI AI 服务（Dify 工作流 / LLM），失败时自动重试。
 */
@Service
public class AiAgentService {
    public AiAgentService(AiService aiService, SseEmitterManager sseEmitterManager) {
        this.aiService = aiService;
        this.sseEmitterManager = sseEmitterManager;
    }


    private static final Logger log = LoggerFactory.getLogger(AiAgentService.class);

    private final AiService aiService;
    private final SseEmitterManager sseEmitterManager;

    /** 最大重试次数 */
    private static final int MAX_RETRIES = 3;

    /**
     * 事件抽取：从文本抽取结构化灾情信息
     *
     * @param text 原始上报文本
     * @return taskId（用于 SSE 订阅）
     */
    public String extractIncident(String text) {
        String taskId = "extract-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        Map<String, Object> params = new HashMap<>();
        params.put("text", text);
        params.put("task_id", taskId);
        executeWithRetry(taskId, "事件抽取", "/api/v1/agent/extract-incident", params);
        return taskId;
    }

    /**
     * 预案检索：从知识库检索相关应急预案
     *
     * @param query      查询条件（灾害类型、关键词等）
     * @param topK       返回条数
     * @return taskId
     */
    public String retrievePlans(String query, Integer topK) {
        String taskId = "retrieve-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        Map<String, Object> params = new HashMap<>();
        params.put("query", query);
        params.put("top_k", topK != null ? topK : 5);
        params.put("task_id", taskId);
        executeWithRetry(taskId, "预案检索", "/api/v1/agent/retrieve-plans", params);
        return taskId;
    }

    /**
     * 方案审查：对应急方案进行合规性与可行性审查
     *
     * @param planContent 方案内容
     * @param incidentId  关联灾情ID
     * @return taskId
     */
    public String reviewPlan(String planContent, Long incidentId) {
        String taskId = "review-" + UUID.randomUUID().toString().replace("-", "").substring(0, 12);
        Map<String, Object> params = new HashMap<>();
        params.put("plan_content", planContent);
        params.put("incident_id", incidentId);
        params.put("task_id", taskId);
        executeWithRetry(taskId, "方案审查", "/api/v1/agent/review-plan", params);
        return taskId;
    }

    /**
     * 同步调用事件抽取（阻塞返回结果，无 SSE）
     */
    public Map<String, Object> extractIncidentSync(String text) {
        Map<String, Object> params = new HashMap<>();
        params.put("text", text);
        return callAiWithRetry("事件抽取", "/api/v1/agent/extract-incident", params);
    }

    /**
     * 同步调用预案检索（阻塞返回结果，无 SSE）
     */
    public Map<String, Object> retrievePlansSync(String query, Integer topK) {
        Map<String, Object> params = new HashMap<>();
        params.put("query", query);
        params.put("top_k", topK != null ? topK : 5);
        return callAiWithRetry("预案检索", "/api/v1/agent/retrieve-plans", params);
    }

    /**
     * 同步调用方案审查（阻塞返回结果，无 SSE）
     */
    public Map<String, Object> reviewPlanSync(String planContent, Long incidentId) {
        Map<String, Object> params = new HashMap<>();
        params.put("plan_content", planContent);
        params.put("incident_id", incidentId);
        return callAiWithRetry("方案审查", "/api/v1/agent/review-plan", params);
    }

    /**
     * 同步调用风险评估（阻塞返回结果，无 SSE）
     *
     * 前端传入: { title, disaster_type, risk_level, location_name, description, occurred_at }
     * ai-service commander/review 期望: { area_name, disaster_type, description, risk_level }
     * ai-service 内部再映射为 Dify 工作流输入: { location_name, longitude, latitude, info, type, time }
     *
     * @param incidentInfo 灾情信息
     * @return 风险评估结果
     */
    public Map<String, Object> riskAssessSync(Map<String, Object> incidentInfo) {
        Map<String, Object> params = new HashMap<>();
        params.put("area_name", incidentInfo.getOrDefault("location_name", ""));
        params.put("disaster_type", incidentInfo.getOrDefault("disaster_type", ""));
        params.put("description", incidentInfo.getOrDefault("description", ""));
        params.put("risk_level", incidentInfo.getOrDefault("risk_level", "中"));
        // 经纬度选填，前端未传则为空
        if (incidentInfo.containsKey("longitude") && incidentInfo.get("longitude") != null) {
            params.put("longitude", incidentInfo.get("longitude"));
        }
        if (incidentInfo.containsKey("latitude") && incidentInfo.get("latitude") != null) {
            params.put("latitude", incidentInfo.get("latitude"));
        }
        return callAiWithRetry("风险评估", "/api/v1/commander/review", params);
    }

    /**
     * 异步执行 AI 任务，带 SSE 进度推送和异常重试
     */
    private void executeWithRetry(String taskId, String taskName, String path, Map<String, Object> params) {
        // 异步执行（@Async 配合 EnableAsync）
        new Thread(() -> {
            sseEmitterManager.sendProgress(taskId, "started", 0, taskName + "任务已启动", null);
            try {
                sseEmitterManager.sendProgress(taskId, "calling", 20, "正在调用AI服务...", null);

                Map<String, Object> result = callAiWithRetry(taskName, path, params);

                sseEmitterManager.sendProgress(taskId, "completed", 100,
                    taskName + "完成", result);
            } catch (Exception e) {
                log.error("[ai-agent] {} 任务失败: taskId={}, err={}", taskName, taskId, e.getMessage());
                sseEmitterManager.sendProgress(taskId, "error", 0,
                    taskName + "失败: " + e.getMessage(), null);
            }
        }, "ai-agent-" + taskId).start();
    }

    /**
     * 带重试的 AI 服务调用
     */
    private Map<String, Object> callAiWithRetry(String taskName, String path, Map<String, Object> params) {
        Exception lastError = null;
        for (int attempt = 1; attempt <= MAX_RETRIES; attempt++) {
            try {
                sseEmitterManager.sendProgress(
                    String.valueOf(params.get("task_id")),
                    "retrying", 20 + attempt * 20,
                    String.format("%s调用中（第%d次）", taskName, attempt), null);

                String response = aiService.post(path, params);
                log.info("[ai-agent] {} 调用成功，响应长度: {}", taskName,
                    response != null ? response.length() : 0);

                if (response == null || response.isEmpty()) {
                    throw new RuntimeException("AI服务返回空响应");
                }
                try {
                    return JSONUtil.parseObj(response);
                } catch (Exception e) {
                    // 非 JSON 响应，包装返回
                    Map<String, Object> wrapped = new HashMap<>();
                    wrapped.put("raw", response);
                    return wrapped;
                }
            } catch (Exception e) {
                lastError = e;
                log.warn("[ai-agent] {} 第{}次调用失败: {}", taskName, attempt, e.getMessage());
                if (attempt < MAX_RETRIES) {
                    try {
                        Thread.sleep(1000L * attempt); // 指数退避
                    } catch (InterruptedException ie) {
                        Thread.currentThread().interrupt();
                        throw new RuntimeException(taskName + "被中断", ie);
                    }
                }
            }
        }
        throw new RuntimeException(taskName + "重试" + MAX_RETRIES + "次后仍失败: " +
            (lastError != null ? lastError.getMessage() : "未知错误"), lastError);
    }
}
