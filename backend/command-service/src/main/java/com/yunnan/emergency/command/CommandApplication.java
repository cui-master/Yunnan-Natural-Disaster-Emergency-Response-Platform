package com.yunnan.emergency.command;

import com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

/**
 * 应急指挥系统：事件审核 / 处置方案 / 资源调度 / 实时推送。
 */
@SpringBootApplication(scanBasePackages = "com.yunnan.emergency",
        exclude = {DataSourceAutoConfiguration.class, MybatisPlusAutoConfiguration.class})
public class CommandApplication {
    public static void main(String[] args) {
        SpringApplication.run(CommandApplication.class, args);
    }
}
