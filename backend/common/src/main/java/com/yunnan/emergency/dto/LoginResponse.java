package com.yunnan.emergency.dto;

import lombok.Data;

@Data
public class LoginResponse {
    private String token;
    private String username;
    private String realName;
    private String roleKey;
    private String roleName;
}
