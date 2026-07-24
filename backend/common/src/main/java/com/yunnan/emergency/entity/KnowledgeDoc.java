package com.yunnan.emergency.entity;

import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.annotation.TableId;
import com.baomidou.mybatisplus.annotation.TableName;
import lombok.Data;

import java.time.LocalDateTime;

@Data
@TableName("knowledge_docs")
public class KnowledgeDoc {
    @TableId(type = IdType.AUTO)
    private Long id;
    private String title;
    private String category;
    private String tagList;
    private String disasterList;
    private String fileUrl;
    private Integer chunkCount;
    private String source;
    private String uploader;
    private LocalDateTime uploadedAt;
    private LocalDateTime updatedAt;
}
