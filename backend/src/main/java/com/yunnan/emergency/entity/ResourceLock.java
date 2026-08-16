package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;

/**
 * 资源锁定记录
 *
 * 用于资源调度时的预占与冲突检测。
 * 锁定后资源的 available_qty 相应扣减；释放后回补。
 */
@TableName("resource_locks")
public class ResourceLock {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 锁定编号 */
    private String lockNo;

    /** 资源ID */
    private Long resourceId;

    /** 资源名称（冗余） */
    private String resourceName;

    /** 关联灾情ID */
    private Long incidentId;

    /** 关联调度指令ID */
    private Long dispatchOrderId;

    /** 锁定数量 */
    private Integer lockedQty;

    /** 锁定人ID */
    private Long lockedBy;

    /** 锁定人姓名 */
    private String lockedByName;

    /** 状态: locked-锁定中 / released-已释放 / expired-已过期 */
    private String status;

    /** 锁定原因 */
    private String reason;

    /** 过期时间（自动释放） */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime expiresAt;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime lockedAt;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime releasedAt;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updatedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getLockNo() { return lockNo; }
    public void setLockNo(String lockNo) { this.lockNo = lockNo; }
    public Long getResourceId() { return resourceId; }
    public void setResourceId(Long resourceId) { this.resourceId = resourceId; }
    public String getResourceName() { return resourceName; }
    public void setResourceName(String resourceName) { this.resourceName = resourceName; }
    public Long getIncidentId() { return incidentId; }
    public void setIncidentId(Long incidentId) { this.incidentId = incidentId; }
    public Long getDispatchOrderId() { return dispatchOrderId; }
    public void setDispatchOrderId(Long dispatchOrderId) { this.dispatchOrderId = dispatchOrderId; }
    public Integer getLockedQty() { return lockedQty; }
    public void setLockedQty(Integer lockedQty) { this.lockedQty = lockedQty; }
    public Long getLockedBy() { return lockedBy; }
    public void setLockedBy(Long lockedBy) { this.lockedBy = lockedBy; }
    public String getLockedByName() { return lockedByName; }
    public void setLockedByName(String lockedByName) { this.lockedByName = lockedByName; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public String getReason() { return reason; }
    public void setReason(String reason) { this.reason = reason; }
    public LocalDateTime getExpiresAt() { return expiresAt; }
    public void setExpiresAt(LocalDateTime expiresAt) { this.expiresAt = expiresAt; }
    public LocalDateTime getLockedAt() { return lockedAt; }
    public void setLockedAt(LocalDateTime lockedAt) { this.lockedAt = lockedAt; }
    public LocalDateTime getReleasedAt() { return releasedAt; }
    public void setReleasedAt(LocalDateTime releasedAt) { this.releasedAt = releasedAt; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
