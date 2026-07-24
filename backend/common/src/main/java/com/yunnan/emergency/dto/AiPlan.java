package com.yunnan.emergency.dto;

import lombok.Data;

import java.util.List;
import java.util.Map;

@Data
public class AiPlan {
    private String title;
    private String content;
    private List<String> steps;
    private List<Map<String, Object>> resourceSuggestions;
    private List<Map<String, Object>> citations;
}
