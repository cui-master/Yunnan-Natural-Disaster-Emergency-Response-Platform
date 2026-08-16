package com.yunnan.emergency;

import com.yunnan.emergency.service.AiAgentService;
import com.yunnan.emergency.service.AiService;
import com.yunnan.emergency.service.SseEmitterManager;
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

/**
 * AI Agent 服务测试 —— 两个 Dify 工作流
 *
 * 测试目标：
 *   1. 事件抽取（extract-incident）：调用 FastAPI /api/v1/agent/extract-incident → Dify 工作流 #1
 *   2. 预案检索（retrieve-plans）：调用 FastAPI /api/v1/agent/retrieve-plans → Dify 工作流 #2
 *   3. 方案审查（review-plan）：调用 FastAPI /api/v1/agent/review-plan → Dify 工作流 #3
 *   4. 异常重试机制：失败时自动重试 3 次
 *   5. SSE 进度推送：任务启动/调用中/完成/失败 均推送给前端
 *
 * 测试策略：
 *   - 单元测试（默认运行）：mock AiService 的 HTTP 响应，验证编排逻辑
 *   - 集成测试（RUN_INTEGRATION=1）：真实调用 FastAPI → Dify
 */
@SpringBootTest
@ActiveProfiles("test")
class AiAgentServiceTest {

    @Autowired
    private AiAgentService aiAgentService;

    @MockBean
    private AiService aiService;

    @MockBean
    private SseEmitterManager sseEmitterManager;

    final String SAMPLE_TEXT = "2025年7月20日上午8点30分，云南省昭通市彝良县发生5.2级地震，震源深度10公里。受灾人口约2500人。";

    @Test
    @DisplayName("事件抽取（Dify 工作流 #1）- 同步调用返回结构化结果")
    void testExtractIncidentSync() {
        // mock FastAPI 返回的 Dify 响应
        String mockResp = """
            {
              "task_id": "extract-test-001",
              "status": "succeeded",
              "workflow_run_id": "wr-001",
              "result": {
                "disaster_type": "地震",
                "location": "云南省昭通市彝良县",
                "level": "较大",
                "affected_people": 2500
              }
            }
            """;
        when(aiService.post(eq("/api/v1/agent/extract-incident"), anyMap()))
            .thenReturn(mockResp);

        Map<String, Object> result = aiAgentService.extractIncidentSync(SAMPLE_TEXT);

        assertNotNull(result);
        assertEquals("succeeded", result.get("status"));
        assertNotNull(result.get("result"));
        System.out.println("[事件抽取] 返回: " + result);

        verify(aiService, times(1)).post(eq("/api/v1/agent/extract-incident"), anyMap());
    }

    @Test
    @DisplayName("预案检索（Dify 工作流 #2）- 同步调用返回预案列表")
    void testRetrievePlansSync() {
        String mockResp = """
            {
              "task_id": "retrieve-test-001",
              "status": "succeeded",
              "result": {
                "plans": [
                  {"title": "云南省地震应急预案", "score": 0.95},
                  {"title": "昭通市地质灾害应急预案", "score": 0.88}
                ],
                "total": 2
              }
            }
            """;
        when(aiService.post(eq("/api/v1/agent/retrieve-plans"), anyMap()))
            .thenReturn(mockResp);

        Map<String, Object> result = aiAgentService.retrievePlansSync("地震 应急预案", 5);

        assertNotNull(result);
        assertEquals("succeeded", result.get("status"));
        System.out.println("[预案检索] 返回: " + result);

        verify(aiService, times(1)).post(eq("/api/v1/agent/retrieve-plans"), anyMap());
    }

    @Test
    @DisplayName("方案审查（Dify 工作流 #3）- 同步调用返回审查意见")
    void testReviewPlanSync() {
        String mockResp = """
            {
              "task_id": "review-test-001",
              "status": "succeeded",
              "result": {
                "compliant": true,
                "feasibility": "高",
                "issues": ["医疗物资储备量可能不足"],
                "overall_score": 85
              }
            }
            """;
        when(aiService.post(eq("/api/v1/agent/review-plan"), anyMap()))
            .thenReturn(mockResp);

        Map<String, Object> result = aiAgentService.reviewPlanSync("应急方案内容...", 1L);

        assertNotNull(result);
        assertEquals("succeeded", result.get("status"));
        System.out.println("[方案审查] 返回: " + result);

        verify(aiService, times(1)).post(eq("/api/v1/agent/review-plan"), anyMap());
    }

