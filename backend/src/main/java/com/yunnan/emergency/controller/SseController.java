package com.yunnan.emergency.controller;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.service.SseEmitterManager;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.util.HashMap;
import java.util.Map;
import java.util.UUID;

/**
 * SSE 推送控制器
 *
 * 用于 AI 生成进度的流式推送。
 * 前端通过 EventSource 连接 /sse/progress/{taskId} 接收实时进度。
 *
 * 典型流程：
 *   1. 前端调用 /ai/agent/extract-incident 等 AI 接口，获得 taskId
 *   2. 前端建立 EventSource(/sse/progress/{taskId})
 *   3. AI 服务通过 SseEmitterManager.sendProgress 推送进度
 *   4. 任务完成后 SSE 自动关闭
 */
@Tag(name = "SSE推送", description = "AI 生成进度 SSE 流式推送")
@RestController
@RequestMapping("/sse")
public class SseController {
    public SseController(SseEmitterManager sseEmitterManager) {
        this.sseEmitterManager = sseEmitterManager;
    }


    private static final Logger log = LoggerFactory.getLogger(SseController.class);

    private final SseEmitterManager sseEmitterManager;

    @Operation(summary = "订阅任务进度（SSE）")
    @GetMapping(value = "/progress/{taskId}", produces = "text/event-stream;charset=UTF-8")
    public SseEmitter subscribeProgress(@PathVariable String taskId) {
        log.info("[sse] 客户端订阅任务进度: taskId={}", taskId);
        return sseEmitterManager.create(taskId);
    }

    @Operation(summary = "创建新任务并返回 taskId")
    @PostMapping("/tasks")
    public Result<Map<String, Object>> createTask(@RequestParam(required = false) String taskType) {
        String taskId = "task-" + UUID.randomUUID().toString().replace("-", "").substring(0, 16);
        Map<String, Object> data = new HashMap<>();
        data.put("taskId", taskId);
        data.put("taskType", taskType != null ? taskType : "generic");
        data.put("createdAt", System.currentTimeMillis());
        return Result.success(data);
    }

    @Operation(summary = "获取 SSE 连接状态")
    @GetMapping("/status")
    public Result<Map<String, Object>> status() {
        Map<String, Object> data = new HashMap<>();
        data.put("activeEmitters", sseEmitterManager.getActiveCount());
        return Result.success(data);
    }
}
