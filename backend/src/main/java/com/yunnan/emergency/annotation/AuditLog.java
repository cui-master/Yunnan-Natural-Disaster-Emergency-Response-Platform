package com.yunnan.emergency.annotation;

import java.lang.annotation.ElementType;
import java.lang.annotation.Retention;
import java.lang.annotation.RetentionPolicy;
import java.lang.annotation.Target;

/**
 * 操作审计注解
 *
 * 标注在 Controller 方法上，由 {@link com.yunnan.emergency.aspect.AuditAspect}
 * 自动记录操作日志到 audit_logs 表。
 *
 * 用法：
 *   @AuditLog(module = "resource", action = "create", description = "新增资源")
 *   @PostMapping
 *   public Result<Resource> create(...) { ... }
 */
@Target(ElementType.METHOD)
@Retention(RetentionPolicy.RUNTIME)
public @interface AuditLog {

    /** 模块: auth/incident/resource/plan/system/dispatch */
    String module() default "";

    /** 操作: login/logout/create/update/delete/approve/reject/lock/release */
    String action() default "";

    /** 操作描述 */
    String description() default "";

    /** 操作对象类型（默认自动推断） */
    String targetType() default "";
}
