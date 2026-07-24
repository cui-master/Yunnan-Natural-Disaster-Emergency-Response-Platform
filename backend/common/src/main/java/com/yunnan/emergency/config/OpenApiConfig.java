package com.yunnan.emergency.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class OpenApiConfig {
    @Bean
    public OpenAPI emergencyOpenAPI() {
        return new OpenAPI().info(new Info()
                .title("云南自然灾害应急协同决策平台 API")
                .version("0.1")
                .description("MVP 垂直切片：灾情上报→审核→方案生成→资源调度→归档"));
    }
}
