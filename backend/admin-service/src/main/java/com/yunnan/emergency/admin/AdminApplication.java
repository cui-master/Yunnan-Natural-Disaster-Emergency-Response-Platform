package com.yunnan.emergency.admin;

import com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

/**
 * 系统管理系统：认证登录 / 用户 / 角色 / 知识库 / 审计 / 系统配置。
 * 作为统一认证入口，对外提供 /api/auth 登录与 JWT 签发。
 */
@SpringBootApplication(scanBasePackages = "com.yunnan.emergency",
        exclude = {DataSourceAutoConfiguration.class, MybatisPlusAutoConfiguration.class})
public class AdminApplication {
    public static void main(String[] args) {
        SpringApplication.run(AdminApplication.class, args);
    }
}
