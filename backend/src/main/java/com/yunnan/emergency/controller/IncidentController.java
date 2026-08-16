package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.annotation.AuditLog;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.mapper.ResourceMapper;
import com.yunnan.emergency.service.IncidentStateMachineService;
import com.yunnan.emergency.service.SqlNeo4jSyncService;
import com.yunnan.emergency.service.DisasterSituationService;
import com.yunnan.emergency.service.InfoService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDate;
import java.util.ArrayList;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Tag(name = "灾情事件管理", description = "灾情事件的查询、统计、状态机流转等")
@RestController
@RequestMapping("/incidents")
public class IncidentController {

    private final IncidentMapper incidentMapper;
    private final IncidentStateMachineService stateMachineService;
    private final SqlNeo4jSyncService sqlNeo4jSyncService;
    private final ResourceMapper resourceMapper;
    private final DisasterSituationService disasterSituationService;
    private final InfoService infoService;

    public IncidentController(IncidentMapper incidentMapper, IncidentStateMachineService stateMachineService, SqlNeo4jSyncService sqlNeo4jSyncService, ResourceMapper resourceMapper, DisasterSituationService disasterSituationService, InfoService infoService) {
        this.incidentMapper = incidentMapper;
        this.stateMachineService = stateMachineService;
        this.sqlNeo4jSyncService = sqlNeo4jSyncService;
        this.resourceMapper = resourceMapper;
        this.disasterSituationService = disasterSituationService;
        this.infoService = infoService;
    }

    @Operation(summary = "分页查询灾情事件")
    @GetMapping("/page")
    public Result<Page<Incident>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String disasterType,
            @RequestParam(required = false) String riskLevel,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<Incident> wrapper = new LambdaQueryWrapper<>();
        if (disasterType != null && !disasterType.isEmpty()) {
            wrapper.eq(Incident::getDisasterType, disasterType);
        }
        if (riskLevel != null && !riskLevel.isEmpty()) {
            wrapper.eq(Incident::getRiskLevel, riskLevel);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq(Incident::getStatus, status);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(Incident::getTitle, keyword).or().like(Incident::getLocationName, keyword);
        }
        wrapper.orderByDesc(Incident::getCreatedAt);

        Page<Incident> page = incidentMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取灾情事件详情")
    @GetMapping("/{id}")
    public Result<Incident> getById(@PathVariable Long id) {
        Incident incident = incidentMapper.selectById(id);
        return Result.success(incident);
    }

    @Operation(summary = "获取灾情工单可流转状态（状态机）")
    @GetMapping("/{id}/transitions")
    public Result<Map<String, Object>> getTransitions(@PathVariable Long id) {
        return stateMachineService.getTransitions(id);
    }

    @Operation(summary = "灾情工单状态流转（状态机校验）")
    @PutMapping("/{id}/transition")
    @AuditLog(module = "incident", action = "state_transition", description = "灾情工单状态流转")
    @PreAuthorize("hasAnyRole('COMMANDER','REPORTER')")
    public Result<Incident> transition(@PathVariable Long id,
                                        @RequestParam String targetStatus,
                                        @RequestParam(required = false) String reason,
                                        @AuthenticationPrincipal User user) {
        Result<Incident> result = stateMachineService.transition(id, targetStatus, user, reason);
        // SQL 写入成功后同步到 Neo4j
        if (result.getCode() == 200 && result.getData() != null) {
            try {
                sqlNeo4jSyncService.syncIncidentUpdate(result.getData());
            } catch (Exception e) {
                // Neo4j 同步失败不影响 SQL 主流程
            }
            // 状态变更后刷新灾情态势聚合表
            try { disasterSituationService.refresh(); } catch (Exception ignored) {}
        }
        return result;
    }

