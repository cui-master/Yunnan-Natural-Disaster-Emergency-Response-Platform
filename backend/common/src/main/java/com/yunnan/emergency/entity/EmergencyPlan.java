package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("emergency_plans")
public class EmergencyPlan {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long incidentId;
    private String title;
    private String content;
    private String status;
    private Long generatedBy;
    private Long approvedBy;
    private LocalDateTime createdAt;
    private LocalDateTime approvedAt;
}
