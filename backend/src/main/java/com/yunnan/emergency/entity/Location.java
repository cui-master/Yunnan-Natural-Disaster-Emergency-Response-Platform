package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.math.BigDecimal;
import java.time.LocalDateTime;

@Data
@TableName("locations")
public class Location {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String name;
    private String address;
    private String geom;          // WKT，MVP 可选
    private BigDecimal lat;
    private BigDecimal lng;
    private BigDecimal riskRadius;
    private String riskGeom;       // WKT，MVP 可选
    private LocalDateTime createdAt;
}
