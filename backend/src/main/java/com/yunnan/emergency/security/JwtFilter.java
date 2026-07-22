package com.yunnan.emergency.security;

import com.yunnan.emergency.common.BizException;
import io.jsonwebtoken.Claims;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Component;

import javax.servlet.Filter;
import javax.servlet.FilterChain;
import javax.servlet.ServletException;
import javax.servlet.ServletRequest;
import javax.servlet.ServletResponse;
import javax.servlet.http.HttpServletRequest;
import javax.servlet.http.HttpServletResponse;
import java.io.IOException;
import java.util.Arrays;
import java.util.List;

@Component
public class JwtFilter implements Filter {

    @Autowired
    private JwtUtil jwtUtil;

    private static final List<String> PERMIT = Arrays.asList(
            "/api/auth/login", "/v3/api-docs", "/swagger-ui", "/doc.html", "/ws/events");

    @Override
    public void doFilter(ServletRequest request, ServletResponse response, FilterChain chain)
            throws IOException, ServletException {
        HttpServletRequest req = (HttpServletRequest) request;
        HttpServletResponse res = (HttpServletResponse) response;
        String path = req.getServletPath();

        if (isPermit(path)) {
            try {
                chain.doFilter(request, response);
            } finally {
                UserContext.clear();
            }
            return;
        }

        String auth = req.getHeader("Authorization");
        try {
            if (auth == null || !auth.startsWith("Bearer ")) {
                throw new BizException(401, "未登录或令牌缺失");
            }
            Claims claims = jwtUtil.parse(auth.substring(7));
            LoginUser u = new LoginUser();
            u.setId(((Number) claims.get("uid")).longValue());
            u.setUsername(claims.getSubject());
            u.setRoleKey(claims.get("role", String.class));
            u.setRealName(claims.get("name", String.class));
            UserContext.set(u);
            chain.doFilter(request, response);
        } catch (BizException e) {
            writeUnauthorized(res, e.getMessage());
        } catch (Exception e) {
            writeUnauthorized(res, "令牌无效或已过期");
        } finally {
            UserContext.clear();
        }
    }

    private boolean isPermit(String path) {
        return PERMIT.stream().anyMatch(p -> path.equals(p) || path.startsWith(p));
    }

    private void writeUnauthorized(HttpServletResponse res, String msg) throws IOException {
        res.setStatus(401);
        res.setContentType("application/json;charset=utf-8");
        res.getWriter().write("{\"code\":401,\"message\":\"" + msg + "\"}");
    }
}
