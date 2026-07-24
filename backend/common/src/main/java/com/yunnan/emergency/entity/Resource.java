package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("resources")
public class Resource {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String type;
    private Integer total;
    private Integer available;
    private String unit;
    private Long locationId;
    private String status;
    private Long lockedBy;
    private LocalDateTime lockedAt;
    private LocalDateTime createdAt;
}