    @Operation(summary = "灾情态势大屏统计数据（优先从 info 表读取，兼容 disaster_situation 聚合表）")
    @GetMapping("/dashboard/stats")
    public Result<Map<String, Object>> getDashboardStats() {
        com.yunnan.emergency.entity.Info info = infoService.getOrInit();
        com.yunnan.emergency.entity.DisasterSituation ds = disasterSituationService.get();
        Map<String, Object> stats = new HashMap<>();

        // 大屏上方 6 个 KPI 严格读取 info 表，不回退到 disaster_situation
        int totalDisasters = info.getTotalDisasters() != null ? info.getTotalDisasters() : 0;
        int inProgress = info.getInProgress() != null ? info.getInProgress() : 0;
        int pending = info.getPending() != null ? info.getPending() : 0;
        int affectedPeople = info.getAffectedPeople() != null ? info.getAffectedPeople() : 0;
        int availableResources = info.getAvailableResources() != null ? info.getAvailableResources() : 0;
        int rescueTeams = info.getRescueTeams() != null ? info.getRescueTeams() : 0;

        stats.put("totalCount", totalDisasters);
        stats.put("pendingCount", pending);
        stats.put("confirmedCount", ds.getConfirmedCount());
        stats.put("processingCount", inProgress);
        stats.put("completedCount", ds.getCompletedCount());
        // 兼容旧字段名
        stats.put("activeCount", inProgress);
        stats.put("resolvedCount", ds.getCompletedCount());
        stats.put("totalDisasters", totalDisasters);
        stats.put("inProgress", inProgress);
        stats.put("pending", pending);
        stats.put("highRiskCount", ds.getHighRiskCount());
        stats.put("totalAffected", affectedPeople);
        stats.put("affectedPeople", affectedPeople);
        stats.put("availableResources", availableResources);
        stats.put("rescueTeams", rescueTeams);

        // 解析 JSON 字段（null 安全），类型分布过滤掉数量为 0 的项
        try {
            if (ds.getTypeDistribution() != null) {
                cn.hutool.json.JSONObject typeObj = cn.hutool.json.JSONUtil.parseObj(ds.getTypeDistribution());
                cn.hutool.json.JSONObject filtered = new cn.hutool.json.JSONObject();
                for (Map.Entry<String, Object> entry : typeObj.entrySet()) {
                    int count = entry.getValue() == null ? 0 : ((Number) entry.getValue()).intValue();
                    if (count > 0) {
                        filtered.set(entry.getKey(), count);
                    }
                }
                stats.put("typeStats", filtered);
            } else {
                stats.put("typeStats", new LinkedHashMap<>());
            }
        } catch (Exception ignored) { stats.put("typeStats", new LinkedHashMap<>()); }
        try {
            if (ds.getRealtimeEvents() != null) {
                @SuppressWarnings({"rawtypes", "unchecked"})
                List<Map<String, Object>> events = (List<Map<String, Object>>) (List) cn.hutool.json.JSONUtil.toList(ds.getRealtimeEvents(), Map.class);
                stats.put("activeIncidents", events);
            } else {
                stats.put("activeIncidents", new ArrayList<>());
            }
        } catch (Exception ignored) { stats.put("activeIncidents", new ArrayList<>()); }

        return Result.success(stats);
    }

    // 云南省 16 个地级行政区固定顺序（省会昆明在前，其余按常规行政区划顺序）
    private static final List<String> YUNNAN_CITIES = List.of(
            "昆明市", "曲靖市", "玉溪市", "保山市", "昭通市", "丽江市", "普洱市", "临沧市",
            "楚雄彝族自治州", "红河哈尼族彝族自治州", "文山壮族苗族自治州", "西双版纳傣族自治州",
            "大理白族自治州", "德宏傣族景颇族自治州", "怒江傈僳族自治州", "迪庆藏族自治州"
    );

