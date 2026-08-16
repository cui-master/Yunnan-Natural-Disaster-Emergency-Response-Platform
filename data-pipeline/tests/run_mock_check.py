"""前端 mock 残留检测 —— 独立运行脚本（不依赖 pytest）

直接运行：python tests/run_mock_check.py
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent.parent
FRONTEND_ROOT = ROOT / "frontend"
SRC_ROOT = FRONTEND_ROOT / "src"

failures = []
passes = []


def check(name: str, condition: bool, detail: str = ""):
    if condition:
        passes.append(f"[OK] {name}")
        print(f"  [OK] {name}" + (f" - {detail}" if detail else ""))
    else:
        failures.append(f"[FAIL] {name}: {detail}")
        print(f"  [FAIL] {name} - {detail}")


print("\n========== 前端 Mock 残留检测 ==========\n")

# 1. .env.development VITE_USE_MOCK=false
env_file = FRONTEND_ROOT / ".env.development"
if env_file.exists():
    content = env_file.read_text(encoding="utf-8")
    m = re.search(r"^VITE_USE_MOCK\s*=\s*(\w+)", content, re.MULTILINE)
    if m:
        check(".env.development VITE_USE_MOCK",
              m.group(1).lower() == "false",
              f"实际值={m.group(1)}")
    else:
        check(".env.development VITE_USE_MOCK", False, "未设置该变量")
else:
    check(".env.development 存在", False, f"文件不存在: {env_file}")

# 2. api/index.js 无 Math.random()
api_file = SRC_ROOT / "api" / "index.js"
content = api_file.read_text(encoding="utf-8")
random_count = len(re.findall(r"Math\.random\(\)", content))
check("api/index.js 无 Math.random()", random_count == 0, f"发现 {random_count} 处")

# 3. getDispatchGraph 不回退 mock
m = re.search(r"export function getDispatchGraph\([^)]*\)\s*\{(.+?)\n\}", content, re.DOTALL)
if m:
    body = m.group(1)
    check("getDispatchGraph 不回退 mock",
          "mock.commander.getDispatchGraph().data" not in body,
          "仍在使用 mock 数据回退")
    check("getDispatchGraph 调用后端接口",
          "/neo4j/dispatch-graph" in body,
          "未调用 /neo4j/dispatch-graph")
else:
    check("getDispatchGraph 函数存在", False, "未找到函数")

# 4. 关键 API 调用真实端点
critical_apis = [
    ("getCityDisasterCount", "/incidents/dashboard/city-count"),
    ("getWeeklyTrend", "/incidents/dashboard/weekly-trend"),
    ("getDashboardStats", "/incidents/dashboard/stats"),
    ("getResourceList", "/resources/page"),
    ("getKnowledgeList", "/admin/knowledge-bases/page"),
]
for func, url in critical_apis:
    m = re.search(rf"export function {func}\s*\([^)]*\)\s*\{{(.+?)\n\}}", content, re.DOTALL)
    if m:
        body = m.group(1)
        check(f"{func} 调用 {url}", url in body, "未调用真实端点")
    else:
        check(f"{func} 函数存在", False, "未找到函数")

# 5. Dashboard 视图无 Math.random
views_root = SRC_ROOT / "views"
dash_violations = []
if views_root.exists():
    for p in views_root.rglob("Dashboard.vue"):
        c = p.read_text(encoding="utf-8")
        if "Math.random()" in c:
            dash_violations.append(str(p.relative_to(FRONTEND_ROOT)))
check("Dashboard 视图无 Math.random", not dash_violations, str(dash_violations))

# 6. DispatchBoard.vue 硬编码 demo 占位检查（warning）
dispatch_board = views_root / "commander" / "DispatchBoard.vue"
if dispatch_board.exists():
    c = dispatch_board.read_text(encoding="utf-8")
    has_demo = bool(re.search(r"value\s*=\s*[\"']demo[\"']", c))
    has_sample = "XX灾区（示例）" in c
    if has_demo or has_sample:
        print(f"\n  [WARN] DispatchBoard.vue 仍有 demo/示例 占位符（建议清理）")
    else:
        passes.append("[OK] DispatchBoard.vue 无 demo 占位符")

# ============ 结果汇总 ============
print("\n========== 检测结果 ==========")
print(f"通过: {len(passes)} 项")
print(f"失败: {len(failures)} 项")
if failures:
    print("\n失败详情:")
    for f in failures:
        print(f"  {f}")
    sys.exit(1)
else:
    print("\n✓ 前端已严格使用后端 SQL 数据，无 mock 残留")
    sys.exit(0)
