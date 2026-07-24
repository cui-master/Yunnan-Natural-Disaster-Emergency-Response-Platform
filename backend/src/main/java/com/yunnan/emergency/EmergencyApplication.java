package com.yunnan.emergency;

import org.mybatis.spring.annotation.MapperScan;
import org.springframework.boot.SpringApplication;
import org.springframework.boot.autoconfigure.SpringBootApplication;

@SpringBootApplication
@MapperScan("com.yunnan.emergency.mapper")
public class EmergencyApplication {
    public static void main(String[] args) {
        SpringApplication.run(EmergencyApplication.class, args);
    }
}
