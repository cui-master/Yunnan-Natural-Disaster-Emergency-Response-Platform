package com.yunnan.emergency.controller;

import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.baomidou.mybatisplus.extension.plugins.pagination.Page;
import com.yunnan.emergency.annotation.AuditLog;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.DispatchOrder;
import com.yunnan.emergency.entity.ResourceLock;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.DispatchOrderMapper;
import com.yunnan.emergency.service.ResourceLockService;
import com.yunnan.emergency.service.SqlNeo4jSyncService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.time.LocalDateTime;
import java.util.List;

@Tag(name = "调度指令管理", description = "资源调度指令的增删改查")
@RestController
@RequestMapping("/dispatch-orders")
public class DispatchOrderController {
    public DispatchOrderController(DispatchOrderMapper dispatchOrderMapper, ResourceLockService resourceLockService, SqlNeo4jSyncService sqlNeo4jSyncService) {
        this.dispatchOrderMapper = dispatchOrderMapper;
        this.resourceLockService = resourceLockService;
        this.sqlNeo4jSyncService = sqlNeo4jSyncService;
    }


    private final DispatchOrderMapper dispatchOrderMapper;
    private final ResourceLockService resourceLockService;
    private final SqlNeo4jSyncService sqlNeo4jSyncService;

    @Operation(summary = "分页查询调度指令")
    @GetMapping("/page")
    public Result<Page<DispatchOrder>> page(
            @RequestParam(defaultValue = "1") Integer pageNum,
            @RequestParam(defaultValue = "10") Integer pageSize,
            @RequestParam(required = false) String status,
            @RequestParam(required = false) String priority,
            @RequestParam(required = false) Long incidentId) {

        LambdaQueryWrapper<DispatchOrder> wrapper = new LambdaQueryWrapper<>();
        if (status != null && !status.isEmpty()) {
            wrapper.eq(DispatchOrder::getStatus, status);
        }
        if (priority != null && !priority.isEmpty()) {
            wrapper.eq(DispatchOrder::getPriority, priority);
        }
        if (incidentId != null) {
            wrapper.eq(DispatchOrder::getIncidentId, incidentId);
        }
        wrapper.orderByDesc(DispatchOrder::getCreatedAt);

        Page<DispatchOrder> page = dispatchOrderMapper.selectPage(new Page<>(pageNum, pageSize), wrapper);
        return Result.success(page);
    }

    @Operation(summary = "获取调度指令详情")
    @GetMapping("/{id}")
    public Result<DispatchOrder> getById(@PathVariable Long id) {
        DispatchOrder order = dispatchOrderMapper.selectById(id);
        return Result.success(order);
    }

    @Operation(summary = "创建调度指令（自动锁定资源）")
    @PostMapping
    @AuditLog(module = "dispatch", action = "create", description = "创建调度指令")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<DispatchOrder> create(@RequestBody DispatchOrder order,
                                         @AuthenticationPrincipal User user) {
        if (order.getOrderNo() == null || order.getOrderNo().isEmpty()) {
            order.setOrderNo("DO-" + System.currentTimeMillis());
        }
        if (user != null) {
            order.setCommanderId(user.getId());
            order.setCommanderName(user.getRealName() != null ? user.getRealName() : user.getUsername());
        }
        if (order.getStatus() == null || order.getStatus().isEmpty()) {
            order.setStatus("pending");
        }
        if (order.getPriority() == null || order.getPriority().isEmpty()) {
            order.setPriority("normal");
        }
        dispatchOrderMapper.insert(order);

        // 创建调度指令时自动锁定资源（冲突检测 + 扣减可用量）
        if (order.getResourceId() != null && order.getDispatchQty() != null && order.getDispatchQty() > 0) {
            Result<ResourceLock> lockResult = resourceLockService.lock(
                order.getResourceId(), order.getIncidentId(), order.getId(),
                order.getDispatchQty(), user, "调度指令 " + order.getOrderNo(), 120);
            if (lockResult.getCode() != 200) {
                // 资源锁定失败，回滚调度指令
                dispatchOrderMapper.deleteById(order.getId());
                return Result.error("资源锁定失败: " + lockResult.getMessage());
            }
        }
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncDispatchOrderCreate(order); } catch (Exception ignored) {}
        return Result.success(order);
    }

    @Operation(summary = "更新调度指令")
    @PutMapping("/{id}")
    @AuditLog(module = "dispatch", action = "update", description = "更新调度指令")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<DispatchOrder> update(@PathVariable Long id, @RequestBody DispatchOrder order) {
        order.setId(id);
        dispatchOrderMapper.updateById(order);
        DispatchOrder updated = dispatchOrderMapper.selectById(id);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncDispatchOrderUpdate(updated); } catch (Exception ignored) {}
        return Result.success(updated);
    }

    @Operation(summary = "更新调度状态（完成时释放资源锁）")
    @PutMapping("/{id}/status")
    @AuditLog(module = "dispatch", action = "update_status", description = "更新调度状态")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<Void> updateStatus(@PathVariable Long id, @RequestParam String status,
                                      @AuthenticationPrincipal User user) {
        DispatchOrder order = dispatchOrderMapper.selectById(id);
        if (order == null) {
            return Result.error("调度指令不存在");
        }
        order.setStatus(status);
        if ("executing".equals(status) && order.getStartTime() == null) {
            order.setStartTime(LocalDateTime.now());
        }
        if ("completed".equals(status) || "cancelled".equals(status)) {
            if (order.getEndTime() == null) {
                order.setEndTime(LocalDateTime.now());
            }
            // 完成/取消时释放关联的资源锁
            if (order.getIncidentId() != null) {
                resourceLockService.releaseByIncident(order.getIncidentId(), user);
            }
        }
        dispatchOrderMapper.updateById(order);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncDispatchOrderUpdate(order); } catch (Exception ignored) {}
        return Result.success();
    }

    @Operation(summary = "删除调度指令")
    @DeleteMapping("/{id}")
    @AuditLog(module = "dispatch", action = "delete", description = "删除调度指令")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<Void> delete(@PathVariable Long id, @AuthenticationPrincipal User user) {
        DispatchOrder order = dispatchOrderMapper.selectById(id);
        if (order != null && order.getIncidentId() != null) {
            resourceLockService.releaseByIncident(order.getIncidentId(), user);
        }
        dispatchOrderMapper.deleteById(id);
        // 同步到 Neo4j
        try { sqlNeo4jSyncService.syncDispatchOrderDelete(id); } catch (Exception ignored) {}
        return Result.success();
    }

    @Operation(summary = "获取调度看板统计")
    @GetMapping("/dashboard/stats")
    public Result<java.util.Map<String, Object>> getDashboardStats() {
        java.util.Map<String, Object> stats = new java.util.HashMap<>();

        Long total = dispatchOrderMapper.selectCount(null);
        Long pending = dispatchOrderMapper.selectCount(
            new LambdaQueryWrapper<DispatchOrder>().eq(DispatchOrder::getStatus, "pending")
        );
        Long executing = dispatchOrderMapper.selectCount(
            new LambdaQueryWrapper<DispatchOrder>().eq(DispatchOrder::getStatus, "executing")
        );
        Long completed = dispatchOrderMapper.selectCount(
            new LambdaQueryWrapper<DispatchOrder>().eq(DispatchOrder::getStatus, "completed")
        );

        stats.put("total", total);
        stats.put("pending", pending);
        stats.put("executing", executing);
        stats.put("completed", completed);

        return Result.success(stats);
    }
}
