package com.yunnan.emergency.dto;

import lombok.Data;

@Data
public class SystemConfigVO {
    private Long id;
    private String key;
    private String value;
    private String group;
    private String remark;
}
