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
    /** 知识库中文名：优化调度 / 风险评估 */
    private String kbName;
    /** Dify 文档 id（删除 / 查状态用） */
    private String difyDocumentId;
    /** 文件名 */
    private String docName;
    /** PARSING / COMPLETED / FAILED */
    private String status;
    private Integer chunkCount;
    private Integer wordCount;
    private String uploader;
    private LocalDateTime uploadedAt;
    private LocalDateTime updatedAt;
}
