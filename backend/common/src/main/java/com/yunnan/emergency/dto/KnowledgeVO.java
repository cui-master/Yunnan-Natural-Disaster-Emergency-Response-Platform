package com.yunnan.emergency.dto;

import lombok.Data;

import java.util.List;

@Data
public class KnowledgeVO {
    private Long id;
    private String title;
    private String category;
    private List<String> tags;
    private List<String> disasterTypes;
    private Integer chunkCount;
    private String source;
    private String uploader;
    private String uploadedAt;
    private String updatedAt;
}
