package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("dispatch_orders")
public class DispatchOrder {
    @TableId(type = IdType.AUTO)
    private Long id;
    private Long incidentId;
    private Long planId;
    private Long resourceId;
    private Integer quantity;
    private String status;
    private Long operatorId;
    private LocalDateTime createdAt;
    private LocalDateTime executedAt;
    private LocalDateTime releasedAt;
}
