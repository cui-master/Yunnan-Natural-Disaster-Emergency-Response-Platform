package com.yunnan.emergency.report;

import com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

/**
 * 信息员系统：灾情上报。
 * 共享库 common 提供双数据源、安全 JWT、实体与 Mapper、审计/认证/资源/WebSocket 服务。
 */
@SpringBootApplication(scanBasePackages = "com.yunnan.emergency",
        exclude = {DataSourceAutoConfiguration.class, MybatisPlusAutoConfiguration.class})
public class ReportApplication {
    public static void main(String[] args) {
        SpringApplication.run(ReportApplication.class, args);
    }
}
