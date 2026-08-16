package com.yunnan.emergency.security;

import com.fasterxml.jackson.databind.ObjectMapper;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.service.UserService;
import com.yunnan.emergency.utils.JwtUtils;
import jakarta.servlet.FilterChain;
import jakarta.servlet.ServletException;
import jakarta.servlet.http.HttpServletRequest;
import jakarta.servlet.http.HttpServletResponse;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.security.authentication.UsernamePasswordAuthenticationToken;
import org.springframework.security.core.authority.SimpleGrantedAuthority;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.filter.OncePerRequestFilter;

import java.io.IOException;
import java.util.Collections;

@Component
public class JwtAuthenticationFilter extends OncePerRequestFilter {
    public JwtAuthenticationFilter(JwtUtils jwtUtils, UserService userService, ObjectMapper objectMapper) {
        this.jwtUtils = jwtUtils;
        this.userService = userService;
        this.objectMapper = objectMapper;
    }


    private final JwtUtils jwtUtils;
    private final UserService userService;
    private final ObjectMapper objectMapper;

    @Value("${jwt.header}")
    private String header;

    @Value("${jwt.prefix}")
    private String prefix;

    @Override
    protected void doFilterInternal(HttpServletRequest request, HttpServletResponse response, FilterChain filterChain)
            throws ServletException, IOException {

        // 1. 优先从请求头读取 Token
        String authHeader = request.getHeader(header);
        String token = null;

        if (authHeader != null && authHeader.startsWith(prefix + " ")) {
            token = authHeader.substring(prefix.length() + 1);
        } else {
            // 2. WebSocket / SSE 场景：从 query 参数读取 Token
            //    浏览器 EventSource / WebSocket 无法自定义请求头，需通过 query 传递
            String queryToken = request.getParameter("token");
            if (queryToken != null && !queryToken.isEmpty()) {
                token = queryToken;
            }
        }

        if (token != null) {
            try {
                if (jwtUtils.validateToken(token)) {
                    Long userId = jwtUtils.getUserIdFromToken(token);
                    String roleCode = jwtUtils.getRoleCodeFromToken(token);

                    User user = userService.getUserInfo(userId);
                    if (user != null && user.getStatus() == 1) {
                        UsernamePasswordAuthenticationToken authentication =
                            new UsernamePasswordAuthenticationToken(
                                user,
                                null,
                                Collections.singletonList(new SimpleGrantedAuthority("ROLE_" + roleCode.toUpperCase()))
                            );
                        SecurityContextHolder.getContext().setAuthentication(authentication);
                    }
                }
            } catch (Exception e) {
                response.setContentType("application/json;charset=UTF-8");
                response.setStatus(HttpServletResponse.SC_UNAUTHORIZED);
                response.getWriter().write(objectMapper.writeValueAsString(Result.error(401, "Token无效或已过期")));
                return;
            }
        }

        filterChain.doFilter(request, response);
    }
}
