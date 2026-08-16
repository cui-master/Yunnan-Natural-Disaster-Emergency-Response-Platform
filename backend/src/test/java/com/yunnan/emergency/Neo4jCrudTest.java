package com.yunnan.emergency;

import com.yunnan.emergency.service.Neo4jService;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.neo4j.driver.*;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.test.context.ActiveProfiles;
import org.springframework.test.context.TestPropertySource;

import java.util.HashMap;
import java.util.List;
import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;

/**
 * Neo4j CRUD 集成测试
 *
 * 测试目标：
 *   - 节点 Create / Read / Update / Delete
 *   - 关系 Create / Delete
 *   - 业务主键对应（resourceId / incidentId / dispatchOrderId）
 *
 * 运行条件：
 *   - 需要 Neo4j 实例运行在 bolt://localhost:7687
 *   - 设置环境变量 RUN_INTEGRATION=1 才执行
 *
 * 运行命令：
 *   mvn test -Dtest=Neo4jCrudTest -DRUN_INTEGRATION=1
 */
@SpringBootTest
@ActiveProfiles("test")
@TestPropertySource(locations = "classpath:application-test.yml")
@EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION", matches = "1")
class Neo4jCrudTest {

    @Autowired
    private Neo4jService neo4jService;

    @Autowired
    private Driver driver;

    private static final Long TEST_RESOURCE_ID = 9_999_001L;
    private static final Long TEST_INCIDENT_ID = 9_999_002L;
    private static final Long TEST_ORDER_ID = 9_999_003L;

    @BeforeEach
    void cleanupBefore() {
        // 确保测试前没有残留节点
        deleteTestNode("Resource", TEST_RESOURCE_ID);
        deleteTestNode("Incident", TEST_INCIDENT_ID);
        deleteTestNode("DispatchOrder", TEST_ORDER_ID);
    }

    @AfterEach
    void cleanupAfter() {
        deleteTestNode("Resource", TEST_RESOURCE_ID);
        deleteTestNode("Incident", TEST_INCIDENT_ID);
        deleteTestNode("DispatchOrder", TEST_ORDER_ID);
    }

    @Test
    @DisplayName("资源节点完整 CRUD 周期")
    void testResourceNodeCrud() {
        // 1. 创建
        Map<String, Object> props = new HashMap<>();
        props.put("resourceId", TEST_RESOURCE_ID);
        props.put("resourceNo", "RES-TEST-001");
        props.put("name", "测试救援队");
        props.put("category", "救援队");
        props.put("totalQty", 100);
        props.put("availableQty", 100);

        Map<String, Object> created = neo4jService.createNode("Resource", props);
        assertNotNull(created);
        assertEquals("Resource", created.get("label"));
        System.out.println("[创建] Resource 节点: " + created);

        // 2. 查询
        Map<String, Object> queried = neo4jService.getNode("Resource", TEST_RESOURCE_ID);
        assertNotNull(queried, "查询返回 null");
        Map<?, ?> queriedProps = (Map<?, ?>) queried.get("properties");
        assertEquals("测试救援队", queriedProps.get("name"));
        assertEquals(100, queriedProps.get("totalQty"));
        System.out.println("[查询] Resource 节点: " + queriedProps);

        // 3. 更新
        Map<String, Object> updateProps = new HashMap<>();
        updateProps.put("name", "测试救援队-已更新");
        updateProps.put("availableQty", 80);
        Map<String, Object> updated = neo4jService.updateNode("Resource", TEST_RESOURCE_ID, updateProps);
        assertEquals("测试救援队-已更新", ((Map<?, ?>) updated.get("properties")).get("name"));
        assertEquals(80, ((Map<?, ?>) updated.get("properties")).get("availableQty"));
        System.out.println("[更新] Resource 节点: " + updated);

        // 4. 统计
        long count = neo4jService.countByLabel("Resource");
        assertTrue(count > 0, "Resource 节点数应 > 0");
        System.out.println("[统计] Resource 节点数: " + count);

        // 5. 删除
        Map<String, Object> deleted = neo4jService.deleteNode("Resource", TEST_RESOURCE_ID);
        assertEquals(1L, deleted.get("deleted"));
        System.out.println("[删除] Resource 节点: " + deleted);

        // 6. 确认已删除
        assertNull(neo4jService.getNode("Resource", TEST_RESOURCE_ID), "删除后仍能查询到节点");
    }

