package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.annotation.AuditLog;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.IncidentReport;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.IncidentMapper;
import com.yunnan.emergency.mapper.IncidentReportMapper;
import com.yunnan.emergency.service.DisasterSituationService;
import com.yunnan.emergency.service.GraphJsonService;
import com.yunnan.emergency.service.InfoService;
import com.yunnan.emergency.service.SqlNeo4jSyncService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.UUID;

@Tag(name = "灾情上报管理", description = "灾情上报、审核等")
@RestController
@RequestMapping("/reports")
public class IncidentReportController {
    public IncidentReportController(IncidentReportMapper reportMapper, IncidentMapper incidentMapper, SqlNeo4jSyncService sqlNeo4jSyncService, DisasterSituationService disasterSituationService, InfoService infoService, GraphJsonService graphJsonService) {
        this.reportMapper = reportMapper;
        this.incidentMapper = incidentMapper;
        this.sqlNeo4jSyncService = sqlNeo4jSyncService;
        this.disasterSituationService = disasterSituationService;
        this.infoService = infoService;
        this.graphJsonService = graphJsonService;
    }


    private final IncidentReportMapper reportMapper;
    private final IncidentMapper incidentMapper;
    private final SqlNeo4jSyncService sqlNeo4jSyncService;
    private final DisasterSituationService disasterSituationService;
    private final InfoService infoService;
    private final GraphJsonService graphJsonService;

