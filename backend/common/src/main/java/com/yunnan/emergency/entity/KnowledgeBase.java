package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("knowledge_bases")
public class KnowledgeBase {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String kbKey;
    private String kbName;
    private String datasetId;
    private String description;
    private LocalDateTime createdAt;
    private LocalDateTime updatedAt;
}
