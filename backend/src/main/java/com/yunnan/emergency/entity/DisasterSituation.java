package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;
import lombok.Data;

import java.time.LocalDateTime;

/**
 * 灾情态势聚合表
 * 前端大屏直接从此表读取，由后端在事件变更时刷新
 */
@Data
@TableName("disaster_situation")
public class DisasterSituation {

    @TableId(type = IdType.AUTO)
    private Long id;

    /** 总事件数 */
    private Integer totalCount;
    /** 待核验数 */
    private Integer pendingCount;
    /** 已确认数 */
    private Integer confirmedCount;
    /** 处置中数 */
    private Integer processingCount;
    /** 已结束数 */
    private Integer completedCount;
    /** 高风险未结束数 */
    private Integer highRiskCount;
    /** 受灾总人数 */
    private Integer totalAffected;
    /** 可用资源数 */
    private Integer availableResources;
    /** 救援队伍数 */
    private Integer rescueTeams;
    /** 灾害类型分布 JSON */
    private String typeDistribution;
    /** 各地市灾害数量 JSON */
    private String cityDistribution;
    /** 近7日灾害趋势 JSON */
    private String weeklyTrend;
    /** 实时事件流 JSON */
    private String realtimeEvents;
    /** 最后刷新时间 */
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime refreshedAt;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;
    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updatedAt;
}
