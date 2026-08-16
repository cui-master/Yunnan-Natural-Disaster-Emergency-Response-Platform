package com.yunnan.emergency;

import com.yunnan.emergency.service.SqlNeo4jSyncService;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * SQL ↔ Neo4j 数据一致性测试
 *
 * 测试目标：
 *   1. 调用 verifyConsistency() 返回完整一致性报告
 *   2. 各标签的 SQL 行数与 Neo4j 节点数一致
 *   3. 没有 orphan 节点（Neo4j 有但 SQL 已删除）
 *   4. 没有 missing 节点（SQL 有但 Neo4j 没有）
 *
 * 运行条件：
 *   - MySQL emergency_auth 数据库已初始化（执行 deploy/sql/schema.sql + data.sql）
 *   - Neo4j 实例运行
 *   - 设置环境变量 RUN_INTEGRATION=1
 */
@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(locations = "classpath:application-test.yml")
@EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION", matches = "1")
class SqlNeo4jConsistencyTest {

    @Autowired
    private SqlNeo4jSyncService syncService;

    @Test
    @DisplayName("SQL 与 Neo4j 数据一致性校验报告")
    void testConsistencyReport() {
        Map<String, Object> report = syncService.verifyConsistency();

        assertNotNull(report);
        assertNotNull(report.get("_summary"));
        System.out.println("====== SQL ↔ Neo4j 一致性报告 ======");
        report.forEach((label, value) -> {
            System.out.println("[" + label + "] " + value);
        });

        @SuppressWarnings("unchecked")
        Map<String, Object> summary = (Map<String, Object>) report.get("_summary");
        long totalOrphans = ((Number) summary.get("totalOrphanInNeo4j")).longValue();
        long totalMissing = ((Number) summary.get("totalMissingInNeo4j")).longValue();

        System.out.println("\n汇总: orphanInNeo4j=" + totalOrphans + ", missingInNeo4j=" + totalMissing);
        System.out.println("一致: " + summary.get("consistent"));

        // 严格断言：要么完全一致，要么给出详细差异
        if (totalOrphans > 0 || totalMissing > 0) {
            StringBuilder sb = new StringBuilder("SQL ↔ Neo4j 数据不一致:\n");
            for (String label : new String[]{"Incident", "Resource", "DispatchOrder"}) {
                @SuppressWarnings("unchecked")
                Map<String, Object> entry = (Map<String, Object>) report.get(label);
                sb.append(String.format("  %s: SQL=%s, Neo4j=%s, orphan=%s, missing=%s\n",
                    label,
                    entry.get("sqlCount"),
                    entry.get("neo4jCount"),
                    entry.get("orphanIds"),
                    entry.get("missingInNeo4j")
                ));
            }
            fail(sb.toString());
        }
    }

    @Test
    @DisplayName("Incident 表行数与 Neo4j 节点数对应")
    void testIncidentCountMatches() {
        Map<String, Object> report = syncService.verifyConsistency();
        @SuppressWarnings("unchecked")
        Map<String, Object> incident = (Map<String, Object>) report.get("Incident");

        long sqlCount = ((Number) incident.get("sqlCount")).longValue();
        long neo4jCount = ((Number) incident.get("neo4jCount")).longValue();

        System.out.println("[Incident] SQL=" + sqlCount + ", Neo4j=" + neo4jCount);
        assertEquals(sqlCount, neo4jCount, "Incident 节点数不一致");
    }

    @Test
    @DisplayName("Resource 表行数与 Neo4j 节点数对应")
    void testResourceCountMatches() {
        Map<String, Object> report = syncService.verifyConsistency();
        @SuppressWarnings("unchecked")
        Map<String, Object> resource = (Map<String, Object>) report.get("Resource");

        long sqlCount = ((Number) resource.get("sqlCount")).longValue();
        long neo4jCount = ((Number) resource.get("neo4jCount")).longValue();

        System.out.println("[Resource] SQL=" + sqlCount + ", Neo4j=" + neo4jCount);
        assertEquals(sqlCount, neo4jCount, "Resource 节点数不一致");
    }

    @Test
    @DisplayName("DispatchOrder 表行数与 Neo4j 节点数对应")
    void testDispatchOrderCountMatches() {
        Map<String, Object> report = syncService.verifyConsistency();
        @SuppressWarnings("unchecked")
        Map<String, Object> order = (Map<String, Object>) report.get("DispatchOrder");

        long sqlCount = ((Number) order.get("sqlCount")).longValue();
        long neo4jCount = ((Number) order.get("neo4jCount")).longValue();

        System.out.println("[DispatchOrder] SQL=" + sqlCount + ", Neo4j=" + neo4jCount);
        assertEquals(sqlCount, neo4jCount, "DispatchOrder 节点数不一致");
    }
}
