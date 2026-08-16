package com.yunnan.emergency.controller;

import com.yunnan.emergency.annotation.AuditLog;
import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.ResourceLock;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.service.ResourceLockService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import org.springframework.security.access.prepost.PreAuthorize;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

import java.util.List;
import java.util.Map;

/**
 * 资源锁定管理控制器
 *
 * 提供资源锁定、释放、冲突检测接口。
 * 权限：指挥员、资源管理员可操作；其他角色只读。
 */
@Tag(name = "资源锁定", description = "资源锁定、释放、冲突检测")
@RestController
@RequestMapping("/resource-locks")
public class ResourceLockController {
    public ResourceLockController(ResourceLockService resourceLockService) {
        this.resourceLockService = resourceLockService;
    }


    private final ResourceLockService resourceLockService;

    @Operation(summary = "冲突检测（校验资源可用量）")
    @GetMapping("/conflict-check")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<Map<String, Object>> checkConflict(@RequestParam Long resourceId,
                                                      @RequestParam Integer requiredQty) {
        return resourceLockService.checkConflict(resourceId, requiredQty);
    }

    @Operation(summary = "锁定资源")
    @PostMapping
    @AuditLog(module = "resource", action = "lock", description = "锁定资源")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<ResourceLock> lock(@RequestBody Map<String, Object> body,
                                      @AuthenticationPrincipal User user) {
        Long resourceId = ((Number) body.get("resourceId")).longValue();
        Long incidentId = body.get("incidentId") != null ? ((Number) body.get("incidentId")).longValue() : null;
        Long dispatchOrderId = body.get("dispatchOrderId") != null ? ((Number) body.get("dispatchOrderId")).longValue() : null;
        Integer lockedQty = ((Number) body.get("lockedQty")).intValue();
        String reason = (String) body.getOrDefault("reason", "");
        Integer expireMinutes = body.get("expireMinutes") != null ? ((Number) body.get("expireMinutes")).intValue() : 60;

        return resourceLockService.lock(resourceId, incidentId, dispatchOrderId,
            lockedQty, user, reason, expireMinutes);
    }

    @Operation(summary = "释放资源锁")
    @DeleteMapping("/{lockId}")
    @AuditLog(module = "resource", action = "release", description = "释放资源锁")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<Void> release(@PathVariable Long lockId,
                                 @AuthenticationPrincipal User user) {
        return resourceLockService.release(lockId, user);
    }

    @Operation(summary = "按灾情释放所有锁定资源")
    @DeleteMapping("/by-incident/{incidentId}")
    @AuditLog(module = "resource", action = "release", description = "按灾情批量释放资源锁")
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER')")
    public Result<Map<String, Object>> releaseByIncident(@PathVariable Long incidentId,
                                                          @AuthenticationPrincipal User user) {
        return resourceLockService.releaseByIncident(incidentId, user);
    }

    @Operation(summary = "查询锁定记录")
    @GetMapping
    @PreAuthorize("hasAnyRole('COMMANDER','RESMANAGER','ADMIN')")
    public Result<List<ResourceLock>> list(@RequestParam(required = false) Long resourceId,
                                            @RequestParam(required = false) String status) {
        return resourceLockService.getLocks(resourceId, status);
    }

    @Operation(summary = "清理过期锁（手动）")
    @PostMapping("/cleanup-expired")
    @PreAuthorize("hasAnyRole('ADMIN','RESMANAGER')")
    public Result<Map<String, Object>> cleanupExpired() {
        int count = resourceLockService.cleanupExpired();
        return Result.success(Map.of("cleaned", count));
    }
}
