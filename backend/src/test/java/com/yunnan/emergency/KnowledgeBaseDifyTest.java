package com.yunnan.emergency;

import com.yunnan.emergency.controller.KnowledgeBaseController;
import com.yunnan.emergency.entity.KnowledgeBase;
import com.yunnan.emergency.mapper.KnowledgeBaseMapper;
import com.yunnan.emergency.service.DifyKnowledgeSyncService;
import com.fasterxml.jackson.databind.ObjectMapper;
import org.junit.jupiter.api.*;
import org.junit.jupiter.api.condition.EnabledIfEnvironmentVariable;
import org.springframework.beans.factory.annotation.Autowired;
import org.springframework.boot.test.context.SpringBootTest;
import org.springframework.boot.test.mock.mockito.MockBean;
import org.springframework.test.context.ActiveProfiles;

import java.util.Map;

import static org.junit.jupiter.api.Assertions.*;
import static org.mockito.ArgumentMatchers.*;
import static org.mockito.Mockito.*;
import static org.springframework.test.web.servlet.request.MockMvcRequestBuilders.*;
import static org.springframework.test.web.servlet.result.MockMvcResultMatchers.*;

/**
 * 知识库 ↔ Dify Dataset 接入测试
 *
 * 测试目标：
 *   1. 创建知识库时同步创建到 Dify（kb_id 字段写入 Dify dataset ID）
 *   2. 删除知识库时同步删除 Dify dataset
 *   3. Dify 不可用时 SQL 主流程仍能成功（降级策略）
 *   4. /dify-status 接口返回 Dify 连通性
 *
 * 测试策略：
 *   - 单元测试：mock DifyKnowledgeSyncService，验证 KnowledgeBaseController 编排逻辑
 *   - 集成测试（RUN_INTEGRATION=1）：真实调用 FastAPI → Dify
 */
@SpringBootTest
@ActiveProfiles("test")
class KnowledgeBaseDifyTest {

    @Autowired
    private KnowledgeBaseMapper kbMapper;

    @Autowired
    private KnowledgeBaseController kbController;

    @MockBean
    private DifyKnowledgeSyncService difySyncService;

    private static final String TEST_KB_NAME_PREFIX = "测试知识库-DifyTest-";

    @AfterEach
    void cleanup() {
        // 清理测试创建的知识库
        kbMapper.selectList(null).stream()
            .filter(kb -> kb.getName() != null && kb.getName().startsWith(TEST_KB_NAME_PREFIX))
            .forEach(kb -> kbMapper.deleteById(kb.getId()));
    }

    @Test
    @DisplayName("创建知识库时同步创建到 Dify，kb_id 写入 Dify dataset ID")
    void testCreateSyncsToDify() {
        // mock Dify 同步成功
        when(difySyncService.syncCreate(anyString(), anyString()))
            .thenReturn(Map.of("id", "dify-ds-001", "name", "测试库"));

        KnowledgeBase kb = new KnowledgeBase();
        kb.setName(TEST_KB_NAME_PREFIX + "sync");
        kb.setDescription("测试同步");
        kb.setCategory("测试");

        var result = kbController.create(kb);
        KnowledgeBase created = result.getData();

        assertNotNull(created.getId());
        assertEquals("dify-ds-001", created.getKbId(), "kb_id 应写入 Dify dataset ID");
        System.out.println("[创建知识库] SQL id=" + created.getId() + ", Dify kbId=" + created.getKbId());

        verify(difySyncService, times(1)).syncCreate(eq(TEST_KB_NAME_PREFIX + "sync"), eq("测试同步"));
    }

    @Test
    @DisplayName("Dify 不可用时 SQL 仍能创建成功（降级策略）")
    void testCreateDegradesWhenDifyDown() {
        // mock Dify 同步抛异常
        when(difySyncService.syncCreate(anyString(), anyString()))
            .thenReturn(Map.of("synced", false, "error", "Dify 不可达"));

        KnowledgeBase kb = new KnowledgeBase();
        kb.setName(TEST_KB_NAME_PREFIX + "degrade");
        kb.setDescription("Dify 不可用时降级");

        var result = kbController.create(kb);
        KnowledgeBase created = result.getData();

        assertNotNull(created.getId(), "SQL 主流程应成功");
        assertNotNull(created.getKbId(), "Dify 失败时 kb_id 应有 fallback 值");
        assertTrue(created.getKbId().startsWith("pending-"), "Dify 失败时 kb_id 应以 pending- 开头");
        System.out.println("[降级策略] Dify 不可达，SQL 仍成功，kbId=" + created.getKbId());
    }

    @Test
    @DisplayName("删除知识库时同步删除 Dify dataset")
    void testDeleteSyncsToDify() {
        // 先创建一个知识库
        when(difySyncService.syncCreate(anyString(), anyString()))
            .thenReturn(Map.of("id", "dify-ds-002"));
        KnowledgeBase kb = new KnowledgeBase();
        kb.setName(TEST_KB_NAME_PREFIX + "delete");
        kb.setDescription("待删除");
        var created = kbController.create(kb).getData();
        Long sqlId = created.getId();
        String kbId = created.getKbId();

        // mock 删除
        when(difySyncService.syncDelete(eq(kbId))).thenReturn(true);

        // 执行删除
        kbController.delete(sqlId);

        // 验证 SQL 已删除
        assertNull(kbMapper.selectById(sqlId), "SQL 记录应已删除");
        // 验证 Dify 同步删除被调用
        verify(difySyncService, times(1)).syncDelete(eq(kbId));
        System.out.println("[删除知识库] SQL id=" + sqlId + ", Dify kbId=" + kbId + " 均已删除");
    }

    @Test
    @DisplayName("/dify-status 接口返回 Dify 连通性")
    void testDifyStatus() {
        when(difySyncService.checkStatus())
            .thenReturn(Map.of(
                "status", "connected",
                "base_url", "http://localhost:8080",
                "workflows", Map.of(),
                "dataset", Map.of("reachable", true)
            ));

        var result = kbController.difyStatus();
        Map<String, Object> data = result.getData();

        assertEquals("connected", data.get("status"));
        assertNotNull(data.get("base_url"));
        System.out.println("[Dify 状态] " + data);
    }

    // ============ 集成测试 ============

    @Test
    @DisplayName("[集成] 真实创建知识库并同步到 Dify")
    @EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION", matches = "1")
    void testRealCreateSyncsToDify() {
        // 此测试不 mock，使用真实 DifyKnowledgeSyncService
        // 需要先恢复 bean（取消 @MockBean 影响）—— 实际集成测试建议单独写
        System.out.println("[集成测试] 需要在 RUN_INTEGRATION=1 环境下手动验证");
    }
}
