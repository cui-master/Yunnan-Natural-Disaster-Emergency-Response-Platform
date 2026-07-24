package com.yunnan.emergency.service;

import com.yunnan.emergency.entity.AuditLog;
import com.yunnan.emergency.mapper.AuditLogMapper;
import com.yunnan.emergency.security.LoginUser;
import com.yunnan.emergency.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;

@Service
public class AuditService {

    @Autowired
    private AuditLogMapper auditLogMapper;

    public void log(String action, String target, String detail) {
        LoginUser u = UserContext.get();
        AuditLog log = new AuditLog();
        if (u != null) {
            log.setUserId(u.getId());
            log.setUsername(u.getUsername());
        }
        log.setAction(action);
        log.setTarget(target);
        log.setDetail(detail);
        log.setCreatedAt(LocalDateTime.now());
        auditLogMapper.insert(log);
    }

    public void logWithUser(Long userId, String username, String action, String target, String detail) {
        AuditLog log = new AuditLog();
        log.setUserId(userId);
        log.setUsername(username);
        log.setAction(action);
        log.setTarget(target);
        log.setDetail(detail);
        log.setCreatedAt(LocalDateTime.now());
        auditLogMapper.insert(log);
    }
}
