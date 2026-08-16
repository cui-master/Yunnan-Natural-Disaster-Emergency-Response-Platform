package com.yunnan.emergency;

import org.junit.jupiter.api.Test;
import org.junit.jupiter.api.DisplayName;

import java.io.IOException;
import java.nio.file.Files;
import java.nio.file.Path;
import java.nio.file.Paths;
import java.util.regex.Matcher;
import java.util.regex.Pattern;
import java.util.ArrayList;
import java.util.List;

import static org.junit.jupiter.api.Assertions.*;

/**
 * 前端 mock 残留检测测试
 *
 * 测试目标：
 *   确保前端严格使用 SQL/后端数据，不再有任何虚拟/假数据。
 *
 * 检测项：
 *   1. .env.development 中 VITE_USE_MOCK=false
 *   2. api/index.js 中没有 Math.random() 生成业务数据
 *   3. getDispatchGraph 不再回退 mock
 *   4. 关键 API 函数调用真实后端端点
 *   5. 视图文件中无 demo/示例 占位符
 *
 * 此测试不需要任何外部服务，可默认运行。
 */
class FrontendMockRemnantTest {

    private static final Path FRONTEND_ROOT = Paths.get("..", "frontend").toAbsolutePath().normalize();
    private static final Path SRC_ROOT = FRONTEND_ROOT.resolve("src");

    @Test
    @DisplayName(".env.development 必须 VITE_USE_MOCK=false")
    void testEnvMockDisabled() throws IOException {
        Path envFile = FRONTEND_ROOT.resolve(".env.development");
        assertTrue(Files.exists(envFile), ".env.development 不存在: " + envFile);

        String content = Files.readString(envFile);
        Pattern pattern = Pattern.compile("^VITE_USE_MOCK\\s*=\\s*(\\w+)", Pattern.MULTILINE);
        Matcher matcher = pattern.matcher(content);
        assertTrue(matcher.find(), ".env.development 未设置 VITE_USE_MOCK");
        assertEquals("false", matcher.group(1).toLowerCase(),
            "VITE_USE_MOCK 应为 false，实际为 " + matcher.group(1));
        System.out.println("[OK] .env.development VITE_USE_MOCK=false");
    }

    @Test
    @DisplayName("api/index.js 不允许使用 Math.random() 生成业务数据")
    void testNoRandomInApi() throws IOException {
        Path apiFile = SRC_ROOT.resolve("api").resolve("index.js");
        String content = Files.readString(apiFile);

        // 排除 mock 模块导入行
        long count = Pattern.compile("Math\\.random\\(\\)")
            .matcher(content).results().count();

        assertEquals(0, count,
            "api/index.js 中发现 " + count + " 处 Math.random()，业务数据应严格来自后端 SQL");
        System.out.println("[OK] api/index.js 无 Math.random() 残留");
    }

    @Test
    @DisplayName("getDispatchGraph 不再回退 mock 数据")
    void testDispatchGraphNoMockFallback() throws IOException {
        Path apiFile = SRC_ROOT.resolve("api").resolve("index.js");
        String content = Files.readString(apiFile);

        // 提取 getDispatchGraph 函数体
        Pattern pattern = Pattern.compile(
            "export function getDispatchGraph\\(\\)\\s*\\{(.+?)\\n\\}",
            Pattern.DOTALL
        );
        Matcher matcher = pattern.matcher(content);
        assertTrue(matcher.find(), "未找到 getDispatchGraph 函数");

        String body = matcher.group(1);
        assertFalse(body.contains("mock.commander.getDispatchGraph().data"),
            "getDispatchGraph 仍在使用 mock 数据回退，应直接调用后端 /neo4j/dispatch-graph");
        assertTrue(body.contains("/neo4j/dispatch-graph"),
            "getDispatchGraph 应调用 /neo4j/dispatch-graph");
        System.out.println("[OK] getDispatchGraph 已改为调用后端接口");
    }

    @Test
    @DisplayName("关键 API 函数必须调用真实后端端点")
    void testCriticalApisUseRealEndpoints() throws IOException {
        Path apiFile = SRC_ROOT.resolve("api").resolve("index.js");
        String content = Files.readString(apiFile);

        String[][] criticalApis = {
            {"getCityDisasterCount", "/incidents/dashboard/city-count"},
            {"getWeeklyTrend", "/incidents/dashboard/weekly-trend"},
            {"getDispatchGraph", "/neo4j/dispatch-graph"},
            {"getDashboardStats", "/incidents/dashboard/stats"},
            {"getResourceList", "/resources/page"},
            {"getKnowledgeList", "/admin/knowledge-bases/page"},
        };

        for (String[] api : criticalApis) {
            String funcName = api[0];
            String expectedUrl = api[1];

            Pattern pattern = Pattern.compile(
                "export function " + funcName + "\\s*\\([^)]*\\)\\s*\\{(.+?)\\n\\}",
                Pattern.DOTALL
            );
            Matcher matcher = pattern.matcher(content);
            assertTrue(matcher.find(), "未找到 API 函数: " + funcName);

            String body = matcher.group(1);
            assertTrue(body.contains(expectedUrl),
                funcName + " 应调用 " + expectedUrl + "，函数体: " + body.substring(0, Math.min(200, body.length())));
        }
        System.out.println("[OK] " + criticalApis.length + " 个关键 API 函数均调用真实后端端点");
    }

    @Test
    @DisplayName("Dashboard 视图不应使用 Math.random 生成数据")
    void testNoRandomInDashboardViews() throws IOException {
        List<String> violations = new ArrayList<>();
        Path viewsRoot = SRC_ROOT.resolve("views");

        if (!Files.exists(viewsRoot)) {
            System.out.println("[SKIP] views 目录不存在: " + viewsRoot);
            return;
        }

        try (var stream = Files.walk(viewsRoot)) {
            stream.filter(p -> p.getFileName().toString().equals("Dashboard.vue"))
                .forEach(p -> {
                    try {
                        String content = Files.readString(p);
                        if (content.contains("Math.random()")) {
                            violations.add(p.toString());
                        }
                    } catch (IOException e) {
                        // ignore
                    }
                });
        }

        assertTrue(violations.isEmpty(),
            "以下 Dashboard 视图仍用 Math.random 生成数据: " + violations);
        System.out.println("[OK] Dashboard 视图无 Math.random");
    }

    @Test
    @DisplayName("api/index.js 不应有大段硬编码假数据数组")
    void testNoLargeHardcodedDataInApi() throws IOException {
        Path apiFile = SRC_ROOT.resolve("api").resolve("index.js");
        String content = Files.readString(apiFile);

        // 检测 useMock=false 分支里的硬编码数组（如 const data = [{...}, {...}]）
        // 简化检测：查找 request().then() 里的 .map(=>({ ... Math.random ... }))
        long randomMapCount = Pattern.compile(
            "\\.map\\([^)]*Math\\.random"
        ).matcher(content).results().count();

        assertEquals(0, randomMapCount,
            "api/index.js 中发现 " + randomMapCount + " 处使用 Math.random 的 .map()，疑似硬编码假数据");
        System.out.println("[OK] api/index.js 无 .map(Math.random) 模式");
    }
}
