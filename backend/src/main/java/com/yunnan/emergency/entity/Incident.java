package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("incidents")
public class Incident {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String code;
    private String title;
    private String type;
    private String level;
    private String status;
    private Long reportId;
    private Long locationId;
    private String description;
    private Long confirmedBy;
    private LocalDateTime confirmedAt;
    private LocalDateTime closedAt;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
