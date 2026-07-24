package com.yunnan.emergency.enums;

public enum PlanStatus {
    DRAFT("草稿"),
    APPROVED("已审批");

    private final String desc;

    PlanStatus(String desc) {
        this.desc = desc;
    }

    public String getDesc() {
        return desc;
    }
}
