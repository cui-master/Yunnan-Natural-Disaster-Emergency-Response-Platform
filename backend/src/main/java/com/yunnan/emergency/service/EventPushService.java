package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.websocket.WebSocketSessionManager;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.Map;

/**
 * 事件状态推送服务（WebSocket）
 *
 * 负责向所有已连接的 WebSocket 客户端广播事件状态变更。
 * 与 {@link SseEmitterManager}（AI 生成进度 SSE）分工：
 *   - WebSocket：事件状态、灾情工单流转、调度指令变更
 *   - SSE：AI 生成进度（长连接、单向流式）
 */
@Service
public class EventPushService {

    private static final Logger log = LoggerFactory.getLogger(EventPushService.class);

    private final WebSocketSessionManager sessionManager;

    public EventPushService(@Autowired(required = false) WebSocketSessionManager sessionManager) {
        this.sessionManager = sessionManager;
    }

    /**
     * 推送事件状态变更
     *
     * @param type    事件类型，如 incident_status_change / dispatch_status_change / resource_lock_change
     * @param payload 负载
     */
    public void pushEventStatus(String type, Map<String, Object> payload) {
        if (sessionManager == null) {
            log.debug("WebSocket 管理器未启用，跳过广播: type={}", type);
            return;
        }
        try {
            sessionManager.broadcast(type, payload);
        } catch (Exception e) {
            log.warn("WebSocket 广播失败: type={}, err={}", type, e.getMessage());
        }
    }
}
