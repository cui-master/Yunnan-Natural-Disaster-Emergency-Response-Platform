package com.yunnan.emergency.config;

import org.slf4j.Logger;
import org.slf4j.LoggerFactory;
import org.neo4j.driver.AuthTokens;
import org.neo4j.driver.Driver;
import org.neo4j.driver.GraphDatabase;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;

import jakarta.annotation.PreDestroy;

/**
 * Neo4j 驱动配置
 *
 * 资源调度大屏、灾情-资源-调度指令图谱使用 Neo4j 存储。
 * 节点标签：Incident（灾情）、Resource（资源）、DispatchOrder（调度指令）、Location（地点）
 * 关系类型：DISPATCHED_TO（调度→灾情）、LOCATED_AT（资源/灾情→地点）、RESPONDS_TO（资源→灾情）
 *
 * SQL（MySQL emergency_auth）作为主存储，Neo4j 作为图谱视图，二者通过业务 ID 对应。
 */
@Configuration
public class Neo4jConfig {
    public Neo4jConfig(Neo4jProperties neo4jProperties) {
        this.neo4jProperties = neo4jProperties;
    }


    private static final Logger log = LoggerFactory.getLogger(Neo4jConfig.class);

    private final Neo4jProperties neo4jProperties;

    @Bean
    public Driver neo4jDriver() {
        log.info("[neo4j] 初始化驱动: uri={}, user={}, db={}",
            neo4jProperties.getUri(),
            neo4jProperties.getUsername(),
            neo4jProperties.getDatabase());
        return GraphDatabase.driver(
            neo4jProperties.getUri(),
            AuthTokens.basic(neo4jProperties.getUsername(), neo4jProperties.getPassword())
        );
    }

    @PreDestroy
    public void closeDriver() {
        log.info("[neo4j] 关闭驱动");
    }
}
