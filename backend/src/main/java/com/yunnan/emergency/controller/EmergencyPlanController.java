package com.yunnan.emergency.controller;

import cn.hutool.http.HttpRequest;
import cn.hutool.http.HttpResponse;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.fasterxml.jackson.databind.ObjectMapper;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.EmergencyPlan;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.EmergencyPlanMapper;
import com.yunnan.emergency.mapper.ResourceMapper;
import com.yunnan.emergency.service.InfoService;
import com.yunnan.emergency.service.Neo4jService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import lombok.extern.slf4j.Slf4j;
import org.springframework.beans.factory.annotation.Value;
import org.springframework.http.ResponseEntity;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.LinkedHashMap;
import java.util.List;
import java.util.Map;

@Slf4j
@Tag(name = "应急方案管理", description = "应急方案的生成、查询、修改等")
@RestController
@RequestMapping("/plans")
@RequiredArgsConstructor
public class EmergencyPlanController {

    private final EmergencyPlanMapper planMapper;
    private final Neo4jService neo4jService;
    private final ResourceMapper resourceMapper;
    private final ObjectMapper objectMapper;
    private final InfoService infoService;

    @Value("${ai-service.base-url:http://localhost:8050}")
    private String aiServiceBaseUrl;

    @Operation(summary = "查询Neo4j受灾点列表（供前端选择区域）")
    @GetMapping("/incidents")
    public Result<List<Map<String, Object>>> listIncidents() {
        try {
            String url = aiServiceBaseUrl + "/api/v1/commander/incidents";
            HttpResponse response = HttpRequest.get(url).timeout(10000).execute();
            String body = response.body();
            Map<String, Object> aiResult = objectMapper.readValue(body, Map.class);
            List<Map<String, Object>> list = (List<Map<String, Object>>) aiResult.getOrDefault("data", java.util.Collections.emptyList());
            return Result.success(list);
        } catch (Exception e) {
            log.error("[listIncidents] 查询受灾点列表失败", e);
            return Result.error("查询受灾点列表失败: " + e.getMessage());
        }
    }

    @Operation(summary = "AI生成应急处置方案（调用Dify工作流）")
    @PostMapping("/generate")
    public Result<Map<String, Object>> generate(@RequestBody Map<String, Object> params) {
        try {
            String url = aiServiceBaseUrl + "/api/v1/commander/dispatch-plan";
            // 前端传驼峰key，转为ai-service期望的蛇形key
            Map<String, Object> snakeParams = new LinkedHashMap<>();
            for (Map.Entry<String, Object> entry : params.entrySet()) {
                String camelKey = entry.getKey();
                String snakeKey = switch (camelKey) {
                    case "incidentId" -> "incident_id";
                    case "incidentIds" -> "incident_ids";
                    case "areaName" -> "area_name";
                    case "disasterType" -> "disaster_type";
                    case "riskLevel" -> "risk_level";
                    case "affectedPeople" -> "affected_people";
                    case "riskInfo" -> "input_risk_info";
                    case "visionText" -> "vision_text";
                    default -> camelKey;
                };
                snakeParams.put(snakeKey, entry.getValue());
            }
            String jsonBody = objectMapper.writeValueAsString(snakeParams);
            log.info("[generate] 调用AI服务生成方案: areaName={}, body={}", params.get("areaName"), jsonBody);
            HttpResponse response = HttpRequest.post(url)
                .header("Content-Type", "application/json")
                .body(jsonBody)
                .timeout(200000)
                .execute();
            String body = response.body();
            log.info("[generate] AI服务响应: status={}, body={}", response.getStatus(), body.length() > 500 ? body.substring(0, 500) + "..." : body);
            Map<String, Object> aiResult = objectMapper.readValue(body, Map.class);
            return Result.success(aiResult);
        } catch (Exception e) {
            log.error("[generate] AI生成方案失败", e);
            return Result.error("AI生成方案失败: " + e.getMessage());
        }
    }

