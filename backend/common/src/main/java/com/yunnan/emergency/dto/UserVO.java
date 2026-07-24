package com.yunnan.emergency.dto;

import lombok.Data;

import java.time.LocalDateTime;
import java.util.List;

@Data
public class UserVO {
    private Long id;
    private String username;
    private String realName;
    private String phone;
    private List<String> roles;
    private String status;
    private LocalDateTime createdAt;
    private String lastLoginAt;
}
