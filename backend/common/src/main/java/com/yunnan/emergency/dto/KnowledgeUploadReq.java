package com.yunnan.emergency.dto;

import lombok.Data;

import java.util.List;

@Data
public class KnowledgeUploadReq {
    private String title;
    private String category;
    private List<String> tags;
    private List<String> disasterTypes;
    private String fileUrl;
}