    @Operation(summary = "分页查询应急方案")
    @GetMapping("/page")
    public Result<Page<EmergencyPlan>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String disasterType,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) Long incidentId,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<EmergencyPlan> wrapper = new LambdaQueryWrapper<>();
        if (disasterType != null && !disasterType.isEmpty()) {
            wrapper.eq(EmergencyPlan::getDisasterType, disasterType);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq(EmergencyPlan::getStatus, status);
        }
        if (incidentId != null) {
            wrapper.eq(EmergencyPlan::getIncidentId, incidentId);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(EmergencyPlan::getTitle, keyword).or().like(EmergencyPlan::getPlanNo, keyword);
        }
        wrapper.orderByDesc(EmergencyPlan::getCreatedAt);

        Page<EmergencyPlan> page = planMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取方案详情")
    @GetMapping("/{id}")
    public Result<EmergencyPlan> getById(@PathVariable Long id) {
        EmergencyPlan plan = planMapper.selectById(id);
        return Result.success(plan);
    }

    @Operation(summary = "创建应急方案（手动）")
    @PostMapping
    public Result<EmergencyPlan> create(@RequestBody EmergencyPlan plan,
                                         @AuthenticationPrincipal User user) {
        if (plan.getPlanNo() == null || plan.getPlanNo().isEmpty()) {
            plan.setPlanNo("EP-" + System.currentTimeMillis());
        }
        if (plan.getSource() == null || plan.getSource().isEmpty()) {
            plan.setSource("manual");
        }
        if (plan.getStatus() == null || plan.getStatus().isEmpty()) {
            plan.setStatus("draft");
        }
        if (plan.getVersion() == null) {
            plan.setVersion(1);
        }
        if (user != null) {
            plan.setGeneratedBy(user.getId());
        }
        planMapper.insert(plan);
        return Result.success(plan);
    }

    @Operation(summary = "更新应急方案")
    @PutMapping("/{id}")
    public Result<EmergencyPlan> update(@PathVariable Long id, @RequestBody EmergencyPlan plan) {
        plan.setId(id);
        planMapper.updateById(plan);
        return Result.success(planMapper.selectById(id));
    }

    @Operation(summary = "删除应急方案")
    @DeleteMapping("/{id}")
    public Result<Void> delete(@PathVariable Long id) {
        planMapper.deleteById(id);
        return Result.success();
    }

    @Operation(summary = "提交应急方案并同步更新Neo4j资源状态")
    @PostMapping("/{id}/submit")
    public Result<Map<String, Object>> submit(@PathVariable Long id) {
        EmergencyPlan plan = planMapper.selectById(id);
        if (plan == null) {
            return Result.error("方案不存在");
        }
        plan.setStatus("submitted");
        plan.setApprovedAt(LocalDateTime.now());
        planMapper.updateById(plan);

        int updatedWarehouses = 0;
        int updatedTeams = 0;
        int updatedShelters = 0;

        // 更新物资仓库库存
        if (plan.getMaterials() != null) {
            for (Map<String, Object> material : plan.getMaterials()) {
                try {
                    String resourceNo = (String) material.get("resourceNo");
                    Object allocatedQtyObj = material.get("allocatedQty");
                    if (resourceNo != null && allocatedQtyObj != null) {
                        int allocatedQty = ((Number) allocatedQtyObj).intValue();
                        neo4jService.updateMaterialStock(resourceNo, allocatedQty);
                        // 同步更新MySQL
                        Resource wh = resourceMapper.selectOne(
                            new LambdaQueryWrapper<Resource>().eq(Resource::getResourceNo, resourceNo)
                        );
                        if (wh != null && wh.getAvailableQty() != null) {
                            wh.setAvailableQty(Math.max(0, wh.getAvailableQty() - allocatedQty));
                            resourceMapper.updateById(wh);
                        }
                        updatedWarehouses++;
                    }
                } catch (Exception e) {
                    log.warn("[submit] 更新物资仓库失败: material={}, err={}", material, e.getMessage());
                }
            }
        }

        // 更新救援队伍状态为忙碌
        if (plan.getTeams() != null) {
            for (Map<String, Object> team : plan.getTeams()) {
                try {
                    String resourceNo = (String) team.get("resourceNo");
                    if (resourceNo != null) {
                        neo4jService.updateTeamStatus(resourceNo, true);
                        // 同步更新MySQL
                        Resource t = resourceMapper.selectOne(
                            new LambdaQueryWrapper<Resource>().eq(Resource::getResourceNo, resourceNo)
                        );
                        if (t != null) {
                            t.setStatus(1);
                            resourceMapper.updateById(t);
                        }
                        updatedTeams++;
                    }
                } catch (Exception e) {
                    log.warn("[submit] 更新救援队伍失败: team={}, err={}", team, e.getMessage());
                }
            }
        }

        // 更新避难场所剩余容纳人数
        if (plan.getShelters() != null) {
            for (Map<String, Object> shelter : plan.getShelters()) {
                try {
                    String resourceNo = (String) shelter.get("resourceNo");
                    Object evacueesObj = shelter.get("evacuees");
                    if (resourceNo != null && evacueesObj != null) {
                        int evacuees = ((Number) evacueesObj).intValue();
                        neo4jService.updateShelterCapacity(resourceNo, evacuees);
                        // 同步更新MySQL
                        Resource s = resourceMapper.selectOne(
                            new LambdaQueryWrapper<Resource>().eq(Resource::getResourceNo, resourceNo)
                        );
                        if (s != null && s.getAvailableQty() != null) {
                            s.setAvailableQty(Math.max(0, s.getAvailableQty() - evacuees));
                            resourceMapper.updateById(s);
                        }
                        updatedShelters++;
                    }
                } catch (Exception e) {
                    log.warn("[submit] 更新避难场所失败: shelter={}, err={}", shelter, e.getMessage());
                }
            }
        }

        Map<String, Object> result = Map.of(
            "planId", id,
            "updatedWarehouses", updatedWarehouses,
            "updatedTeams", updatedTeams,
            "updatedShelters", updatedShelters
        );
        log.info("[submit] 方案提交成功并同步Neo4j: {}", result);

        // 提交处置方案时，info 表可用资源随机减少 500-1200
        try {
            int decrease = 500 + (int)(Math.random() * 701);
            com.yunnan.emergency.entity.Info info = infoService.getOrInit();
            int current = info.getAvailableResources() == null ? 0 : info.getAvailableResources();
            info.setAvailableResources(Math.max(0, current - decrease));
            infoService.updateById(info);
            log.info("[submit] 提交处置方案，可用资源减少 {}，当前值 {}", decrease, info.getAvailableResources());
        } catch (Exception e) {
            log.warn("[submit] 更新 info 表可用资源失败", e);
        }

        return Result.success(result);
    }

    @Operation(summary = "审批方案")
    @PostMapping("/{id}/approve")
    public Result<Void> approve(@PathVariable Long id,
                                 @RequestParam String status,
                                 @AuthenticationPrincipal User user) {
        EmergencyPlan plan = planMapper.selectById(id);
        if (plan == null) {
            return Result.error("方案不存在");
        }
        plan.setStatus(status);
        if ("approved".equals(status)) {
            plan.setApprovedBy(user.getId());
            plan.setApprovedAt(LocalDateTime.now());
        }
        planMapper.updateById(plan);
        return Result.success();
    }

    @Operation(summary = "获取方案列表（用于下拉选择）")
    @GetMapping("/list")
    public Result<List<EmergencyPlan>> list(
            @RequestParam(required = false) String status) {
        LambdaQueryWrapper<EmergencyPlan> wrapper = new LambdaQueryWrapper<>();
        if (status != null && !status.isEmpty()) {
            wrapper.eq(EmergencyPlan::getStatus, status);
        }
        wrapper.orderByDesc(EmergencyPlan::getCreatedAt).last("LIMIT 50");
        return Result.success(planMapper.selectList(wrapper));
    }
}
