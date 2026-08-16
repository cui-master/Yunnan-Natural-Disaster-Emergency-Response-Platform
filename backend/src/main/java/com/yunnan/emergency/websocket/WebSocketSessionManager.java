package com.yunnan.emergency.websocket;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import cn.hutool.json.JSONUtil;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;

import java.io.IOException;
import java.util.Map;
import java.util.Set;
import java.util.concurrent.ConcurrentHashMap;

/**
 * WebSocket 会话管理器
 *
 * 维护所有已连接的客户端会话，提供广播能力。
 * 推送事件状态变更：灾情工单流转、调度指令变更、资源锁定/释放等。
 */
@Component
public class WebSocketSessionManager {

    private static final Logger log = LoggerFactory.getLogger(WebSocketSessionManager.class);

    /** 在线会话：sessionId -> session */
    private final Map<String, WebSocketSession> sessions = new ConcurrentHashMap<>();

    /** 订阅频道：sessionId -> 订阅类型集合（null 表示订阅全部） */
    private final Map<String, Set<String>> subscriptions = new ConcurrentHashMap<>();

    public void register(WebSocketSession session) {
        sessions.put(session.getId(), session);
        log.info("[ws] 客户端连接: id={}, 总在线={}", session.getId(), sessions.size());
    }

    public void unregister(WebSocketSession session) {
        sessions.remove(session.getId());
        subscriptions.remove(session.getId());
        log.info("[ws] 客户端断开: id={}, 总在线={}", session.getId(), sessions.size());
    }

    /**
     * 订阅指定类型
     */
    public void subscribe(String sessionId, String type) {
        subscriptions.computeIfAbsent(sessionId, k -> ConcurrentHashMap.newKeySet()).add(type);
    }

    /**
     * 向所有客户端（或订阅了该类型的客户端）广播消息
     */
    public void broadcast(String type, Map<String, Object> payload) {
        if (sessions.isEmpty()) {
            return;
        }
        Map<String, Object> message = Map.of(
            "type", type,
            "data", payload,
            "timestamp", System.currentTimeMillis()
        );
        String json = JSONUtil.toJsonStr(message);

        sessions.values().forEach(session -> {
            try {
                if (!session.isOpen()) {
                    return;
                }
                // 检查订阅：若客户端有订阅列表且不包含该类型，则跳过
                Set<String> subs = subscriptions.get(session.getId());
                if (subs != null && !subs.isEmpty() && !subs.contains(type)) {
                    return;
                }
                session.sendMessage(new TextMessage(json));
            } catch (IOException e) {
                log.warn("[ws] 发送消息失败: id={}, err={}", session.getId(), e.getMessage());
            }
        });
        log.debug("[ws] 广播 type={} 到 {} 个客户端", type, sessions.size());
    }

    public int getOnlineCount() {
        return sessions.size();
    }
}
