package com.yunnan.emergency.config;

import org.springframework.boot.context.properties.ConfigurationProperties;
import org.springframework.context.annotation.Configuration;

@Configuration
@ConfigurationProperties(prefix = "neo4j")
public class Neo4jProperties {
    private String uri;
    private String username;
    private String password;
    private String database = "neo4j";

    public String getUri() { return uri; }
    public void setUri(String uri) { this.uri = uri; }
    public String getUsername() { return username; }
    public void setUsername(String username) { this.username = username; }
    public String getPassword() { return password; }
    public void setPassword(String password) { this.password = password; }
    public String getDatabase() { return database; }
    public void setDatabase(String database) { this.database = database; }
}
