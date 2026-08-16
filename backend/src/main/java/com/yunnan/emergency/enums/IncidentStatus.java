package com.yunnan.emergency.enums;

import java.util.Arrays;
import java.util.Collections;
import java.util.EnumSet;
import java.util.Set;

/**
 * 灾情工单状态机
 *
 * 状态流转：
 *   待核验(PENDING_VERIFICATION)
 *       ↓ 核验通过
 *   已确认(CONFIRMED)
 *       ↓ 开始处置
 *   处置中(PROCESSING)
 *       ↓ 处置完成
 *   已结束(COMPLETED)  ← 终态
 *
 * 允许的跳转见 {@link #allowedNext}
 */
public enum IncidentStatus {

    PENDING_VERIFICATION("待核验"),
    CONFIRMED("已确认"),
    PROCESSING("处置中"),
    COMPLETED("已结束");

    /** 数据库存储值（中文） */
    private final String code;

    IncidentStatus(String code) {
        this.code = code;
    }

    public String getCode() {
        return code;
    }

    /**
     * 允许的下一状态
     */
    public Set<IncidentStatus> allowedNext() {
        return switch (this) {
            case PENDING_VERIFICATION -> EnumSet.of(CONFIRMED, COMPLETED);
            case CONFIRMED -> EnumSet.of(PROCESSING, COMPLETED);
            case PROCESSING -> EnumSet.of(COMPLETED, CONFIRMED);
            case COMPLETED -> Collections.emptySet();
        };
    }

    /**
     * 是否允许跳转到目标状态
     */
    public boolean canTransitionTo(IncidentStatus target) {
        return allowedNext().contains(target);
    }

    /**
     * 根据中文编码解析枚举
     */
    public static IncidentStatus fromCode(String code) {
        if (code == null) {
            return null;
        }
        return Arrays.stream(values())
            .filter(s -> s.code.equals(code) || s.name().equalsIgnoreCase(code))
            .findFirst()
            .orElse(null);
    }

    /**
     * 判断给定字符串是否为合法状态
     */
    public static boolean isValid(String code) {
        return fromCode(code) != null;
    }
}
