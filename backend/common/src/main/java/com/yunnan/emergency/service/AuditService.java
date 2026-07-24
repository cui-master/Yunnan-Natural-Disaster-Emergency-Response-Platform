package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.QueryWrapper;
import com.baomidou.mybatisplus.core.metadata.IPage;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.BizException;
import com.yunnan.emergency.dto.AuditVO;
import com.yunnan.emergency.entity.AuditLog;
import com.yunnan.emergency.entity.Role;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mysql.mapper.AuditLogMapper;
import com.yunnan.emergency.mysql.mapper.RoleMapper;
import com.yunnan.emergency.mysql.mapper.UserMapper;
import com.yunnan.emergency.security.LoginUser;
import com.yunnan.emergency.security.UserContext;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.stereotype.Service;

import java.util.ArrayList;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

@Service
public class AuditService {

    @Autowired
    private AuditLogMapper auditLogMapper;
    @Autowired
    private UserMapper userMapper;
    @Autowired
    private RoleMapper roleMapper;

    private static final Map<String, String> MODULE_MAP = new HashMap<>();
    static {
        MODULE_MAP.put("REPORT_SUBMIT", "灾情上报");
        MODULE_MAP.put("REPORT_CONFIRM", "灾情审核");
        MODULE_MAP.put("LOGIN", "认证登录");
        MODULE_MAP.put("LOGOUT", "认证登出");
        MODULE_MAP.put("PLAN_GENERATE", "方案生成");
        MODULE_MAP.put("PLAN_APPROVE", "方案审批");
        MODULE_MAP.put("DISPATCH", "资源调度");
        MODULE_MAP.put("RESOURCE_CREATE", "资源管理");
        MODULE_MAP.put("USER_CREATE", "用户管理");
        MODULE_MAP.put("KB_UPLOAD", "知识库");
        MODULE_MAP.put("KB_DELETE", "知识库");
    }

    public Map<String, Object> list(String keyword, long page, long pageSize) {
        QueryWrapper<AuditLog> q = new QueryWrapper<>();
        if (keyword != null && !keyword.trim().isEmpty()) {
            q.like("username", keyword).or().like("action", keyword);
        }
        q.orderByDesc("created_at");
        Page<AuditLog> p = new Page<>(page, pageSize);
        IPage<AuditLog> res = auditLogMapper.selectPage(p, q);
        List<AuditLog> rows = res.getRecords();

        Map<Long, String> uidRole = new HashMap<>();
        for (User u : userMapper.selectList(null)) {
            Role r = u.getRoleId() != null ? roleMapper.selectById(u.getRoleId()) : null;
            uidRole.put(u.getId(), r == null ? null : r.getRoleKey());
        }

        List<AuditVO> vos = new ArrayList<>();
        for (AuditLog log : rows) {
            AuditVO v = new AuditVO();
            v.setId(log.getId());
            v.setOperator(log.getUsername());
            String roleKey = log.getUserId() != null ? uidRole.get(log.getUserId()) : null;
            if (roleKey == null) roleKey = inferByUsername(log.getUsername());
            v.setRole(stripPrefix(roleKey));
            v.setModule(MODULE_MAP.getOrDefault(log.getAction(), log.getAction()));
            v.setAction(log.getAction());
            v.setTarget(log.getTarget());
            v.setIp(log.getIp());
            v.setResult("SUCCESS");
            v.setDetail(log.getDetail());
            v.setCreatedAt(log.getCreatedAt());
            vos.add(v);
        }
        Map<String, Object> m = new HashMap<>();
        m.put("list", vos);
        m.put("total", res.getTotal());
        return m;
    }

    private static String stripPrefix(String rk) {
        if (rk != null && rk.startsWith("ROLE_")) return rk.substring(5);
        return rk;
    }

    private static String inferByUsername(String username) {
        if (username == null) return null;
        switch (username) {
            case "reporter": return "ROLE_REPORTER";
            case "commander": return "ROLE_COMMANDER";
            case "resmanager": return "ROLE_RESMGR";
            case "admin": return "ROLE_ADMIN";
            default: return null;
        }
    }

    public void log(String action, String target, String detail) {
        LoginUser u = UserContext.get();
        AuditLog log = new AuditLog();
        log.setUserId(u == null ? null : u.getId());
        log.setUsername(u == null ? null : u.getUsername());
        log.setAction(action);
        log.setTarget(target);
        log.setDetail(detail);
        auditLogMapper.insert(log);
    }
}
