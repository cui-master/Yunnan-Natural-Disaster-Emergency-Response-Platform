package com.yunnan.emergency.dto;

import lombok.Data;

import java.util.ArrayList;
import java.util.List;

@Data
public class RoleVO {
    private String name;
    private String key;
    private String description;
    private List<String> permissions = new ArrayList<>();
}
