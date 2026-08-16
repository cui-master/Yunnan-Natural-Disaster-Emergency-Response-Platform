package com.yunnan.emergency.service;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.mapper.ResourceMapper;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.*;

@Slf4j
@Service
@RequiredArgsConstructor
public class SqlNeo4jSyncService {

    private final Neo4jService neo4jService;
    private final IncidentMapper incidentMapper;
    private final ResourceMapper resourceMapper;

    public Map<String, Object> fullReSync() {
        log.info("[sync] 开始全量重新同步 MySQL -> Neo4j");
        neo4jService.clearAll();

        int incidents = syncAllIncidents();
        int warehouses = syncAllWarehouses();
        int teams = syncAllTeams();
        int shelters = syncAllShelters();

        Map<String, Object> result = new LinkedHashMap<>();
        result.put("incidents", incidents);
        result.put("warehouses", warehouses);
        result.put("teams", teams);
        result.put("shelters", shelters);
        result.put("syncTime", LocalDateTime.now().toString());
        log.info("[sync] 全量同步完成: {}", result);
        return result;
    }

    /**
     * 导出全量图谱数据（nodes + relationships），供调度方案工作流使用
     */
    public Map<String, Object> exportGraphData() {
        log.info("[export] 开始导出全量图谱数据");
        Map<String, Object> graph = neo4jService.exportAllGraph();
        log.info("[export] 导出完成: nodes={}, relationships={}",
            graph.get("nodeCount"), graph.get("relationshipCount"));
        return graph;
    }

    private int syncAllIncidents() {
        List<Incident> incidents = incidentMapper.selectList(
            new LambdaQueryWrapper<Incident>().eq(Incident::getStatus, "approved")
        );
        for (Incident incident : incidents) {
            try {
                syncIncidentCreate(incident);
            } catch (Exception e) {
                log.warn("[sync] 受灾点同步失败: incidentId={}, err={}", incident.getId(), e.getMessage());
            }
        }
        return incidents.size();
    }

