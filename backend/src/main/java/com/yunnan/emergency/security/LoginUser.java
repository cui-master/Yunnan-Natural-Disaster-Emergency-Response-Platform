package com.yunnan.emergency.security;

import lombok.Data;

@Data
public class LoginUser {
    private Long id;
    private String username;
    private String roleKey;
    private String realName;
}
