package com.yunnan.emergency.resource;

import com.baomidou.mybatisplus.autoconfigure.MybatisPlusAutoConfiguration;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;
import org.springframework.boot.autoconfigure.jdbc.DataSourceAutoConfiguration;

/**
 * 资源管理系统：人员 / 车辆 / 物资 / 避难场所。
 */
@SpringBootApplication(scanBasePackages = "com.yunnan.emergency",
        exclude = {DataSourceAutoConfiguration.class, MybatisPlusAutoConfiguration.class})
public class ResourceApplication {
    public static void main(String[] args) {
        SpringApplication.run(ResourceApplication.class, args);
    }
}
