package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.AuditLog;
import com.yunnan.emergency.entity.Incident;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.enums.IncidentStatus;
import com.yunnan.emergency.mapper.AuditLogMapper;
import com.yunnan.emergency.mapper.IncidentMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.Map;

/**
 * 灾情工单状态机服务
 *
 * 负责校验状态流转的合法性，并同步写入审计日志、推送 WebSocket 事件状态。
 * 所有状态变更必须经过本服务，禁止直接 update status。
 */
@Service
public class IncidentStateMachineService {
    public IncidentStateMachineService(IncidentMapper incidentMapper, AuditLogMapper auditLogMapper, EventPushService eventPushService) {
        this.incidentMapper = incidentMapper;
        this.auditLogMapper = auditLogMapper;
        this.eventPushService = eventPushService;
    }


    private static final Logger log = LoggerFactory.getLogger(IncidentStateMachineService.class);

    private final IncidentMapper incidentMapper;
    private final AuditLogMapper auditLogMapper;
    private final EventPushService eventPushService;

    /**
     * 执行状态流转
     *
     * @param incidentId  灾情ID
     * @param targetCode  目标状态编码（中文：待核验/已确认/处置中/已结束）
     * @param operator    操作人
     * @param reason      流转原因/备注
     * @return 流转后的灾情事件
     */
    @Transactional(rollbackFor = Exception.class)
    public Result<Incident> transition(Long incidentId, String targetCode, User operator, String reason) {
        Incident incident = incidentMapper.selectById(incidentId);
        if (incident == null) {
            return Result.error("灾情事件不存在");
        }

        IncidentStatus current = IncidentStatus.fromCode(incident.getStatus());
        IncidentStatus target = IncidentStatus.fromCode(targetCode);
        if (current == null) {
            return Result.error("当前状态非法: " + incident.getStatus());
        }
        if (target == null) {
            return Result.error("目标状态非法: " + targetCode);
        }
        if (current == target) {
            return Result.error("当前状态已是: " + current.getCode());
        }
        if (!current.canTransitionTo(target)) {
            return Result.error(String.format(
                "状态流转非法: %s → %s（允许的下一状态: %s）",
                current.getCode(), target.getCode(), current.allowedNext()
            ));
        }

        // 记录流转前状态
        String previousStatus = incident.getStatus();

        // 更新状态
        incident.setStatus(target.getCode());
        LocalDateTime now = LocalDateTime.now();
        switch (target) {
            case CONFIRMED -> {
                if (incident.getReviewedAt() == null) {
                    incident.setReviewedAt(now);
                }
                if (operator != null) {
                    incident.setReviewerId(operator.getId());
                }
            }
            case COMPLETED -> {
                // 终态：无额外字段
            }
            default -> { /* PROCESSING 无额外字段 */ }
        }
        incident.setUpdatedAt(now);
        incidentMapper.updateById(incident);

        // 写审计日志
        saveAuditLog(incident, operator, previousStatus, target.getCode(), reason);

        // WebSocket 推送事件状态变更
        Map<String, Object> payload = new HashMap<>();
        payload.put("incidentId", incident.getId());
        payload.put("incidentNo", incident.getIncidentNo());
        payload.put("title", incident.getTitle());
        payload.put("previousStatus", previousStatus);
        payload.put("currentStatus", target.getCode());
        payload.put("operator", operator != null ? operator.getRealName() : "system");
        payload.put("reason", reason);
        payload.put("timestamp", now.toString());
        eventPushService.pushEventStatus("incident_status_change", payload);

        log.info("[state-machine] 灾情 {} 状态流转: {} → {}, 操作人: {}, 原因: {}",
            incident.getIncidentNo(), previousStatus, target.getCode(),
            operator != null ? operator.getUsername() : "system", reason);

        return Result.success("状态流转成功", incident);
    }

    /**
     * 获取当前状态可流转的下一状态列表
     */
    public Result<Map<String, Object>> getTransitions(Long incidentId) {
        Incident incident = incidentMapper.selectById(incidentId);
        if (incident == null) {
            return Result.error("灾情事件不存在");
        }
        IncidentStatus current = IncidentStatus.fromCode(incident.getStatus());
        Map<String, Object> data = new HashMap<>();
        data.put("currentStatus", incident.getStatus());
        data.put("currentLabel", current != null ? current.getCode() : incident.getStatus());
        data.put("allowedNext", current != null
            ? current.allowedNext().stream().map(IncidentStatus::getCode).toList()
            : java.util.Collections.emptyList());
        return Result.success(data);
    }

    private void saveAuditLog(Incident incident, User operator, String from, String to, String reason) {
        try {
            AuditLog log = new AuditLog();
            if (operator != null) {
                log.setUserId(operator.getId());
                log.setUsername(operator.getUsername());
                log.setRoleCode(operator.getRoleCode());
            }
            log.setModule("incident");
            log.setAction("state_transition");
            log.setTargetType("incident");
            log.setTargetId(String.valueOf(incident.getId()));
            log.setDescription(String.format("灾情[%s]状态流转 %s → %s，原因: %s",
                incident.getIncidentNo(), from, to, reason));
            log.setResult("success");
            log.setCreatedAt(LocalDateTime.now());
            auditLogMapper.insert(log);
        } catch (Exception e) {
            IncidentStateMachineService.log.warn("写入审计日志失败: {}", e.getMessage());
        }
    }
}
