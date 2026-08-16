package com.yunnan.emergency.controller;

import com.yunnan.emergency.annotation.AuditLog;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.DisasterSituation;
import com.yunnan.emergency.service.DisasterSituationService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

/**
 * 灾情态势聚合接口
 * 前端大屏直接从此接口读取，审核/流转/资源变更时自动刷新
 */
@Tag(name = "灾情态势", description = "灾情态势大屏数据（聚合表）")
@RestController
@RequestMapping("/disaster-situation")
@RequiredArgsConstructor
public class DisasterSituationController {

    private final DisasterSituationService service;

    @Operation(summary = "获取灾情态势数据")
    @GetMapping
    public Result<DisasterSituation> get() {
        return Result.success(service.get());
    }

    @Operation(summary = "手动刷新灾情态势（重新聚合）")
    @PostMapping("/refresh")
    @AuditLog(module = "disaster_situation", action = "refresh", description = "手动刷新灾情态势")
    @PreAuthorize("hasAnyRole('COMMANDER','ADMIN')")
    public Result<DisasterSituation> refresh() {
        return Result.success("刷新成功", service.refresh());
    }
}
