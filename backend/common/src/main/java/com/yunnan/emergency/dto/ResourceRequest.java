package com.yunnan.emergency.dto;

import lombok.Data;

@Data
public class ResourceRequest {
    private String name;
    private String type;
    private Integer total;
    private Integer available;
    private String unit;
    private Long locationId;
}
