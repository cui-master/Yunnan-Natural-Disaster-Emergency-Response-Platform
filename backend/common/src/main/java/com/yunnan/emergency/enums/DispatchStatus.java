package com.yunnan.emergency.enums;

public enum DispatchStatus {
    LOCKED("已锁定"),
    DISPATCHED("已调度"),
    RELEASED("已释放"),
    CONFLICT("冲突");

    private final String desc;

    DispatchStatus(String desc) {
        this.desc = desc;
    }

    public String getDesc() {
        return desc;
    }
}
