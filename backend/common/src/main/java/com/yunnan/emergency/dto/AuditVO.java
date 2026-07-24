package com.yunnan.emergency.dto;

import lombok.Data;

import java.time.LocalDateTime;

@Data
public class AuditVO {
    private Long id;
    private String operator;
    private String role;
    private String module;
    private String action;
    private String target;
    private String ip;
    private String result;
    private String detail;
    private LocalDateTime createdAt;
}
