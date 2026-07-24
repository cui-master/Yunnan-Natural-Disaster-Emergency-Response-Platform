package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.R;
import com.yunnan.emergency.dto.LoginRequest;
import com.yunnan.emergency.dto.LoginResponse;
import com.yunnan.emergency.service.AuthService;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.validation.annotation.Validated;
import org.springframework.web.bind.annotation.GetMapping;
import org.springframework.web.bind.annotation.PostMapping;
import org.springframework.web.bind.annotation.RequestBody;
import org.springframework.web.bind.annotation.RequestMapping;
import org.springframework.web.bind.annotation.RestController;

import javax.validation.Valid;

@RestController
@RequestMapping("/api/auth")
@Validated
public class AuthController {

    @Autowired
    private AuthService authService;

    @PostMapping("/login")
    public R<LoginResponse> login(@RequestBody @Valid LoginRequest req) {
        return R.ok(authService.login(req));
    }

    @GetMapping("/me")
    public R<LoginResponse> me() {
        return R.ok(authService.me());
    }
}