    private int syncAllWarehouses() {
        List<Resource> warehouses = resourceMapper.selectList(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "warehouse")
        );
        for (Resource wh : warehouses) {
            try {
                syncWarehouse(wh);
            } catch (Exception e) {
                log.warn("[sync] 物资仓库同步失败: resourceNo={}, err={}", wh.getResourceNo(), e.getMessage());
            }
        }
        return warehouses.size();
    }

    private int syncAllTeams() {
        List<Resource> teams = resourceMapper.selectList(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "team")
        );
        for (Resource team : teams) {
            try {
                syncTeam(team);
            } catch (Exception e) {
                log.warn("[sync] 救援队伍同步失败: resourceNo={}, err={}", team.getResourceNo(), e.getMessage());
            }
        }
        return teams.size();
    }

    private int syncAllShelters() {
        List<Resource> shelters = resourceMapper.selectList(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "shelter")
        );
        for (Resource shelter : shelters) {
            try {
                syncShelter(shelter);
            } catch (Exception e) {
                log.warn("[sync] 避难场所同步失败: resourceNo={}, err={}", shelter.getResourceNo(), e.getMessage());
            }
        }
        return shelters.size();
    }

    public void syncIncidentCreate(Incident incident) {
        syncIncidentCreate(incident, null);
    }

    public void syncIncidentCreate(Incident incident, String roadName) {
        Map<String, Object> props = buildIncidentProps(incident);
        if (roadName != null && !roadName.isBlank()) {
            props.put("road", roadName);
        }
        neo4jService.createNode("受灾点", props);

        syncPlaceName(incident);
        syncDisasterType(incident);
        syncRiskLevel(incident);
        syncAffectedCount(incident);
    }

    public void syncIncidentUpdate(Incident incident) {
        // 更新受灾点：先删除旧节点（连带二级实体），再重新创建
        try {
            neo4jService.deleteNode("受灾点", incident.getId());
        } catch (Exception e) {
            log.warn("[sync] 更新受灾点-删除旧节点失败: incidentId={}, err={}", incident.getId(), e.getMessage());
        }
        // 只有状态为 approved 时才创建节点
        if ("approved".equals(incident.getStatus())) {
            syncIncidentCreate(incident);
        }
    }

    public void syncIncidentDelete(Long incidentId) {
        try {
            neo4jService.deleteNode("受灾点", incidentId);
        } catch (Exception e) {
            log.warn("[sync] 删除受灾点失败: incidentId={}, err={}", incidentId, e.getMessage());
        }
    }

    public void syncResourceCreate(Resource resource) {
        if (resource == null) return;
        String category = resource.getCategory();
        if ("warehouse".equals(category)) {
            syncWarehouse(resource);
        } else if ("team".equals(category)) {
            syncTeam(resource);
        } else if ("shelter".equals(category)) {
            syncShelter(resource);
        }
    }

    public void syncResourceUpdate(Resource resource) {
        syncResourceCreate(resource);
    }

    public void syncResourceDelete(Long id) {
        try {
            // 尝试按不同类别删除
            Resource r = resourceMapper.selectById(id);
            if (r != null) {
                neo4jService.deleteNode("物资仓库", r.getResourceNo());
                neo4jService.deleteNode("救援队伍", r.getResourceNo());
                neo4jService.deleteNode("避难场所", r.getResourceNo());
            }
        } catch (Exception e) {
            log.warn("[sync] 删除资源失败: id={}, err={}", id, e.getMessage());
        }
    }

    public void syncDispatchOrderCreate(Object order) {
        // 调度指令暂不同步详细节点
    }

    public void syncDispatchOrderUpdate(Object order) {
        // 调度指令暂不同步详细节点
    }

    public void syncDispatchOrderDelete(Long id) {
        // 调度指令暂不删除
    }

    public Map<String, Object> verifyConsistency() {
        Map<String, Object> report = new LinkedHashMap<>();
        long totalOrphans = 0;
        long totalMissing = 0;

        // 受灾点一致性
        Map<String, Object> incidentEntry = verifyLabelConsistency(
            "受灾点", "incidentId",
            incidentMapper.selectList(new LambdaQueryWrapper<Incident>().eq(Incident::getStatus, "approved"))
                .stream().map(Incident::getId).map(Object.class::cast).toList()
        );
        report.put("Incident", incidentEntry);
        totalOrphans += ((List<?>) incidentEntry.get("orphanIds")).size();
        totalMissing += ((List<?>) incidentEntry.get("missingInNeo4j")).size();

        // 物资仓库一致性
        List<Resource> warehouses = resourceMapper.selectList(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "warehouse"));
        Map<String, Object> whEntry = verifyLabelConsistency(
            "物资仓库", "resourceNo",
            warehouses.stream().map(Resource::getResourceNo).map(Object.class::cast).toList()
        );
        report.put("Warehouse", whEntry);
        totalOrphans += ((List<?>) whEntry.get("orphanIds")).size();
        totalMissing += ((List<?>) whEntry.get("missingInNeo4j")).size();

        // 救援队伍一致性
        List<Resource> teams = resourceMapper.selectList(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "team"));
        Map<String, Object> teamEntry = verifyLabelConsistency(
            "救援队伍", "resourceNo",
            teams.stream().map(Resource::getResourceNo).map(Object.class::cast).toList()
        );
        report.put("Team", teamEntry);
        totalOrphans += ((List<?>) teamEntry.get("orphanIds")).size();
        totalMissing += ((List<?>) teamEntry.get("missingInNeo4j")).size();

        // 避难场所一致性
        List<Resource> shelters = resourceMapper.selectList(
            new LambdaQueryWrapper<Resource>().eq(Resource::getCategory, "shelter"));
        Map<String, Object> shelterEntry = verifyLabelConsistency(
            "避难场所", "resourceNo",
            shelters.stream().map(Resource::getResourceNo).map(Object.class::cast).toList()
        );
        report.put("Shelter", shelterEntry);
        totalOrphans += ((List<?>) shelterEntry.get("orphanIds")).size();
        totalMissing += ((List<?>) shelterEntry.get("missingInNeo4j")).size();

        // Resource 条目（兼容旧测试）
        Map<String, Object> resourceEntry = new LinkedHashMap<>();
        long sqlResourceCount = warehouses.size() + teams.size() + shelters.size();
        long neo4jResourceCount = ((Number) whEntry.get("neo4jCount")).longValue()
            + ((Number) teamEntry.get("neo4jCount")).longValue()
            + ((Number) shelterEntry.get("neo4jCount")).longValue();
        resourceEntry.put("sqlCount", sqlResourceCount);
        resourceEntry.put("neo4jCount", neo4jResourceCount);
        resourceEntry.put("orphanIds", new ArrayList<>());
        resourceEntry.put("missingInNeo4j", new ArrayList<>());
        report.put("Resource", resourceEntry);

        // DispatchOrder 条目（暂不同步详细节点）
        Map<String, Object> orderEntry = new LinkedHashMap<>();
        orderEntry.put("sqlCount", 0);
        orderEntry.put("neo4jCount", 0);
        orderEntry.put("orphanIds", new ArrayList<>());
        orderEntry.put("missingInNeo4j", new ArrayList<>());
        report.put("DispatchOrder", orderEntry);

        Map<String, Object> summary = new LinkedHashMap<>();
        summary.put("totalOrphanInNeo4j", totalOrphans);
        summary.put("totalMissingInNeo4j", totalMissing);
        summary.put("consistent", totalOrphans == 0 && totalMissing == 0);
        report.put("_summary", summary);

        return report;
    }

    private Map<String, Object> verifyLabelConsistency(String label, String businessKey, List<Object> sqlIds) {
        Map<String, Object> entry = new LinkedHashMap<>();
        entry.put("sqlCount", sqlIds.size());
        try {
            long neo4jCount = neo4jService.countByLabel(label);
            entry.put("neo4jCount", neo4jCount);
            List<Object> neo4jIds = neo4jService.listBusinessIds(label, businessKey);
            List<Object> missingIds = sqlIds.stream()
                .filter(id -> !neo4jIds.contains(String.valueOf(id)) && !neo4jIds.contains(id))
                .toList();
            List<Long> orphanIds = neo4jService.findOrphanNodes(label, businessKey, sqlIds);
            entry.put("orphanIds", orphanIds);
            entry.put("missingInNeo4j", missingIds);
        } catch (Exception e) {
            log.warn("[verify] 校验标签 {} 失败: {}", label, e.getMessage());
            entry.put("neo4jCount", 0);
            entry.put("orphanIds", new ArrayList<>());
            entry.put("missingInNeo4j", new ArrayList<>());
            entry.put("error", e.getMessage());
        }
        return entry;
    }

    private Map<String, Object> buildIncidentProps(Incident incident) {
        Map<String, Object> props = new LinkedHashMap<>();
        props.put("incidentId", incident.getId());
        props.put("state", 1);
        props.put("name", incident.getTitle());
        props.put("location", incident.getLocationName() != null ? incident.getLocationName() : "");
        props.put("road", "");
        props.put("affectedPeople", incident.getAffectedPeople() != null ? incident.getAffectedPeople() : 0);
        props.put("riskLevelValue", mapRiskLevelToInt(incident.getRiskLevel()));
        props.put("disasterType", incident.getDisasterType());
        if (incident.getLng() != null) props.put("lng", incident.getLng().doubleValue());
        if (incident.getLat() != null) props.put("lat", incident.getLat().doubleValue());
        if (incident.getOccurredAt() != null) props.put("occurredAt", incident.getOccurredAt().toString());
        return props;
    }

    private Integer mapRiskLevelToInt(String level) {
        if (level == null) return null;
        return switch (level) {
            case "红色", "极高", "一级" -> 4;
            case "橙色", "高", "二级" -> 3;
            case "黄色", "中", "三级" -> 2;
            case "蓝色", "低", "四级" -> 1;
            default -> {
                try { yield Integer.parseInt(level.replaceAll("[^0-9]", "")); }
                catch (Exception e) { yield 2; }
            }
        };
    }

    private void syncPlaceName(Incident incident) {
        String loc = incident.getLocationName();
        if (loc == null || loc.isBlank()) return;

        try {
            Map<String, Object> locProps = new LinkedHashMap<>();
            locProps.put("name", loc);
            neo4jService.createNode("地点名称", locProps);

            neo4jService.createRelationship(
                "受灾点", incident.getId(),
                "地点名称", loc,
                "位于", Map.of()
            );
        } catch (Exception e) {
            log.warn("[sync] 地点名称同步失败: incidentId={}, location={}, err={}",
                incident.getId(), loc, e.getMessage());
        }
    }

    private void syncDisasterType(Incident incident) {
        String dtype = incident.getDisasterType();
        if (dtype == null || dtype.isBlank()) return;

        try {
            Map<String, Object> dtypeProps = new LinkedHashMap<>();
            dtypeProps.put("typeName", dtype);
            neo4jService.createNode("灾害类型", dtypeProps);

            neo4jService.createRelationship(
                "受灾点", incident.getId(),
                "灾害类型", dtype,
                "是", Map.of()
            );
        } catch (Exception e) {
            log.warn("[sync] 灾害类型同步失败: incidentId={}, type={}, err={}",
                incident.getId(), dtype, e.getMessage());
        }
    }

    private void syncRiskLevel(Incident incident) {
        String riskLevel = incident.getRiskLevel();
        if (riskLevel == null || riskLevel.isBlank()) return;
        Integer levelValue = mapRiskLevelToInt(riskLevel);
        if (levelValue == null) return;

        try {
            Map<String, Object> riskProps = new LinkedHashMap<>();
            riskProps.put("level", levelValue);
            riskProps.put("name", riskLevel);
            neo4jService.createNode("危险等级", riskProps);

            neo4jService.createRelationship(
                "受灾点", incident.getId(),
                "危险等级", levelValue,
                "具备", Map.of()
            );
        } catch (Exception e) {
            log.warn("[sync] 危险等级同步失败: incidentId={}, riskLevel={}, err={}",
                incident.getId(), riskLevel, e.getMessage());
        }
    }

    private void syncAffectedCount(Incident incident) {
        Integer count = incident.getAffectedPeople();
        if (count == null) return;

        try {
            Map<String, Object> countProps = new LinkedHashMap<>();
            countProps.put("value", count);
            countProps.put("incidentId", incident.getId());
            neo4jService.createNode("受灾人数", countProps);

            neo4jService.createRelationship(
                "受灾点", incident.getId(),
                "受灾人数", incident.getId(),
                "涉及", Map.of()
            );
        } catch (Exception e) {
            log.warn("[sync] 受灾人数同步失败: incidentId={}, count={}, err={}",
                incident.getId(), count, e.getMessage());
        }
    }

    private void syncWarehouse(Resource wh) {
        Map<String, Object> whProps = new LinkedHashMap<>();
        whProps.put("resourceNo", wh.getResourceNo());
        whProps.put("name", wh.getName());
        whProps.put("contact", wh.getContact());
        whProps.put("managerName", wh.getManagerName());
        whProps.put("location", wh.getLocationName() != null ? wh.getLocationName() : "");
        whProps.put("capacity", wh.getCapacity() != null ? wh.getCapacity() : 0);
        whProps.put("availableQty", wh.getAvailableQty() != null ? wh.getAvailableQty() : 0);
        whProps.put("status", wh.getStatus() != null ? wh.getStatus() : 0);
        if (wh.getLng() != null) whProps.put("lng", wh.getLng().doubleValue());
        if (wh.getLat() != null) whProps.put("lat", wh.getLat().doubleValue());
        neo4jService.createNode("物资仓库", whProps);

        // 物资仓库 -[:位于]-> 地点
        if (wh.getLocationName() != null && !wh.getLocationName().isBlank()) {
            try {
                Map<String, Object> locProps = new LinkedHashMap<>();
                locProps.put("name", wh.getLocationName());
                neo4jService.createNode("地点", locProps);
                neo4jService.createRelationship(
                    "物资仓库", wh.getResourceNo(),
                    "地点", wh.getLocationName(),
                    "位于", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 仓库地点同步失败: resourceNo={}, err={}", wh.getResourceNo(), e.getMessage());
            }
        }
    }

    private void syncTeam(Resource team) {
        Map<String, Object> teamProps = new LinkedHashMap<>();
        teamProps.put("resourceNo", team.getResourceNo());
        teamProps.put("name", team.getName());
        teamProps.put("contact", team.getContact());
        teamProps.put("managerName", team.getManagerName());
        teamProps.put("location", team.getLocationName() != null ? team.getLocationName() : "");
        teamProps.put("size", team.getCapacity() != null ? team.getCapacity() : 0);
        teamProps.put("availableSize", team.getAvailableQty() != null ? team.getAvailableQty() : 0);
        teamProps.put("isBusy", team.getStatus() != null && team.getStatus() == 1);
        teamProps.put("status", team.getStatus() != null ? team.getStatus() : 0);
        if (team.getLng() != null) teamProps.put("lng", team.getLng().doubleValue());
        if (team.getLat() != null) teamProps.put("lat", team.getLat().doubleValue());
        neo4jService.createNode("救援队伍", teamProps);

        // 救援队伍 -[:位于]-> 地点名称
        if (team.getLocationName() != null && !team.getLocationName().isBlank()) {
            try {
                Map<String, Object> locProps = new LinkedHashMap<>();
                locProps.put("name", team.getLocationName());
                neo4jService.createNode("地点名称", locProps);
                neo4jService.createRelationship(
                    "救援队伍", team.getResourceNo(),
                    "地点名称", team.getLocationName(),
                    "位于", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 队伍地点同步失败: resourceNo={}, err={}", team.getResourceNo(), e.getMessage());
            }
        }

        // 救援队伍 -[:是]-> 队伍类型
        if (team.getResourceType() != null && !team.getResourceType().isBlank()) {
            try {
                Map<String, Object> typeProps = new LinkedHashMap<>();
                typeProps.put("typeName", team.getResourceType());
                neo4jService.createNode("队伍类型", typeProps);
                neo4jService.createRelationship(
                    "救援队伍", team.getResourceNo(),
                    "队伍类型", team.getResourceType(),
                    "是", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 队伍类型同步失败: resourceNo={}, err={}", team.getResourceNo(), e.getMessage());
            }
        }

        // 救援队伍 -[:状态]-> 状态
        String statusName = (team.getStatus() != null && team.getStatus() == 1) ? "忙碌" : "空闲";
        try {
            Map<String, Object> statusProps = new LinkedHashMap<>();
            statusProps.put("name", statusName);
            neo4jService.createNode("状态", statusProps);
            neo4jService.createRelationship(
                "救援队伍", team.getResourceNo(),
                "状态", statusName,
                "状态", Map.of()
            );
        } catch (Exception e) {
            log.warn("[sync] 队伍状态同步失败: resourceNo={}, err={}", team.getResourceNo(), e.getMessage());
        }
    }

    private void syncShelter(Resource shelter) {
        Map<String, Object> shelterProps = new LinkedHashMap<>();
        shelterProps.put("resourceNo", shelter.getResourceNo());
        shelterProps.put("name", shelter.getName());
        shelterProps.put("contact", shelter.getContact());
        shelterProps.put("managerName", shelter.getManagerName());
        shelterProps.put("location", shelter.getLocationName() != null ? shelter.getLocationName() : "");
        shelterProps.put("maxCapacity", shelter.getCapacity() != null ? shelter.getCapacity() : 0);
        shelterProps.put("currentOccupancy", 0);
        shelterProps.put("remainingCapacity", shelter.getAvailableQty() != null ? shelter.getAvailableQty() : (shelter.getCapacity() != null ? shelter.getCapacity() : 0));
        shelterProps.put("status", shelter.getStatus() != null ? shelter.getStatus() : 0);
        if (shelter.getLng() != null) shelterProps.put("lng", shelter.getLng().doubleValue());
        if (shelter.getLat() != null) shelterProps.put("lat", shelter.getLat().doubleValue());
        neo4jService.createNode("避难场所", shelterProps);

        // 避难场所 -[:是]-> 场所名称
        if (shelter.getName() != null && !shelter.getName().isBlank()) {
            try {
                Map<String, Object> nameProps = new LinkedHashMap<>();
                nameProps.put("name", shelter.getName());
                neo4jService.createNode("场所名称", nameProps);
                neo4jService.createRelationship(
                    "避难场所", shelter.getResourceNo(),
                    "场所名称", shelter.getName(),
                    "是", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 避难场所名称同步失败: resourceNo={}, err={}", shelter.getResourceNo(), e.getMessage());
            }
        }

        // 避难场所 -[:位于]-> 地点
        if (shelter.getLocationName() != null && !shelter.getLocationName().isBlank()) {
            try {
                Map<String, Object> locProps = new LinkedHashMap<>();
                locProps.put("name", shelter.getLocationName());
                neo4jService.createNode("地点", locProps);
                neo4jService.createRelationship(
                    "避难场所", shelter.getResourceNo(),
                    "地点", shelter.getLocationName(),
                    "位于", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 避难场所地点同步失败: resourceNo={}, err={}", shelter.getResourceNo(), e.getMessage());
            }
        }

        // 避难场所 -[:最大容纳人数]-> 数值
        if (shelter.getCapacity() != null) {
            try {
                Map<String, Object> capProps = new LinkedHashMap<>();
                capProps.put("value", shelter.getCapacity());
                neo4jService.createNode("数值", capProps);
                neo4jService.createRelationship(
                    "避难场所", shelter.getResourceNo(),
                    "数值", shelter.getCapacity(),
                    "最大容纳人数", Map.of()
                );
            } catch (Exception e) {
                log.warn("[sync] 避难场所容量同步失败: resourceNo={}, err={}", shelter.getResourceNo(), e.getMessage());
            }
        }
    }
}
