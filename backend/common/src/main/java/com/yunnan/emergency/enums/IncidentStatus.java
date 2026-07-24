package com.yunnan.emergency.enums;

public enum IncidentStatus {
    PENDING_VERIFY("待核验"),
    CONFIRMED("已确认"),
    IN_PROGRESS("处置中"),
    CLOSED("已结束"),
    REJECTED("已驳回");

    private final String desc;

    IncidentStatus(String desc) {
        this.desc = desc;
    }

    public String getDesc() {
        return desc;
    }
}
