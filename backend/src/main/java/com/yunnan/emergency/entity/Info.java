package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import com.fasterxml.jackson.annotation.JsonFormat;

import java.time.LocalDateTime;

@TableName("info")
public class Info {

    @TableId(type = IdType.AUTO)
    private Long id;

    private Integer totalDisasters;

    private Integer inProgress;

    private Integer pending;

    private Integer affectedPeople;

    private Integer availableResources;

    private Integer rescueTeams;

    @JsonFormat(pattern = "yyyy-MM-dd HH:mm:ss")
    private LocalDateTime updatedAt;

    public Long getId() { return id; }
    public void setId(Long id) { this.id = id; }
    public Integer getTotalDisasters() { return totalDisasters; }
    public void setTotalDisasters(Integer totalDisasters) { this.totalDisasters = totalDisasters; }
    public Integer getInProgress() { return inProgress; }
    public void setInProgress(Integer inProgress) { this.inProgress = inProgress; }
    public Integer getPending() { return pending; }
    public void setPending(Integer pending) { this.pending = pending; }
    public Integer getAffectedPeople() { return affectedPeople; }
    public void setAffectedPeople(Integer affectedPeople) { this.affectedPeople = affectedPeople; }
    public Integer getAvailableResources() { return availableResources; }
    public void setAvailableResources(Integer availableResources) { this.availableResources = availableResources; }
    public Integer getRescueTeams() { return rescueTeams; }
    public void setRescueTeams(Integer rescueTeams) { this.rescueTeams = rescueTeams; }
    public LocalDateTime getUpdatedAt() { return updatedAt; }
    public void setUpdatedAt(LocalDateTime updatedAt) { this.updatedAt = updatedAt; }
}
