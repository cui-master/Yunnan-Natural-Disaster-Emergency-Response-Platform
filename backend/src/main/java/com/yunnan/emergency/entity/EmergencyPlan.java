package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableField;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;

@TableName("emergency_plans")
public class EmergencyPlan {

    @TableId(type = IdType.AUTO)
    private Long id;

    private String planNo;

    private String title;

    private Long incidentId;

    private String disasterType;

    private String riskLevel;

    private String areaName;

    private String source;

    private Long generatedBy;

    private String status;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private List<Map<String, Object>> materials;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private List<Map<String, Object>> teams;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private List<Map<String, Object>> shelters;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private Map<String, Object> evacuation;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private List<Map<String, Object>> shortTermMeasures;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private List<Map<String, Object>> midTermMeasures;

    @TableField(typeHandler = com.baomidou.mybatisplus.extension.handlers.JacksonTypeHandler.class)
    private List<Map<String, Object>> longTermMeasures;

    private String remarks;

    private String content;

    private Integer version;

    private Long parentId;

    private Long approvedBy;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime approvedAt;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime createdAt;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updatedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public String getPlanNo() { return planNo; }
    public void setPlanNo(String planNo) { this.planNo = planNo; }
    public String getTitle() { return title; }
    public void setTitle(String title) { this.title = title; }
    public Long getIncidentId() { return incidentId; }
    public void setIncidentId(Long incidentId) { this.incidentId = incidentId; }
    public String getDisasterType() { return disasterType; }
    public void setDisasterType(String disasterType) { this.disasterType = disasterType; }
    public String getRiskLevel() { return riskLevel; }
    public void setRiskLevel(String riskLevel) { this.riskLevel = riskLevel; }
    public String getAreaName() { return areaName; }
    public void setAreaName(String areaName) { this.areaName = areaName; }
    public String getSource() { return source; }
    public void setSource(String source) { this.source = source; }
    public Long getGeneratedBy() { return generatedBy; }
    public void setGeneratedBy(Long generatedBy) { this.generatedBy = generatedBy; }
    public String getStatus() { return status; }
    public void setStatus(String status) { this.status = status; }
    public List<Map<String, Object>> getMaterials() { return materials; }
    public void setMaterials(List<Map<String, Object>> materials) { this.materials = materials; }
    public List<Map<String, Object>> getTeams() { return teams; }
    public void setTeams(List<Map<String, Object>> teams) { this.teams = teams; }
    public List<Map<String, Object>> getShelters() { return shelters; }
    public void setShelters(List<Map<String, Object>> shelters) { this.shelters = shelters; }
    public Map<String, Object> getEvacuation() { return evacuation; }
    public void setEvacuation(Map<String, Object> evacuation) { this.evacuation = evacuation; }
    public List<Map<String, Object>> getShortTermMeasures() { return shortTermMeasures; }
    public void setShortTermMeasures(List<Map<String, Object>> shortTermMeasures) { this.shortTermMeasures = shortTermMeasures; }
    public List<Map<String, Object>> getMidTermMeasures() { return midTermMeasures; }
    public void setMidTermMeasures(List<Map<String, Object>> midTermMeasures) { this.midTermMeasures = midTermMeasures; }
    public List<Map<String, Object>> getLongTermMeasures() { return longTermMeasures; }
    public void setLongTermMeasures(List<Map<String, Object>> longTermMeasures) { this.longTermMeasures = longTermMeasures; }
    public String getRemarks() { return remarks; }
    public void setRemarks(String remarks) { this.remarks = remarks; }
    public String getContent() { return content; }
    public void setContent(String content) { this.content = content; }
    public Integer getVersion() { return version; }
    public void setVersion(Integer version) { this.version = version; }
    public Long getParentId() { return parentId; }
    public void setParentId(Long parentId) { this.parentId = parentId; }
    public Long getApprovedBy() { return approvedBy; }
    public void setApprovedBy(Long approvedBy) { this.approvedBy = approvedBy; }
    public LocalDateTime getApprovedAt() { return approvedAt; }
    public void setApprovedAt(LocalDateTime approvedAt) { this.approvedAt = approvedAt; }
    public LocalDateTime getCreatedAt() { return createdAt; }
    public void setCreatedAt(LocalDateTime createdAt) { this.createdAt = createdAt; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
