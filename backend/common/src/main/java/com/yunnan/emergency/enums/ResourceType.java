package com.yunnan.emergency.enums;

public enum ResourceType {
    PERSONNEL("人员"),
    VEHICLE("车辆"),
    MATERIAL("物资"),
    SHELTER("避难所");

    private final String desc;

    ResourceType(String desc) {
        this.desc = desc;
    }

    public String getDesc() {
        return desc;
    }
}
