package com.yunnan.emergency.service;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import com.baomidou.mybatisplus.core.conditions.query.LambdaQueryWrapper;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.Resource;
import com.yunnan.emergency.entity.ResourceLock;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.mapper.ResourceLockMapper;
import com.yunnan.emergency.mapper.ResourceMapper;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;

import java.time.LocalDateTime;
import java.util.HashMap;
import java.util.List;
import java.util.Map;

/**
 * 资源锁定/调度/释放与冲突检测服务
 *
 * 核心机制：
 *   - 锁定（lock）：扣减资源 available_qty，写入 resource_locks 记录
 *   - 释放（release）：回补 available_qty，标记锁记录为 released
 *   - 冲突检测（checkConflict）：校验可用量是否满足需求
 *   - 过期清理（cleanupExpired）：释放超时未确认的锁
 *
 * 并发控制：使用 @Transactional + 资源行锁（selectById 后 update）保证扣减原子性。
 * 高并发场景可升级为 SELECT ... FOR UPDATE 或 Redis 分布式锁。
 */
@Service
public class ResourceLockService {
    public ResourceLockService(ResourceLockMapper resourceLockMapper, ResourceMapper resourceMapper, EventPushService eventPushService) {
        this.resourceLockMapper = resourceLockMapper;
        this.resourceMapper = resourceMapper;
        this.eventPushService = eventPushService;
    }


    private static final Logger log = LoggerFactory.getLogger(ResourceLockService.class);

    private final ResourceLockMapper resourceLockMapper;
    private final ResourceMapper resourceMapper;
    private final EventPushService eventPushService;

    /**
     * 冲突检测：校验资源可用量是否满足需求
     *
     * @return Result.success 通过；Result.error 冲突详情
     */
    public Result<Map<String, Object>> checkConflict(Long resourceId, Integer requiredQty) {
        Resource resource = resourceMapper.selectById(resourceId);
        if (resource == null) {
            return Result.error("资源不存在");
        }
        if (resource.getStatus() == null || resource.getStatus() != 1) {
            return Result.error("资源当前不可用（状态: " + resource.getStatus() + "）");
        }
        int available = resource.getAvailableQty() != null ? resource.getAvailableQty() : 0;
        Map<String, Object> data = new HashMap<>();
        data.put("resourceId", resourceId);
        data.put("resourceName", resource.getName());
        data.put("requiredQty", requiredQty);
        data.put("availableQty", available);
        data.put("capacity", resource.getCapacity());
        if (available < requiredQty) {
            data.put("conflict", true);
            data.put("shortage", requiredQty - available);
            return Result.error(String.format(
                "资源[%s]可用量不足: 需求 %d, 可用 %d, 缺口 %d",
                resource.getName(), requiredQty, available, requiredQty - available));
        }
        data.put("conflict", false);
        return Result.success("冲突检测通过", data);
    }

    /**
     * 锁定资源
     *
     * @param resourceId      资源ID
     * @param incidentId      关联灾情ID（可为空）
     * @param dispatchOrderId 关联调度指令ID（可为空）
     * @param lockedQty       锁定数量
     * @param operator        操作人
     * @param reason          锁定原因
     * @param expireMinutes   锁定时长（分钟），超时自动释放
     */
    @Transactional(rollbackFor = Exception.class)
    public Result<ResourceLock> lock(Long resourceId, Long incidentId, Long dispatchOrderId,
                                     Integer lockedQty, User operator, String reason, Integer expireMinutes) {
        if (lockedQty == null || lockedQty <= 0) {
            return Result.error("锁定数量必须大于0");
        }

        // 冲突检测
        Result<Map<String, Object>> conflict = checkConflict(resourceId, lockedQty);
        if (conflict.getCode() != 200) {
            return Result.error(conflict.getMessage());
        }

        Resource resource = resourceMapper.selectById(resourceId);

        // 扣减可用量
        int newAvailable = (resource.getAvailableQty() != null ? resource.getAvailableQty() : 0) - lockedQty;
        resource.setAvailableQty(newAvailable);
        resource.setUpdatedAt(LocalDateTime.now());
        resourceMapper.updateById(resource);

        // 写入锁记录
        ResourceLock lock = new ResourceLock();
        lock.setLockNo("LK-" + System.currentTimeMillis());
        lock.setResourceId(resourceId);
        lock.setResourceName(resource.getName());
        lock.setIncidentId(incidentId);
        lock.setDispatchOrderId(dispatchOrderId);
        lock.setLockedQty(lockedQty);
        if (operator != null) {
            lock.setLockedBy(operator.getId());
            lock.setLockedByName(operator.getRealName() != null ? operator.getRealName() : operator.getUsername());
        }
        lock.setStatus("locked");
        lock.setReason(reason);
        LocalDateTime now = LocalDateTime.now();
        lock.setLockedAt(now);
        lock.setCreatedAt(now);
        lock.setUpdatedAt(now);
        if (expireMinutes != null && expireMinutes > 0) {
            lock.setExpiresAt(now.plusMinutes(expireMinutes));
        }
        resourceLockMapper.insert(lock);

        // WebSocket 推送资源锁定事件
        Map<String, Object> payload = new HashMap<>();
        payload.put("lockId", lock.getId());
        payload.put("lockNo", lock.getLockNo());
        payload.put("resourceId", resourceId);
        payload.put("resourceName", resource.getName());
        payload.put("lockedQty", lockedQty);
        payload.put("availableQty", newAvailable);
        payload.put("incidentId", incidentId);
        payload.put("operator", operator != null ? operator.getRealName() : "system");
        eventPushService.pushEventStatus("resource_lock_change", payload);

        log.info("[resource-lock] 资源[{}]锁定 {} 件, 锁定号 {}, 可用余量 {}",
            resource.getName(), lockedQty, lock.getLockNo(), newAvailable);
        return Result.success("资源锁定成功", lock);
    }

