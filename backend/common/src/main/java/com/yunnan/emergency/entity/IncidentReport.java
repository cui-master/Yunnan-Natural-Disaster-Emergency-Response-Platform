package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("incident_reports")
public class IncidentReport {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long incidentId;
    private Long reporterId;
    private String reporterName;
    private String contact;
    private String content;
    private String images;
    private String locationText;
    private BigDecimal lat;
    private BigDecimal lng;
    private String status;
    private LocalDateTime createdAt;
}