    @Operation(summary = "获取各地市灾害数量（从 disaster_situation 聚合表，补齐云南省全部地市）")
    @GetMapping("/dashboard/city-count")
    public Result<List<Map<String, Object>>> getCityDisasterCount() {
        com.yunnan.emergency.entity.DisasterSituation ds = disasterSituationService.get();
        Map<String, Integer> cityCountMap = new LinkedHashMap<>();

        // 默认全部地市 count=0
        for (String city : YUNNAN_CITIES) {
            cityCountMap.put(city, 0);
        }

        try {
            if (ds.getCityDistribution() != null) {
                String json = ds.getCityDistribution();
                if (json.trim().startsWith("[")) {
                    // 数组格式 [{"city":"昆明市","count":1}]
                    @SuppressWarnings({"rawtypes", "unchecked"})
                    List<Map<String, Object>> list = (List<Map<String, Object>>) (List) cn.hutool.json.JSONUtil.toList(json, Map.class);
                    for (Map<String, Object> item : list) {
                        String city = String.valueOf(item.get("city"));
                        Object countObj = item.get("count");
                        int count = countObj == null ? 0 : ((Number) countObj).intValue();
                        cityCountMap.put(city, cityCountMap.getOrDefault(city, 0) + count);
                    }
                } else {
                    // 对象格式 {"昆明市":1}
                    cn.hutool.json.JSONObject obj = cn.hutool.json.JSONUtil.parseObj(json);
                    for (Map.Entry<String, Object> entry : obj.entrySet()) {
                        String city = entry.getKey();
                        int count = entry.getValue() == null ? 0 : ((Number) entry.getValue()).intValue();
                        cityCountMap.put(city, cityCountMap.getOrDefault(city, 0) + count);
                    }
                }
            }
        } catch (Exception ignored) {}

        List<Map<String, Object>> result = new ArrayList<>();
        for (String city : YUNNAN_CITIES) {
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("city", city);
            item.put("count", cityCountMap.getOrDefault(city, 0));
            result.add(item);
        }
        return Result.success(result);
    }

    @Operation(summary = "获取近7日灾害趋势（从 disaster_situation 聚合表）")
    @GetMapping("/dashboard/weekly-trend")
    public Result<List<Map<String, Object>>> getWeeklyTrend() {
        com.yunnan.emergency.entity.DisasterSituation ds = disasterSituationService.get();
        try {
            if (ds.getWeeklyTrend() != null) {
                @SuppressWarnings({"rawtypes", "unchecked"})
                List<Map<String, Object>> list = (List<Map<String, Object>>) (List) cn.hutool.json.JSONUtil.toList(ds.getWeeklyTrend(), Map.class);
                // 兼容 key "day" → "date"
                for (Map<String, Object> item : list) {
                    if (item.containsKey("day") && !item.containsKey("date")) {
                        item.put("date", item.remove("day"));
                    }
                }
                return Result.success(list);
            }
        } catch (Exception ignored) {}
        return Result.success(new ArrayList<>());
    }

    @Operation(summary = "获取实时事件列表")
    @GetMapping("/realtime")
    public Result<List<Incident>> getRealtimeIncidents(
            @RequestParam(defaultValue = "10") Integer limit) {
        List<Incident> list = incidentMapper.selectList(
            new LambdaQueryWrapper<Incident>()
                .orderByDesc(Incident::getCreatedAt)
                .last("LIMIT " + limit)
        );
        return Result.success(list);
    }

    @Operation(summary = "更新事件状态（已废弃，请使用 /{id}/transition）")
    @PutMapping("/{id}/status")
    @Deprecated
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam String status,
                                      @AuthenticationPrincipal User user) {
        Incident incident = incidentMapper.selectById(id);
        if (incident == null) {
            return Result.error("事件不存在");
        }
        incident.setStatus(status);
        incidentMapper.updateById(incident);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncIncidentUpdate(incident); } catch (Exception ignored) {}
        // 刷新灾情态势聚合表
        try { disasterSituationService.refresh(); } catch (Exception ignored) {}
        return Result.success();
    }
}
