package com.yunnan.emergency.config;

import com.baomidou.mybatisplus.annotation.DbType;
import com.baomidou.mybatisplus.annotation.IdType;
import com.baomidou.mybatisplus.core.MybatisConfiguration;
import com.baomidou.mybatisplus.core.config.GlobalConfig;
import com.baomidou.mybatisplus.extension.plugins.MybatisPlusInterceptor;
import com.baomidou.mybatisplus.extension.plugins.inner.PaginationInnerInterceptor;
import com.baomidou.mybatisplus.extension.spring.MybatisSqlSessionFactoryBean;
import com.zaxxer.hikari.HikariDataSource;
import org.apache.ibatis.logging.stdout.StdOutImpl;
import org.mybatis.spring.annotation.MapperScan;
import org.springframework.beans.factory.annotation.Qualifier;
import org.springframework.boot.autoconfigure.jdbc.DataSourceProperties;
import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Bean;
import org.springframework.context.annotation.Configuration;
import org.springframework.context.annotation.Primary;
import org.springframework.core.io.support.PathMatchingResourcePatternResolver;

import javax.sql.DataSource;

/**
 * PostgreSQL 数据源（业务 / 地理 / 向量域）
 * 手动双数据源之一；@Primary 标记为主库。
 */
@Configuration
@MapperScan(basePackages = "com.yunnan.emergency.mapper", sqlSessionFactoryRef = "pgSqlSessionFactory")
public class PgDataSourceConfig {

    @Primary
    @Bean("pgDataSourceProperties")
    @ConfigurationProperties("spring.datasource.pg")
    public DataSourceProperties pgDataSourceProperties() {
        return new DataSourceProperties();
    }

    @Primary
    @Bean("pgDataSource")
    public DataSource pgDataSource(@Qualifier("pgDataSourceProperties") DataSourceProperties properties) {
        // 用 initializeDataSourceBuilder：正确把 url 映射到 Hikari 的 jdbcUrl，规避 "jdbcUrl is required"
        return properties.initializeDataSourceBuilder().type(HikariDataSource.class).build();
    }

    @Primary
    @Bean("pgSqlSessionFactory")
    public MybatisSqlSessionFactoryBean pgSqlSessionFactory(@Qualifier("pgDataSource") DataSource dataSource) throws Exception {
        MybatisSqlSessionFactoryBean bean = new MybatisSqlSessionFactoryBean();
        bean.setDataSource(dataSource);

        // 显式 new MybatisConfiguration()，避免 getConfiguration() 在 build 前返回 null 导致 NPE
        MybatisConfiguration configuration = new MybatisConfiguration();
        configuration.setMapUnderscoreToCamelCase(true);
        configuration.setLogImpl(StdOutImpl.class);
        bean.setConfiguration(configuration);

        GlobalConfig globalConfig = new GlobalConfig();
        GlobalConfig.DbConfig dbConfig = new GlobalConfig.DbConfig();
        dbConfig.setIdType(IdType.AUTO);
        globalConfig.setDbConfig(dbConfig);
        bean.setGlobalConfig(globalConfig);

        MybatisPlusInterceptor interceptor = new MybatisPlusInterceptor();
        interceptor.addInnerInterceptor(new PaginationInnerInterceptor(DbType.POSTGRE_SQL));
        bean.setPlugins(interceptor);

        bean.setMapperLocations(new PathMatchingResourcePatternResolver()
                .getResources("classpath*:com/yunnan/emergency/mapper/*.xml"));
        return bean;
    }

    @Primary
    @Bean("pgTransactionManager")
    public org.springframework.jdbc.datasource.DataSourceTransactionManager pgTransactionManager(@Qualifier("pgDataSource") DataSource dataSource) {
        return new org.springframework.jdbc.datasource.DataSourceTransactionManager(dataSource);
    }
}
