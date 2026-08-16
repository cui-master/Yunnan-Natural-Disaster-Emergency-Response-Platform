package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.mapper.IncidentMapper;
import org.springframework.scheduling.annotation.Scheduled;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 定时采集服务
 *
 * 定时采集公开预警和气象数据，并清理过期资源锁。
 *
 * 任务：
 *   1. 每 30 分钟采集云南省气象数据（调用 data-pipeline 爬虫）
 *   2. 每 15 分钟采集公开预警信息
 *   3. 每 5 分钟清理过期资源锁
 *   4. 每天 0 点归档已结束超 30 天的灾情
 *
 * 采集结果通过 WebSocket 推送给前端大屏。
 */
@Service
public class ScheduledCollectionService {
    public ScheduledCollectionService(DataPipelineService dataPipelineService, EventPushService eventPushService, ResourceLockService resourceLockService, IncidentMapper incidentMapper) {
        this.dataPipelineService = dataPipelineService;
        this.eventPushService = eventPushService;
        this.resourceLockService = resourceLockService;
        this.incidentMapper = incidentMapper;
    }


    private static final Logger log = LoggerFactory.getLogger(ScheduledCollectionService.class);

    private final DataPipelineService dataPipelineService;
    private final EventPushService eventPushService;
    private final ResourceLockService resourceLockService;
    private final IncidentMapper incidentMapper;

    /**
     * 定时采集气象数据（每 30 分钟）
     * 调用 data-pipeline 服务爬取云南主要城市天气
     */
    @Scheduled(fixedDelay = 30 * 60 * 1000L, initialDelay = 60 * 1000L)
    public void collectWeatherData() {
        log.info("[scheduler] 开始采集气象数据...");
        try {
            // 采集云南主要城市天气（曲靖、昆明、大理、丽江等）
            String[] cities = {"qujing", "kunming", "dali", "lijiang", "yuxi", "zhaotong"};
            int success = 0;
            for (String slug : cities) {
                try {
                    String result = dataPipelineService.get("/api/v1/weather/forecast/" + slug);
                    if (result != null && result.contains("forecast")) {
                        success++;
                    }
                } catch (Exception e) {
                    log.warn("[scheduler] 采集 {} 天气失败: {}", slug, e.getMessage());
                }
                // 限流，避免触发反爬
                Thread.sleep(1500);
            }

            // 推送采集完成事件
            Map<String, Object> payload = new HashMap<>();
            payload.put("task", "weather_collection");
            payload.put("total", cities.length);
            payload.put("success", success);
            payload.put("timestamp", LocalDateTime.now().toString());
            eventPushService.pushEventStatus("data_collection_complete", payload);

            log.info("[scheduler] 气象数据采集完成: 成功 {}/{}", success, cities.length);
        } catch (Exception e) {
            log.error("[scheduler] 气象数据采集异常: {}", e.getMessage());
        }
    }

    /**
     * 定时采集公开预警信息（每 15 分钟）
     * 调用 data-pipeline 服务采集云南预警
     */
    @Scheduled(fixedDelay = 15 * 60 * 1000L, initialDelay = 30 * 1000L)
    public void collectWarnings() {
        log.info("[scheduler] 开始采集公开预警信息...");
        try {
            String result = dataPipelineService.get("/api/v1/warnings/latest");
            log.info("[scheduler] 预警信息采集完成: {}", result != null ? "success" : "empty");

            // 推送预警更新事件
            Map<String, Object> payload = new HashMap<>();
            payload.put("task", "warning_collection");
            payload.put("status", "completed");
            payload.put("timestamp", LocalDateTime.now().toString());
            eventPushService.pushEventStatus("warning_update", payload);
        } catch (Exception e) {
            log.warn("[scheduler] 预警信息采集失败（服务可能未启用）: {}", e.getMessage());
        }
    }

    /**
     * 清理过期资源锁（每 5 分钟）
     */
    @Scheduled(fixedDelay = 5 * 60 * 1000L)
    public void cleanupExpiredLocks() {
        try {
            int count = resourceLockService.cleanupExpired();
            if (count > 0) {
                log.info("[scheduler] 清理过期资源锁: {} 个", count);
            }
        } catch (Exception e) {
            log.warn("[scheduler] 清理过期资源锁失败: {}", e.getMessage());
        }
    }

    /**
     * 归档已结束超 30 天的灾情（每天凌晨 2 点）
     */
    @Scheduled(cron = "0 0 2 * * ?")
    public void archiveOldIncidents() {
        log.info("[scheduler] 开始归档历史灾情...");
        try {
            LocalDateTime threshold = LocalDateTime.now().minusDays(30);
            // 查询已结束且更新时间超过 30 天的灾情
            var oldIncidents = incidentMapper.selectList(
                new LambdaQueryWrapper<Incident>()
                    .eq(Incident::getStatus, "已结束")
                    .lt(Incident::getUpdatedAt, threshold)
            );
            // 此处仅记录日志，实际归档可迁移到历史表
            log.info("[scheduler] 待归档历史灾情: {} 条", oldIncidents.size());
        } catch (Exception e) {
            log.warn("[scheduler] 归档历史灾情失败: {}", e.getMessage());
        }
    }

    /**
     * 手动触发气象采集（管理接口）
     */
    public Map<String, Object> triggerWeatherCollection() {
        log.info("[scheduler] 手动触发气象采集");
        new Thread(this::collectWeatherData).start();
        Map<String, Object> data = new HashMap<>();
        data.put("status", "triggered");
        data.put("timestamp", LocalDateTime.now().toString());
        return data;
    }

    /**
     * 手动触发预警采集（管理接口）
     */
    public Map<String, Object> triggerWarningCollection() {
        log.info("[scheduler] 手动触发预警采集");
        new Thread(this::collectWarnings).start();
        Map<String, Object> data = new HashMap<>();
        data.put("status", "triggered");
        data.put("timestamp", LocalDateTime.now().toString());
        return data;
    }
}