    @Operation(summary = "分页查询上报记录")
    @GetMapping("/page")
    public Result<Page<IncidentReport>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String disasterType,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String keyword) {

        LambdaQueryWrapper<IncidentReport> wrapper = new LambdaQueryWrapper<>();
        if (disasterType != null && !disasterType.isEmpty()) {
            wrapper.eq(IncidentReport::getDisasterType, disasterType);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq(IncidentReport::getStatus, status);
        }
        if (keyword != null && !keyword.isEmpty()) {
            wrapper.like(IncidentReport::getTitle, keyword).or().like(IncidentReport::getLocationName, keyword);
        }
        wrapper.orderByDesc(IncidentReport::getCreatedAt);

        Page<IncidentReport> page = reportMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取上报详情")
    @GetMapping("/{id}")
    public Result<IncidentReport> getById(@PathVariable Long id) {
        IncidentReport report = reportMapper.selectById(id);
        return Result.success(report);
    }

    @Operation(summary = "提交灾情上报")
    @PostMapping
    @AuditLog(module = "incident", action = "create", description = "提交灾情上报")
    @PreAuthorize("hasAnyRole('REPORTER','COMMANDER')")
    public Result<IncidentReport> create(@RequestBody IncidentReport report,
                                          @AuthenticationPrincipal User user) {
        if (user != null) {
            report.setReporterId(user.getId());
            report.setReporterName(user.getRealName() != null ? user.getRealName() : user.getUsername());
        }
        report.setStatus("pending");
        // 组装 locationName：州市 + 区/县 + 具体地址
        StringBuilder locName = new StringBuilder();
        if (report.getCity() != null) locName.append(report.getCity());
        if (report.getDistrict() != null) locName.append(report.getDistrict());
        if (report.getAddress() != null) locName.append(report.getAddress());
        if (locName.length() > 0) {
            report.setLocationName(locName.toString());
        }
        reportMapper.insert(report);

        // 提交上报后 info 表待审核数 +1
        try {
            com.yunnan.emergency.entity.Info info = infoService.getOrInit();
            info.setPending((info.getPending() == null ? 0 : info.getPending()) + 1);
            infoService.updateById(info);
        } catch (Exception e) {
            // info 更新失败不影响主流程
        }

        return Result.success(report);
    }

    @Operation(summary = "审核上报记录")
    @PostMapping("/{id}/review")
    @AuditLog(module = "incident", action = "approve", description = "审核灾情上报")
    @PreAuthorize("hasRole('COMMANDER')")
    public Result<Void> review(@PathVariable Long id,
                               @RequestParam String status,
                               @RequestParam(required = false) String comment,
                               @AuthenticationPrincipal User user) {
        IncidentReport report = reportMapper.selectById(id);
        if (report == null) {
            return Result.error("上报记录不存在");
        }
        if (!"pending".equals(report.getStatus())) {
            return Result.error("该记录已审核，无法重复审核");
        }

        report.setStatus(status);
        report.setReviewComment(comment);
        report.setReviewerId(user.getId());
        report.setReviewedAt(LocalDateTime.now());
        reportMapper.updateById(report);

        // 审核通过时，创建正式灾情事件（状态为"已确认"），并从 incident_reports 中删除
        if ("approved".equals(status)) {
            Incident incident = new Incident();
            incident.setIncidentNo("INC-" + System.currentTimeMillis());
            incident.setTitle(report.getTitle());
            incident.setDisasterType(report.getDisasterType());
            incident.setRiskLevel(report.getRiskLevel());
            incident.setLocationName(report.getLocationName());
            incident.setLng(report.getLng());
            incident.setLat(report.getLat());
            incident.setStatus("已确认");
            incident.setSource("manual");
            incident.setReporterId(report.getReporterId());
            incident.setReviewerId(user.getId());
            incident.setReviewedAt(LocalDateTime.now());
            incident.setOccurredAt(report.getOccurredAt());
            incident.setDescription(report.getDescription());
            incident.setAffectedPeople(report.getAffectedPeople());
            // 详细地址信息（city/district/street/roadName）保留在 incident_reports 表中
            // Incident 实体不再包含这些字段，locationName 已包含完整地址字符串
            incidentMapper.insert(incident);

            // 同步到 Neo4j（在删除前同步）
            // 同步受灾点及其二级实体：地点、涉及人员、风险评估、灾害类型、临近道路
            try {
                sqlNeo4jSyncService.syncIncidentCreate(incident, report.getRoadName());
            } catch (Exception e) {
                // Neo4j 同步失败不影响 SQL 主流程
            }

            // 同步到图数据库 JSON 文件（只有审核通过才添加）
            try {
                graphJsonService.addIncidentToGraph(report, incident.getId());
            } catch (Exception e) {
                // 图 JSON 同步失败不影响主流程
            }

            // 刷新 disaster_situation 聚合表
            try {
                disasterSituationService.refresh();
            } catch (Exception e) {
                // 刷新失败不影响主流程
            }

            // 同步更新 info 表（大屏 KPI 数据源）
            try {
                com.yunnan.emergency.entity.Info info = infoService.getOrInit();
                info.setTotalDisasters((info.getTotalDisasters() == null ? 0 : info.getTotalDisasters()) + 1);
                info.setInProgress((info.getInProgress() == null ? 0 : info.getInProgress()) + 1);
                int pending = (info.getPending() == null ? 0 : info.getPending()) - 1;
                info.setPending(Math.max(pending, 0));
                int affected = (info.getAffectedPeople() == null ? 0 : info.getAffectedPeople())
                        + (report.getAffectedPeople() == null ? 0 : report.getAffectedPeople());
                info.setAffectedPeople(affected);
                infoService.updateById(info);
            } catch (Exception e) {
                // info 更新失败不影响主流程
            }

            // 审核通过后删除 incident_reports 中的记录
            reportMapper.deleteById(report.getId());
        } else {
            // 审核拒绝时，只更新状态和备注，保留记录
            report.setStatus(status);
            report.setReviewComment(comment);
            report.setReviewerId(user.getId());
            report.setReviewedAt(LocalDateTime.now());
            reportMapper.updateById(report);
        }

        return Result.success();
    }

    @Operation(summary = "获取我的上报列表")
    @GetMapping("/my")
    public Result<Page<IncidentReport>> getMyReports(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @AuthenticationPrincipal User user) {

        LambdaQueryWrapper<IncidentReport> wrapper = new LambdaQueryWrapper<>();
        if (user != null) {
            wrapper.eq(IncidentReport::getReporterId, user.getId());
        }
        wrapper.orderByDesc(IncidentReport::getCreatedAt);

        Page<IncidentReport> page = reportMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }
}
