package com.yunnan.emergency.dto;

import lombok.Data;

import java.math.BigDecimal;

@Data
public class ReportSubmitRequest {
    private String title;
    private String type;
    private String level;
    private String content;
    private String locationText;
    private BigDecimal lat;
    private BigDecimal lng;
    private String images;
    private String contact;
}
