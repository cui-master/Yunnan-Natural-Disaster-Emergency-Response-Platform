package com.yunnan.emergency.controller;

import com.yunnan.emergency.common.Result;
import com.yunnan.emergency.entity.User;
import com.yunnan.emergency.service.UserService;
import com.yunnan.emergency.utils.JwtUtils;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import jakarta.servlet.http.HttpServletRequest;
import org.springframework.security.core.annotation.AuthenticationPrincipal;
import org.springframework.web.bind.annotation.*;

@Tag(name = "认证管理", description = "用户登录、注册、获取用户信息等")
@RestController
@RequestMapping("/auth")
public class AuthController {
    public AuthController(UserService userService, JwtUtils jwtUtils) {
        this.userService = userService;
        this.jwtUtils = jwtUtils;
    }


    private final UserService userService;
    private final JwtUtils jwtUtils;

    @Operation(summary = "用户登录")
    @PostMapping("/login")
    public Result<User> login(@RequestBody LoginRequest request) {
        User user = userService.login(request.getUsername(), request.getPassword());
        return Result.success(user);
    }

    @Operation(summary = "获取当前用户信息")
    @GetMapping("/info")
    public Result<User> getInfo(@AuthenticationPrincipal User user) {
        if (user == null) {
            return Result.error(401, "未登录");
        }
        User userInfo = userService.getUserInfo(user.getId());
        return Result.success(userInfo);
    }

    @Operation(summary = "退出登录")
    @PostMapping("/logout")
    public Result<Void> logout() {
        return Result.success();
    }

    public static class LoginRequest {
        private String username;
        private String password;
        public String getUsername() { return username; }
        public void setUsername(String username) { this.username = username; }
        public String getPassword() { return password; }
        public void setPassword(String password) { this.password = password; }
    }
}
