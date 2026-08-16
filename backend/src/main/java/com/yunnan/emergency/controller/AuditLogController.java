package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.AuditLog;
import com.yunnan.emergency.mapper.AuditLogMapper;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

@Tag(name = "审计日志", description = "审计日志查询")
@RestController
@RequestMapping("/admin/audit-logs")
public class AuditLogController {
    public AuditLogController(AuditLogMapper auditLogMapper) {
        this.auditLogMapper = auditLogMapper;
    }


    private final AuditLogMapper auditLogMapper;

    @Operation(summary = "分页查询审计日志")
    @GetMapping("/page")
    public Result<Page<AuditLog>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String module,
            @RequestParam(required = false) String action,
            @RequestParam(required = false) String result,
            @RequestParam(required = false) Long userId,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<AuditLog> wrapper = new LambdaQueryWrapper<>();
        if (module != null && !module.isEmpty()) {
            wrapper.eq(AuditLog::getModule, module);
        }
        if (action != null && !action.isEmpty()) {
            wrapper.eq(AuditLog::getAction, action);
        }
        if (result != null && !result.isEmpty()) {
            wrapper.eq(AuditLog::getResult, result);
        }
        if (userId != null) {
            wrapper.eq(AuditLog::getUserId, userId);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(AuditLog::getDescription, keyword).or().like(AuditLog::getUsername, keyword);
        }
        wrapper.orderByDesc(AuditLog::getCreatedAt);

        Page<AuditLog> page = auditLogMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取日志详情")
    @GetMapping("/{id}")
    public Result<AuditLog> getById(@PathVariable Long id) {
        return Result.success(auditLogMapper.selectById(id));
    }

    @Operation(summary = "获取日志统计")
    @GetMapping("/stats")
    public Result<java.util.Map<String, Object>> getStats() {
        java.util.Map<String, Object> stats = new java.util.HashMap<>();

        Long total = auditLogMapper.selectCount(null);
        Long success = auditLogMapper.selectCount(
            new LambdaQueryWrapper<AuditLog>().eq(AuditLog::getResult, "success")
        );
        Long fail = auditLogMapper.selectCount(
            new LambdaQueryWrapper<AuditLog>().eq(AuditLog::getResult, "fail")
        );

        stats.put("total", total);
        stats.put("success", success);
        stats.put("fail", fail);

        // 模块统计
        String[] modules = {"auth", "incident", "resource", "plan", "system"};
        String[] moduleNames = {"认证", "灾情", "资源", "方案", "系统"};
        java.util.Map<String, Long> moduleStats = new java.util.HashMap<>();
        for (int i = 0; i < modules.length; i++) {
            Long count = auditLogMapper.selectCount(
                new LambdaQueryWrapper<AuditLog>().eq(AuditLog::getModule, modules[i])
            );
            moduleStats.put(moduleNames[i], count);
        }
        stats.put("moduleStats", moduleStats);

        return Result.success(stats);
    }
}
