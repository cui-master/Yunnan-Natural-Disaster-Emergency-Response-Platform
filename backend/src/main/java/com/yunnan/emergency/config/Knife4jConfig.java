package com.yunnan.emergency.config;

import io.swagger.v3.oas.models.OpenAPI;
import io.swagger.v3.oas.models.info.Contact;
import io.swagger.v3.oas.models.info.Info;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

@Configuration
public class Knife4jConfig {

    @Bean
    public OpenAPI customOpenAPI() {
        return new OpenAPI()
            .info(new Info()
                .title("云南省自然灾害应急响应平台 API")
                .version("1.0.0")
                .description("云南省自然灾害应急响应平台后端接口文档")
                .contact(new Contact().name("应急平台开发组"))
            );
    }
}
