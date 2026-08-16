package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.service.ScheduledCollectionService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.web.bind.annotation.*;

import java.util.HashMap;
import java.util.Map;

/**
 * 定时任务管理控制器
 *
 * 提供定时采集任务的手动触发与状态查询接口。
 * 权限：仅管理员可操作。
 */
@Tag(name = "定时任务", description = "定时采集任务的手动触发与状态查询")
@RestController
@RequestMapping("/scheduler")
public class ScheduledTaskController {
    public ScheduledTaskController(ScheduledCollectionService scheduledCollectionService) {
        this.scheduledCollectionService = scheduledCollectionService;
    }


    private final ScheduledCollectionService scheduledCollectionService;

    @Operation(summary = "手动触发气象数据采集")
    @PostMapping("/trigger/weather")
    @PreAuthorize("hasAnyRole('ADMIN','RESMANAGER')")
    public Result<Map<String, Object>> triggerWeather() {
        return Result.success(scheduledCollectionService.triggerWeatherCollection());
    }

    @Operation(summary = "手动触发预警信息采集")
    @PostMapping("/trigger/warnings")
    @PreAuthorize("hasAnyRole('ADMIN','RESMANAGER')")
    public Result<Map<String, Object>> triggerWarnings() {
        return Result.success(scheduledCollectionService.triggerWarningCollection());
    }

    @Operation(summary = "获取定时任务列表与调度信息")
    @GetMapping("/tasks")
    @PreAuthorize("hasAnyRole('ADMIN')")
    public Result<Map<String, Object>> listTasks() {
        Map<String, Object> data = new HashMap<>();
        data.put("tasks", java.util.List.of(
            Map.of("name", "气象数据采集", "schedule", "每30分钟", "description", "采集云南主要城市天气"),
            Map.of("name", "预警信息采集", "schedule", "每15分钟", "description", "采集公开预警信息"),
            Map.of("name", "清理过期资源锁", "schedule", "每5分钟", "description", "释放超时未确认的资源锁"),
            Map.of("name", "归档历史灾情", "schedule", "每天02:00", "description", "归档已结束超30天的灾情")
        ));
        return Result.success(data);
    }
}
