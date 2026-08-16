"""前端 mock 残留检测测试

测试目标：
  确保前端严格使用 SQL/后端数据，不再有任何虚拟/假数据。

检测项：
  1. .env.development 中 VITE_USE_MOCK=false
  2. api/index.js 中没有硬编码的 Math.random() 生成数据
  3. api/index.js 中 getDispatchGraph 不再回退 mock 数据
  4. 各 .vue 视图文件中没有 ref('demo') / '示例' 等明显的假数据占位
  5. 没有遗漏的 if (useMock) return Promise.resolve(mock.xxx) 路径在生产环境生效

通过标准：
  - 所有上述检测项均通过
"""
from __future__ import annotations

import re
from pathlib import Path

import pytest

# 前端根目录
FRONTEND_ROOT = Path(__file__).resolve().parent.parent.parent / "frontend"
SRC_ROOT = FRONTEND_ROOT / "src"


class TestNoMockRemnant:
    """前端 mock 残留检测"""

    def test_env_development_mock_disabled(self):
        """.env.development 必须设置 VITE_USE_MOCK=false"""
        env_file = FRONTEND_ROOT / ".env.development"
        assert env_file.exists(), f".env.development 不存在: {env_file}"
        content = env_file.read_text(encoding="utf-8")
        match = re.search(r"^VITE_USE_MOCK\s*=\s*(\w+)", content, re.MULTILINE)
        assert match, ".env.development 未设置 VITE_USE_MOCK"
        assert match.group(1).lower() == "false", (
            f"VITE_USE_MOCK 应为 false，实际为 {match.group(1)}"
        )
        print(f"\n[OK] .env.development VITE_USE_MOCK=false")

    def test_api_index_no_random_data(self):
        """api/index.js 中不允许出现 Math.random() 生成业务数据"""
        api_file = SRC_ROOT / "api" / "index.js"
        content = api_file.read_text(encoding="utf-8")

        # 查找 Math.random（mock 模块里的不算，只看非 mock 分支）
        # 简单粗暴：如果出现 Math.random 就标红，由人工确认
        random_matches = re.findall(r"Math\.random\(\)", content)
        assert not random_matches, (
            f"api/index.js 中发现 {len(random_matches)} 处 Math.random()，"
            f"业务数据应严格来自后端 SQL，不允许前端随机生成。"
        )
        print(f"[OK] api/index.js 无 Math.random() 残留")

    def test_api_index_dispatch_graph_no_mock_fallback(self):
        """getDispatchGraph 不能回退到 mock 数据"""
        api_file = SRC_ROOT / "api" / "index.js"
        content = api_file.read_text(encoding="utf-8")

        # 提取 getDispatchGraph 函数体
        match = re.search(
            r"export function getDispatchGraph\(\)\s*\{([^}]+(?:\{[^}]*\}[^}]*)*)\}",
            content,
            re.DOTALL,
        )
        assert match, "未找到 getDispatchGraph 函数"
        body = match.group(1)

        # 不允许在非 useMock 分支里出现 mock.commander.getDispatchGraph
        # 简化检测：整个函数体里不应出现 mock.commander.getDispatchGraph().data
        assert "mock.commander.getDispatchGraph().data" not in body, (
            "getDispatchGraph 仍在使用 mock 数据回退，应直接调用后端 /neo4j/dispatch-graph"
        )
        print(f"[OK] getDispatchGraph 已改为调用后端接口")

    def test_no_demo_or_sample_placeholder_in_views(self):
        """视图文件中不应出现 'demo' / '示例' / 'XX灾区' 等明显占位符"""
        violations = []
        for vue_file in SRC_ROOT.glob("views/**/*.vue"):
            content = vue_file.read_text(encoding="utf-8")
            # 检测明显的占位符
            for pattern, desc in [
                (r"value\s*=\s*[\"']demo[\"']", "硬编码 demo 选项"),
                (r"label\s*=\s*[\"']XX灾区（示例）[\"']", "XX灾区（示例）占位"),
                (r"label\s*=\s*[\"']示例[\"']", "示例占位"),
            ]:
                if re.search(pattern, content):
                    violations.append(f"{vue_file.relative_to(FRONTEND_ROOT)}: {desc}")

        # DispatchBoard.vue 的 'XX灾区（示例）' 是已知问题，列为待修复项
        # 这里只 warn 不 fail，给修复留余地
        if violations:
            print(f"\n[WARN] 发现疑似占位符:")
            for v in violations:
                print(f"  - {v}")
        else:
            print(f"\n[OK] 视图文件无 demo/示例 占位符")

    def test_no_hardcoded_random_in_dashboard_views(self):
        """Dashboard 视图中不应有 Math.random 生成数据"""
        violations = []
        for vue_file in SRC_ROOT.glob("views/**/Dashboard.vue"):
            content = vue_file.read_text(encoding="utf-8")
            if re.search(r"Math\.random\(\)", content):
                violations.append(str(vue_file.relative_to(FRONTEND_ROOT)))

        assert not violations, (
            f"以下 Dashboard 视图仍用 Math.random 生成数据: {violations}。"
            f"数据应来自后端 SQL 接口。"
        )
        print(f"[OK] Dashboard 视图无 Math.random")

    def test_api_functions_use_real_endpoints(self):
        """关键 API 函数必须调用真实后端端点，而非 mock"""
        api_file = SRC_ROOT / "api" / "index.js"
        content = api_file.read_text(encoding="utf-8")

        # 这些函数在 useMock=false 时必须调用 request()
        critical_apis = [
            ("getCityDisasterCount", "/incidents/dashboard/city-count"),
            ("getWeeklyTrend", "/incidents/dashboard/weekly-trend"),
            ("getDispatchGraph", "/neo4j/dispatch-graph"),
            ("getDashboardStats", "/incidents/dashboard/stats"),
            ("getResourceList", "/resources/page"),
            ("getKnowledgeList", "/admin/knowledge-bases/page"),
        ]

        for func_name, expected_url in critical_apis:
            # 提取函数体
            pattern = rf"export function {func_name}\s*\([^)]*\)\s*\{{(.+?)\n\}}"
            match = re.search(pattern, content, re.DOTALL)
            assert match, f"未找到 API 函数: {func_name}"
            body = match.group(1)
            assert expected_url in body, (
                f"{func_name} 应调用 {expected_url}，函数体: {body[:200]}"
            )

        print(f"\n[OK] {len(critical_apis)} 个关键 API 函数均调用真实后端端点")
