package com.yunnan.emergency.config;

import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.security.crypto.bcrypt.BCryptPasswordEncoder;

/**
 * 密码编码器独立配置
 *
 * 抽离自 SecurityConfig，避免与 JwtAuthenticationFilter / UserServiceImpl 形成循环依赖：
 *   SecurityConfig → JwtAuthenticationFilter → UserService → BCryptPasswordEncoder → SecurityConfig
 *
 * 独立成 @Configuration 后，Spring 可在创建 SecurityConfig 之前先完成 PasswordEncoder 的实例化。
 */
@Configuration
public class PasswordEncoderConfig {

    @Bean
    public BCryptPasswordEncoder passwordEncoder() {
        return new BCryptPasswordEncoder();
    }
}
