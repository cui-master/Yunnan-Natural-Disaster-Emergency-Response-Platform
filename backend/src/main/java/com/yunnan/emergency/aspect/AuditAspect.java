package com.yunnan.emergency.aspect;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.annotation.AuditLog;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.AuditLogMapper;
import jakarta.servlet.http.HttpServletRequest;
import org.aspectj.lang.ProceedingJoinPoint;
import org.aspectj.lang.annotation.Around;
import org.aspectj.lang.annotation.Aspect;
import org.aspectj.lang.reflect.MethodSignature;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.stereotype.Component;
import org.springframework.web.context.request.RequestContextHolder;
import org.springframework.web.context.request.ServletRequestAttributes;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 操作审计切面
 *
 * 拦截标注了 @AuditLog 的方法，自动记录：
 *   - 操作人（从 SecurityContext 获取）
 *   - 操作模块、动作、描述
 *   - 请求 URL、方法、IP、User-Agent
 *   - 执行结果（success/fail）、耗时
 *   - 异常信息
 */
@Aspect
@Component
public class AuditAspect {
    public AuditAspect(AuditLogMapper auditLogMapper) {
        this.auditLogMapper = auditLogMapper;
    }


    private static final Logger log = LoggerFactory.getLogger(AuditAspect.class);

    private final AuditLogMapper auditLogMapper;

    @Around("@annotation(com.yunnan.emergency.annotation.AuditLog)")
    public Object around(ProceedingJoinPoint joinPoint) throws Throwable {
        MethodSignature signature = (MethodSignature) joinPoint.getSignature();
        com.yunnan.emergency.annotation.AuditLog anno = signature.getMethod()
            .getAnnotation(com.yunnan.emergency.annotation.AuditLog.class);

        long startTime = System.currentTimeMillis();
        String errorMsg = null;
        String result = "success";
        Object returnValue = null;

        try {
            returnValue = joinPoint.proceed();
            return returnValue;
        } catch (Throwable e) {
            errorMsg = e.getMessage();
            result = "fail";
            throw e;
        } finally {
            try {
                saveAuditLog(anno, startTime, errorMsg, result);
            } catch (Exception e) {
                log.warn("写入审计日志失败: {}", e.getMessage());
            }
        }
    }

    private void saveAuditLog(com.yunnan.emergency.annotation.AuditLog anno,
                              long startTime, String errorMsg, String result) {
        com.yunnan.emergency.entity.AuditLog auditLog = new com.yunnan.emergency.entity.AuditLog();

        // 操作人
        Authentication auth = SecurityContextHolder.getContext().getAuthentication();
        if (auth != null && auth.getPrincipal() instanceof User user) {
            auditLog.setUserId(user.getId());
            auditLog.setUsername(user.getUsername());
            auditLog.setRoleCode(user.getRoleCode());
        }

        auditLog.setModule(anno.module());
        auditLog.setAction(anno.action());
        auditLog.setTargetType(anno.targetType().isEmpty() ? anno.module() : anno.targetType());
        auditLog.setDescription(anno.description());
        auditLog.setResult(result);
        auditLog.setErrorMsg(errorMsg);
        auditLog.setDurationMs((int) (System.currentTimeMillis() - startTime));
        auditLog.setCreatedAt(LocalDateTime.now());

        // 请求信息
        ServletRequestAttributes attrs = (ServletRequestAttributes) RequestContextHolder.getRequestAttributes();
        if (attrs != null) {
            HttpServletRequest request = attrs.getRequest();
            auditLog.setRequestUrl(request.getRequestURI());
            auditLog.setRequestMethod(request.getMethod());
            auditLog.setIpAddress(getClientIp(request));
            auditLog.setUserAgent(request.getHeader("User-Agent"));
        }

        auditLogMapper.insert(auditLog);
    }

    private String getClientIp(HttpServletRequest request) {
        String ip = request.getHeader("X-Forwarded-For");
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getHeader("X-Real-IP");
        }
        if (ip == null || ip.isEmpty() || "unknown".equalsIgnoreCase(ip)) {
            ip = request.getRemoteAddr();
        }
        // 多级代理取第一个
        if (ip != null && ip.contains(",")) {
            ip = ip.split(",")[0].trim();
        }
        return ip;
    }
}
