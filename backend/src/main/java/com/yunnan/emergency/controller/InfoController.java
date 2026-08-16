package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Info;
import com.yunnan.emergency.service.InfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.web.bind.annotation.*;

@Tag(name = "系统综合信息", description = "大屏 KPI 统计信息维护")
@RestController
@RequestMapping("/info")
public class InfoController {

    private final InfoService infoService;

    public InfoController(InfoService infoService) {
        this.infoService = infoService;
    }

    @Operation(summary = "获取系统综合信息")
    @GetMapping
    public Result<Info> get() {
        return Result.success(infoService.getOrInit());
    }

    @Operation(summary = "更新系统综合信息")
    @PutMapping
    public Result<?> update(@RequestBody Info info) {
        infoService.updateInfo(info);
        return Result.success();
    }
}
