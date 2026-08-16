package com.yunnan.emergency.websocket;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import cn.hutool.json.JSONObject;
import cn.hutool.json.JSONUtil;
import org.springframework.stereotype.Component;
import org.springframework.web.socket.CloseStatus;
import org.springframework.web.socket.TextMessage;
import org.springframework.web.socket.WebSocketSession;
import org.springframework.web.socket.handler.TextWebSocketHandler;

import java.util.HashMap;
import java.util.Map;

/**
 * 事件状态 WebSocket 处理器
 *
 * 协议（客户端 → 服务端）：
 *   {"action":"subscribe","types":["incident_status_change","dispatch_status_change"]}
 *   {"action":"ping"}
 *
 * 协议（服务端 → 客户端）：
 *   {"type":"incident_status_change","data":{...},"timestamp":1700000000000}
 *   {"type":"pong","timestamp":1700000000000}
 *   {"type":"connected","sessionId":"xxx","online":3}
 */
@Component
public class EventStatusWebSocketHandler extends TextWebSocketHandler {
    public EventStatusWebSocketHandler(WebSocketSessionManager sessionManager) {
        this.sessionManager = sessionManager;
    }


    private static final Logger log = LoggerFactory.getLogger(EventStatusWebSocketHandler.class);

    private final WebSocketSessionManager sessionManager;

    @Override
    public void afterConnectionEstablished(WebSocketSession session) {
        sessionManager.register(session);
        // 发送连接确认
        Map<String, Object> welcome = new HashMap<>();
        welcome.put("type", "connected");
        welcome.put("sessionId", session.getId());
        welcome.put("online", sessionManager.getOnlineCount());
        try {
            session.sendMessage(new TextMessage(JSONUtil.toJsonStr(welcome)));
        } catch (Exception e) {
            log.warn("[ws] 发送欢迎消息失败: {}", e.getMessage());
        }
    }

    @Override
    protected void handleTextMessage(WebSocketSession session, TextMessage message) {
        String payload = message.getPayload();
        try {
            JSONObject json = JSONUtil.parseObj(payload);
            String action = json.getStr("action");
            switch (action == null ? "" : action) {
                case "subscribe" -> {
                    var types = json.getJSONArray("types");
                    if (types != null) {
                        types.forEach(t -> sessionManager.subscribe(session.getId(), String.valueOf(t)));
                    }
                    log.debug("[ws] 客户端 {} 订阅: {}", session.getId(), types);
                }
                case "ping" -> {
                    Map<String, Object> pong = new HashMap<>();
                    pong.put("type", "pong");
                    pong.put("timestamp", System.currentTimeMillis());
                    session.sendMessage(new TextMessage(JSONUtil.toJsonStr(pong)));
                }
                default -> log.debug("[ws] 未知 action: {}", action);
            }
        } catch (Exception e) {
            log.warn("[ws] 处理消息失败: payload={}, err={}", payload, e.getMessage());
        }
    }

    @Override
    public void afterConnectionClosed(WebSocketSession session, CloseStatus status) {
        sessionManager.unregister(session);
    }

    @Override
    public void handleTransportError(WebSocketSession session, Throwable exception) {
        log.warn("[ws] 传输错误: id={}, err={}", session.getId(), exception.getMessage());
        sessionManager.unregister(session);
    }
}