    @Test
    @DisplayName("灾情节点 CRUD")
    void testIncidentNodeCrud() {
        Map<String, Object> props = new HashMap<>();
        props.put("incidentId", TEST_INCIDENT_ID);
        props.put("incidentNo", "INC-TEST-001");
        props.put("title", "测试灾情");
        props.put("disasterType", "地震");
        props.put("riskLevel", "中");
        props.put("status", "待核验");

        neo4jService.createNode("Incident", props);
        Map<String, Object> node = neo4jService.getNode("Incident", TEST_INCIDENT_ID);
        assertNotNull(node);
        assertEquals("地震", ((Map<?, ?>) node.get("properties")).get("disasterType"));
        System.out.println("[灾情节点] 创建并查询成功: " + node);

        neo4jService.deleteNode("Incident", TEST_INCIDENT_ID);
        assertNull(neo4jService.getNode("Incident", TEST_INCIDENT_ID));
    }

    @Test
    @DisplayName("节点关系创建与删除")
    void testRelationshipCrud() {
        // 创建两个节点
        neo4jService.createNode("Resource", Map.of(
            "resourceId", TEST_RESOURCE_ID,
            "name", "测试救援队",
            "category", "救援队"
        ));
        neo4jService.createNode("Incident", Map.of(
            "incidentId", TEST_INCIDENT_ID,
            "title", "测试灾情",
            "disasterType", "地震"
        ));

        // 创建关系
        Map<String, Object> rel = neo4jService.createRelationship(
            "Resource", TEST_RESOURCE_ID,
            "Incident", TEST_INCIDENT_ID,
            "RESPONDS_TO",
            Map.of("qty", 50)
        );
        assertNotNull(rel.get("id"));
        assertEquals("RESPONDS_TO", rel.get("type"));
        System.out.println("[创建关系] " + rel);

        // 删除关系
        Long relId = ((Number) rel.get("id")).longValue();
        Map<String, Object> deleted = neo4jService.deleteRelationship(relId);
        assertEquals(1L, deleted.get("deleted"));
        System.out.println("[删除关系] relId=" + relId);
    }

    @Test
    @DisplayName("调度大屏图谱查询返回 nodes 和 edges")
    void testDispatchGraph() {
        Map<String, Object> graph = neo4jService.getDispatchGraph(null);
        assertNotNull(graph.get("nodes"));
        assertNotNull(graph.get("edges"));
        assertTrue(graph.get("nodes") instanceof List);
        assertTrue(graph.get("edges") instanceof List);
        System.out.println("[调度图谱] nodes=" + graph.get("nodeCount") + ", edges=" + graph.get("edgeCount"));
    }

    @Test
    @DisplayName("创建节点必须提供业务主键")
    void testCreateNodeRequiresBusinessKey() {
        Map<String, Object> props = new HashMap<>();
        props.put("name", "无主键节点");
        // 缺少 resourceId
        assertThrows(IllegalArgumentException.class, () -> {
            neo4jService.createNode("Resource", props);
        });
    }

    @Test
    @DisplayName("businessKeyOf 反推业务主键字段")
    void testBusinessKeyOf() {
        assertEquals("incidentId", Neo4jService.businessKeyOf("Incident"));
        assertEquals("resourceId", Neo4jService.businessKeyOf("Resource"));
        assertEquals("dispatchOrderId", Neo4jService.businessKeyOf("DispatchOrder"));
        assertEquals("locationId", Neo4jService.businessKeyOf("Location"));
        assertEquals("id", Neo4jService.businessKeyOf("Unknown"));
    }

    private void deleteTestNode(String label, Long id) {
        try {
            neo4jService.deleteNode(label, id);
        } catch (Exception ignored) {
            // 节点不存在是正常情况
        }
    }
}