    /**
     * 释放资源锁
     *
     * @param lockId   锁记录ID
     * @param operator 操作人
     */
    @Transactional(rollbackFor = Exception.class)
    public Result<Void> release(Long lockId, User operator) {
        ResourceLock lock = resourceLockMapper.selectById(lockId);
        if (lock == null) {
            return Result.error("锁定记录不存在");
        }
        if (!"locked".equals(lock.getStatus())) {
            return Result.error("锁定记录状态为 " + lock.getStatus() + "，无法释放");
        }

        // 回补可用量
        Resource resource = resourceMapper.selectById(lock.getResourceId());
        if (resource != null) {
            int newAvailable = (resource.getAvailableQty() != null ? resource.getAvailableQty() : 0) + lock.getLockedQty();
            resource.setAvailableQty(newAvailable);
            resource.setUpdatedAt(LocalDateTime.now());
            resourceMapper.updateById(resource);

            // WebSocket 推送释放事件
            Map<String, Object> payload = new HashMap<>();
            payload.put("lockId", lock.getId());
            payload.put("lockNo", lock.getLockNo());
            payload.put("resourceId", resource.getId());
            payload.put("resourceName", resource.getName());
            payload.put("releasedQty", lock.getLockedQty());
            payload.put("availableQty", newAvailable);
            payload.put("operator", operator != null ? operator.getRealName() : "system");
            eventPushService.pushEventStatus("resource_lock_change", payload);

            log.info("[resource-lock] 资源[{}]释放 {} 件, 锁定号 {}, 可用余量 {}",
                resource.getName(), lock.getLockedQty(), lock.getLockNo(), newAvailable);
        }

        // 更新锁记录
        LocalDateTime now = LocalDateTime.now();
        lock.setStatus("released");
        lock.setReleasedAt(now);
        lock.setUpdatedAt(now);
        resourceLockMapper.updateById(lock);

        return Result.success("资源释放成功", null);
    }

    /**
     * 按灾情释放所有锁定资源
     */
    @Transactional(rollbackFor = Exception.class)
    public Result<Map<String, Object>> releaseByIncident(Long incidentId, User operator) {
        List<ResourceLock> locks = resourceLockMapper.selectList(
            new LambdaQueryWrapper<ResourceLock>()
                .eq(ResourceLock::getIncidentId, incidentId)
                .eq(ResourceLock::getStatus, "locked")
        );
        int released = 0;
        for (ResourceLock lock : locks) {
            try {
                release(lock.getId(), operator);
                released++;
            } catch (Exception e) {
                log.warn("[resource-lock] 释放锁 {} 失败: {}", lock.getLockNo(), e.getMessage());
            }
        }
        Map<String, Object> data = new HashMap<>();
        data.put("incidentId", incidentId);
        data.put("totalLocks", locks.size());
        data.put("released", released);
        return Result.success("批量释放完成", data);
    }

    /**
     * 查询资源的锁定记录
     */
    public Result<List<ResourceLock>> getLocks(Long resourceId, String status) {
        LambdaQueryWrapper<ResourceLock> wrapper = new LambdaQueryWrapper<>();
        if (resourceId != null) {
            wrapper.eq(ResourceLock::getResourceId, resourceId);
        }
        if (status != null && !status.isEmpty()) {
            wrapper.eq(ResourceLock::getStatus, status);
        }
        wrapper.orderByDesc(ResourceLock::getCreatedAt);
        return Result.success(resourceLockMapper.selectList(wrapper));
    }

    /**
     * 清理过期锁（定时任务调用）
     */
    @Transactional(rollbackFor = Exception.class)
    public int cleanupExpired() {
        List<ResourceLock> expired = resourceLockMapper.selectList(
            new LambdaQueryWrapper<ResourceLock>()
                .eq(ResourceLock::getStatus, "locked")
                .isNotNull(ResourceLock::getExpiresAt)
                .lt(ResourceLock::getExpiresAt, LocalDateTime.now())
        );
        for (ResourceLock lock : expired) {
            try {
                release(lock.getId(), null);
                log.info("[resource-lock] 自动释放过期锁: {}", lock.getLockNo());
            } catch (Exception e) {
                log.warn("[resource-lock] 自动释放锁 {} 失败: {}", lock.getLockNo(), e.getMessage());
            }
        }
        return expired.size();
    }
}
