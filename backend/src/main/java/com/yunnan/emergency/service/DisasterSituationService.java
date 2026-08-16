package com.yunnan.emergency.service;

import cn.hutool.json.JSONUtil;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.entity.DisasterSituation;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.mapper.DisasterSituationMapper;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.mapper.ResourceMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.util.*;
import java.util.stream.Collectors;

/**
 * 灾情态势聚合服务
 *
 * 从 incidents / resources 表实时聚合数据写入 disaster_situation 表。
 * 前端大屏直接读此表，审核通过/状态流转/资源变更时调 refresh() 刷新。
 */
@Slf4j
@Service
@RequiredArgsConstructor
public class DisasterSituationService {

    private final DisasterSituationMapper mapper;
    private final IncidentMapper incidentMapper;
    private final ResourceMapper resourceMapper;

    /** 获取当前态势（单行记录，id=1） */
    public DisasterSituation get() {
        DisasterSituation ds = mapper.selectById(1L);
        if (ds == null) {
            ds = refresh();
        }
        return ds;
    }

    /** 全量刷新：重新从 incidents/resources 聚合写入 disaster_situation */
    public DisasterSituation refresh() {
        log.info("[disaster-situation] 开始全量刷新");

        DisasterSituation ds = mapper.selectById(1L);
        if (ds == null) {
            ds = new DisasterSituation();
            ds.setId(1L);
        }

        // 1. 各状态计数（排除已归档）
        long totalCount = incidentMapper.selectCount(
            new LambdaQueryWrapper<Incident>().ne(Incident::getStatus, "已归档")
        );
        long pendingCount = countByStatus("待核验");
        long confirmedCount = countByStatus("已确认");
        long processingCount = countByStatus("处置中");
        long completedCount = countByStatus("已结束");

        ds.setTotalCount((int) totalCount);
        ds.setPendingCount((int) pendingCount);
        ds.setConfirmedCount((int) confirmedCount);
        ds.setProcessingCount((int) processingCount);
        ds.setCompletedCount((int) completedCount);

        // 2. 高风险未结束
        long highRiskCount = incidentMapper.selectCount(
            new LambdaQueryWrapper<Incident>()
                .in(Incident::getRiskLevel, "高", "特别重大")
                .ne(Incident::getStatus, "已结束")
                .ne(Incident::getStatus, "已归档")
        );
        ds.setHighRiskCount((int) highRiskCount);

        // 3. 受灾总人数
        List<Incident> activeIncidents = incidentMapper.selectList(
            new LambdaQueryWrapper<Incident>()
                .ne(Incident::getStatus, "已结束")
                .ne(Incident::getStatus, "已归档")
        );
        int totalAffected = activeIncidents.stream()
            .mapToInt(i -> i.getAffectedPeople() != null ? i.getAffectedPeople() : 0)
            .sum();
        ds.setTotalAffected(totalAffected);

        // 4. 可用资源数 / 救援队伍数
        long availableRes = resourceMapper.selectCount(
            new LambdaQueryWrapper<Resource>().eq(Resource::getStatus, 1)
        );
        long rescueTeams = resourceMapper.selectCount(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "team").eq(Resource::getStatus, 1)
        );
        ds.setAvailableResources((int) availableRes);
        ds.setRescueTeams((int) rescueTeams);

        // 5. 灾害类型分布（排除已归档）
        String[] types = {"地震", "山洪", "洪涝", "崩塌", "泥石流", "滑坡", "暴雨"};
        Map<String, Long> typeStats = new LinkedHashMap<>();
        for (String type : types) {
            typeStats.put(type, incidentMapper.selectCount(
                new LambdaQueryWrapper<Incident>()
                    .eq(Incident::getDisasterType, type)
                    .ne(Incident::getStatus, "已归档")
            ));
        }
        ds.setTypeDistribution(JSONUtil.toJsonStr(typeStats));

        // 6. 各地市灾害数量（排除已归档）
        List<Incident> allIncidents = incidentMapper.selectList(
            new LambdaQueryWrapper<Incident>().ne(Incident::getStatus, "已归档")
        );
        Map<String, Integer> cityCount = new LinkedHashMap<>();
        for (Incident inc : allIncidents) {
            String loc = inc.getLocationName();
            if (loc == null || loc.isEmpty()) continue;
            String city = extractCity(loc);
            if (city != null) {
                cityCount.merge(city, 1, Integer::sum);
            }
        }
        List<Map<String, Object>> cityList = cityCount.entrySet().stream()
            .sorted(Map.Entry.<String, Integer>comparingByValue().reversed())
            .map(e -> {
                Map<String, Object> m = new LinkedHashMap<>();
                m.put("city", e.getKey());
                m.put("count", e.getValue());
                return m;
            })
            .collect(Collectors.toList());
        ds.setCityDistribution(JSONUtil.toJsonStr(cityList));

        // 7. 近7日灾害趋势
        List<Map<String, Object>> weeklyTrend = new ArrayList<>();
        LocalDate today = LocalDate.now();
        for (int i = 6; i >= 0; i--) {
            LocalDate date = today.minusDays(i);
            String dateStr = date.toString();
            long count = incidentMapper.selectCount(
                new LambdaQueryWrapper<Incident>()
                    .apply("DATE(created_at) = {0}", dateStr)
                    .ne(Incident::getStatus, "已归档")
            );
            Map<String, Object> item = new LinkedHashMap<>();
            item.put("date", dateStr.substring(5));
            item.put("count", (int) count);
            weeklyTrend.add(item);
        }
        ds.setWeeklyTrend(JSONUtil.toJsonStr(weeklyTrend));

        // 8. 实时事件流（最新 20 条摘要，排除已归档）
        List<Incident> recentList = incidentMapper.selectList(
            new LambdaQueryWrapper<Incident>()
                .ne(Incident::getStatus, "已归档")
                .orderByDesc(Incident::getCreatedAt)
                .last("LIMIT 20")
        );
        List<Map<String, Object>> realtimeList = recentList.stream().map(inc -> {
            Map<String, Object> m = new LinkedHashMap<>();
            m.put("id", inc.getId());
            m.put("title", inc.getTitle());
            m.put("disasterType", inc.getDisasterType());
            m.put("riskLevel", inc.getRiskLevel());
            m.put("locationName", inc.getLocationName());
            m.put("lng", inc.getLng());
            m.put("lat", inc.getLat());
            m.put("status", inc.getStatus());
            m.put("occurredAt", inc.getOccurredAt());
            return m;
        }).collect(Collectors.toList());
        ds.setRealtimeEvents(JSONUtil.toJsonStr(realtimeList));

        ds.setRefreshedAt(java.time.LocalDateTime.now());

        // insertOrUpdate
        if (mapper.selectById(1L) == null) {
            mapper.insert(ds);
        } else {
            mapper.updateById(ds);
        }

        log.info("[disaster-situation] 刷新完成: total={}, pending={}, processing={}, completed={}",
            totalCount, pendingCount, processingCount, completedCount);
        return ds;
    }

    private long countByStatus(String status) {
        return incidentMapper.selectCount(
            new LambdaQueryWrapper<Incident>().eq(Incident::getStatus, status)
        );
    }

    private String extractCity(String loc) {
        int idx = loc.indexOf("市");
        if (idx > 0) return loc.substring(0, idx + 1);
        int idx2 = loc.indexOf("州");
        if (idx2 > 0) return loc.substring(0, idx2 + 1);
        if (loc.length() >= 2) return loc.substring(0, 2) + "市";
        return null;
    }
}