    @Test
    @DisplayName("异常重试 - 失败时自动重试最多 3 次")
    void testRetryMechanism() {
        when(aiService.post(anyString(), anyMap()))
            .thenThrow(new RuntimeException("Dify 服务超时"))
            .thenThrow(new RuntimeException("Dify 服务超时"))
            .thenReturn("{\"status\":\"succeeded\",\"result\":{}}");

        Map<String, Object> result = aiAgentService.extractIncidentSync(SAMPLE_TEXT);

        assertNotNull(result);
        // 验证调用了 3 次（前两次失败，第三次成功）
        verify(aiService, times(3)).post(anyString(), anyMap());
        System.out.println("[重试机制] 失败 2 次后第 3 次成功");
    }

    @Test
    @DisplayName("异常重试 - 3 次均失败则抛异常")
    void testRetryExhausted() {
        when(aiService.post(anyString(), anyMap()))
            .thenThrow(new RuntimeException("Dify 服务不可达"));

        RuntimeException ex = assertThrows(RuntimeException.class, () -> {
            aiAgentService.extractIncidentSync(SAMPLE_TEXT);
        });

        assertTrue(ex.getMessage().contains("重试3次后仍失败"));
        verify(aiService, times(3)).post(anyString(), anyMap());
        System.out.println("[重试耗尽] 3 次均失败，抛出异常: " + ex.getMessage());
    }

    @Test
    @DisplayName("异步任务返回 taskId 并通过 SSE 推送进度")
    void testAsyncTaskReturnsTaskId() {
        when(aiService.post(anyString(), anyMap()))
            .thenReturn("{\"status\":\"succeeded\",\"result\":{}}");

        String taskId = aiAgentService.extractIncident(SAMPLE_TEXT);

        assertNotNull(taskId);
        assertTrue(taskId.startsWith("extract-"));
        System.out.println("[异步任务] taskId=" + taskId);

        // 等待异步线程完成
        try { Thread.sleep(500); } catch (InterruptedException ignored) {}

        // 验证 SSE 推送了 started 和 completed
        verify(sseEmitterManager, atLeast(2)).sendProgress(eq(taskId), anyString(), anyInt(), anyString(), any());
    }

    @Test
    @DisplayName("空响应检测 - Dify 返回空时抛异常")
    void testEmptyResponseHandling() {
        when(aiService.post(anyString(), anyMap()))
            .thenReturn("");

        RuntimeException ex = assertThrows(RuntimeException.class, () -> {
            aiAgentService.extractIncidentSync(SAMPLE_TEXT);
        });

        assertTrue(ex.getMessage().contains("重试3次后仍失败"));
        System.out.println("[空响应] 检测到空响应并重试: " + ex.getMessage());
    }

    // ============ 集成测试（需要 FastAPI + Dify 运行） ============

    @Test
    @DisplayName("[集成] 真实调用 Dify 事件抽取工作流")
    @EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION", matches = "1")
    void testRealExtractIncident() {
        Map<String, Object> result = aiAgentService.extractIncidentSync(SAMPLE_TEXT);
        System.out.println("[集成-事件抽取] Dify 真实返回: " + result);
        assertNotNull(result);
    }

    @Test
    @DisplayName("[集成] 真实调用 Dify 预案检索工作流")
    @EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION", matches = "1")
    void testRealRetrievePlans() {
        Map<String, Object> result = aiAgentService.retrievePlansSync("地震 应急预案", 3);
        System.out.println("[集成-预案检索] Dify 真实返回: " + result);
        assertNotNull(result);
    }

    @Test
    @DisplayName("[集成] 真实调用 Dify 方案审查工作流")
    @EnabledIfEnvironmentVariable(named = "RUN_INTEGRATION", matches = "1")
    void testRealReviewPlan() {
        Map<String, Object> result = aiAgentService.reviewPlanSync(
            "## 应急方案\n1. 调派消防队200人\n2. 调派医疗队50人\n3. 调拨帐篷500顶", 1L);
        System.out.println("[集成-方案审查] Dify 真实返回: " + result);
        assertNotNull(result);
    }
}
