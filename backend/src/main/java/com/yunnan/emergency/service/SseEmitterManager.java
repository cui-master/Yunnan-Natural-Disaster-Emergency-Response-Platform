package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.springframework.stereotype.Component;
import org.springframework.web.servlet.mvc.method.annotation.SseEmitter;

import java.io.IOException;
import java.util.Map;
import java.util.concurrent.ConcurrentHashMap;

/**
 * SSE Emitter 管理器
 *
 * 用于 AI 生成进度的流式推送（单向长连接）。
 * 每个生成任务对应一个 emitter，任务完成后关闭。
 *
 * 与 WebSocket 分工：
 *   - SSE：AI 生成进度（方案生成、事件抽取、预案检索等长任务的阶段性进度）
 *   - WebSocket：事件状态变更（灾情流转、调度变更等离散事件）
 */
@Component
public class SseEmitterManager {

    private static final Logger log = LoggerFactory.getLogger(SseEmitterManager.class);

    /** 任务ID -> SseEmitter */
    private final Map<String, SseEmitter> emitters = new ConcurrentHashMap<>();

    /** 默认超时：5 分钟（AI 生成可能较慢） */
    private static final long DEFAULT_TIMEOUT = 5 * 60 * 1000L;

    /**
     * 为指定任务创建 SSE 连接
     */
    public SseEmitter create(String taskId) {
        SseEmitter emitter = new SseEmitter(DEFAULT_TIMEOUT);
        emitters.put(taskId, emitter);

        emitter.onCompletion(() -> {
            emitters.remove(taskId);
            log.debug("[sse] 任务 {} 连接完成", taskId);
        });
        emitter.onTimeout(() -> {
            emitters.remove(taskId);
            log.debug("[sse] 任务 {} 连接超时", taskId);
        });
        emitter.onError(e -> {
            emitters.remove(taskId);
            log.warn("[sse] 任务 {} 连接错误: {}", taskId, e.getMessage());
        });

        log.info("[sse] 创建任务连接: taskId={}, 当前活跃={}", taskId, emitters.size());
        return emitter;
    }

    /**
     * 推送进度事件
     *
     * @param taskId   任务ID
     * @param stage    阶段：started / retrieving / generating / reviewing / completed / error
     * @param progress 进度百分比 0-100
     * @param message  提示信息
     * @param data     附加数据
     */
    public void sendProgress(String taskId, String stage, int progress, String message, Object data) {
        SseEmitter emitter = emitters.get(taskId);
        if (emitter == null) {
            log.debug("[sse] 任务 {} 无活跃连接，跳过推送", taskId);
            return;
        }
        try {
            Map<String, Object> payload = new java.util.HashMap<>();
            payload.put("taskId", taskId);
            payload.put("stage", stage);
            payload.put("progress", progress);
            payload.put("message", message);
            if (data != null) {
                payload.put("data", data);
            }
            payload.put("timestamp", System.currentTimeMillis());
            emitter.send(SseEmitter.event().name("progress").data(payload));
            log.debug("[sse] 推送 taskId={} stage={} progress={}%", taskId, stage, progress);

            // 完成或出错时关闭连接
            if ("completed".equals(stage) || "error".equals(stage)) {
                emitter.complete();
                emitters.remove(taskId);
            }
        } catch (IOException e) {
            log.warn("[sse] 推送失败 taskId={}: {}", taskId, e.getMessage());
            emitters.remove(taskId);
        }
    }

    /**
     * 主动关闭任务连接
     */
    public void complete(String taskId) {
        SseEmitter emitter = emitters.remove(taskId);
        if (emitter != null) {
            emitter.complete();
            log.info("[sse] 关闭任务连接: taskId={}", taskId);
        }
    }

    public int getActiveCount() {
        return emitters.size();
    }
}
