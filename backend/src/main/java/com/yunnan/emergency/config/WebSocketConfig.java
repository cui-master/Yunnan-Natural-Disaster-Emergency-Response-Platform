package com.yunnan.emergency.config;

import com.yunnan.emergency.websocket.EventStatusWebSocketHandler;
import org.springframework.context.annotation.Configuration;
import org.springframework.web.socket.config.annotation.EnableWebSocket;
import org.springframework.web.socket.config.annotation.WebSocketConfigurer;
import org.springframework.web.socket.config.annotation.WebSocketHandlerRegistry;

/**
 * WebSocket 配置
 *
 * 注册事件状态推送端点：ws://host/api/ws/events
 * 用于向大屏、指挥端实时推送：灾情工单流转、调度指令变更、资源锁定/释放等事件状态。
 */
@Configuration
@EnableWebSocket
public class WebSocketConfig implements WebSocketConfigurer {
    public WebSocketConfig(EventStatusWebSocketHandler eventStatusWebSocketHandler) {
        this.eventStatusWebSocketHandler = eventStatusWebSocketHandler;
    }


    private final EventStatusWebSocketHandler eventStatusWebSocketHandler;

    @Override
    public void registerWebSocketHandlers(WebSocketHandlerRegistry registry) {
        registry.addHandler(eventStatusWebSocketHandler, "/ws/events")
            .setAllowedOriginPatterns("*");
        //SockJS 兼容（可选）：.withSockJS();
    }
}
