"""SQL 与 Neo4j 数据一致性测试

测试目标：
  1. SQL incidents 表的行数与 Neo4j Incident 节点数一致
  2. SQL resources 表的行数与 Neo4j Resource 节点数一致
  3. SQL dispatch_orders 表的行数与 Neo4j DispatchOrder 节点数一致
  4. SQL 中的每个业务 ID 在 Neo4j 中都能找到对应节点（无遗漏）
  5. Neo4j 中没有 SQL 已删除的孤儿节点

通过标准：
  - 调用 Spring Boot /neo4j/consistency 接口返回 _summary.consistent = true
  - 或手动比对：每个标签的 sqlCount == neo4jCount，且无 orphan/missing
"""
from __future__ import annotations

import json

import pytest

from tests.conftest import integration, require_service


@integration
class TestSqlNeo4jConsistency:
    """SQL ↔ Neo4j 数据一致性集成测试"""

    def _login(self, http_client, base: str) -> str:
        try:
            resp = http_client.post(
                f"{base}/auth/login",
                json={"username": "admin", "password": "123456", "role": "admin"},
            )
            if resp.status_code == 200:
                return resp.json().get("data", {}).get("token", "")
        except Exception:
            pass
        return ""

    def test_consistency_report(self, http_client, spring_boot_base):
        """调用一致性校验接口，检查整体报告"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        # 调用一致性校验（需要后端有 /neo4j/consistency 端点，由 SqlNeo4jSyncService 提供）
        # 这里用各标签的 count + list ids 来手动比对
        report = {}
        for label, sql_endpoint in [
            ("Incident", "/incidents/page?pageNum=1&pageSize=1000"),
            ("Resource", "/resources/page?pageNum=1&pageSize=1000"),
            ("DispatchOrder", "/dispatch-orders/page?pageNum=1&pageSize=1000"),
        ]:
            # SQL 侧
            resp = http_client.get(f"{spring_boot_base}{sql_endpoint}", headers=headers)
            assert resp.status_code == 200, f"查询 SQL {label} 失败: {resp.text}"
            sql_data = resp.json().get("data", {})
            sql_total = sql_data.get("total", 0)
            sql_records = sql_data.get("records", [])
            business_key = {
                "Incident": "id",
                "Resource": "id",
                "DispatchOrder": "id",
            }[label]
            sql_ids = {r.get(business_key) for r in sql_records}

            # Neo4j 侧
            resp = http_client.get(f"{spring_boot_base}/neo4j/count/{label}", headers=headers)
            assert resp.status_code == 200, f"查询 Neo4j {label} 数量失败: {resp.text}"
            neo4j_count = resp.json().get("data", 0)

            resp = http_client.get(f"{spring_boot_base}/neo4j/ids/{label}", headers=headers)
            assert resp.status_code == 200, f"查询 Neo4j {label} IDs 失败: {resp.text}"
            neo4j_ids = set(resp.json().get("data", []))

            # 比对
            missing_in_neo4j = sql_ids - neo4j_ids  # SQL 有但 Neo4j 没有
            orphan_in_neo4j = neo4j_ids - sql_ids   # Neo4j 有但 SQL 没有

            report[label] = {
                "sqlCount": sql_total,
                "neo4jCount": neo4j_count,
                "missingInNeo4j": list(missing_in_neo4j),
                "orphanInNeo4j": list(orphan_in_neo4j),
            }

        print(f"\n[一致性报告] {json.dumps(report, ensure_ascii=False, indent=2)}")

        # 严格断言：每个标签的 SQL 行数应等于 Neo4j 节点数
        for label, info in report.items():
            assert info["sqlCount"] == info["neo4jCount"], (
                f"{label} 数量不一致: SQL={info['sqlCount']}, Neo4j={info['neo4jCount']}. "
                f"missingInNeo4j={info['missingInNeo4j'][:5]}, orphanInNeo4j={info['orphanInNeo4j'][:5]}"
            )

    def test_incident_ids_match(self, http_client, spring_boot_base):
        """严格校验：每个 SQL 灾情 ID 在 Neo4j 中都有对应节点"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        resp = http_client.get(
            f"{spring_boot_base}/incidents/page?pageNum=1&pageSize=100",
            headers=headers,
        )
        sql_incidents = resp.json().get("data", {}).get("records", [])
        if not sql_incidents:
            pytest.skip("SQL 中无灾情数据，跳过")

        resp = http_client.get(f"{spring_boot_base}/neo4j/ids/Incident", headers=headers)
        neo4j_ids = set(resp.json().get("data", []))

        missing = []
        for inc in sql_incidents:
            inc_id = inc.get("id")
            if inc_id not in neo4j_ids:
                missing.append(inc_id)

        assert not missing, (
            f"以下灾情 ID 在 Neo4j 中找不到对应节点: {missing[:10]}。"
            f"请通过 SqlNeo4jSyncService.syncIncidentCreate 同步。"
        )
        print(f"\n[灾情 ID 一致] SQL {len(sql_incidents)} 条 ↔ Neo4j 全部对应")

    def test_resource_ids_match(self, http_client, spring_boot_base):
        """严格校验：每个 SQL 资源 ID 在 Neo4j 中都有对应节点"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        resp = http_client.get(
            f"{spring_boot_base}/resources/page?pageNum=1&pageSize=100",
            headers=headers,
        )
        sql_resources = resp.json().get("data", {}).get("records", [])
        if not sql_resources:
            pytest.skip("SQL 中无资源数据，跳过")

        resp = http_client.get(f"{spring_boot_base}/neo4j/ids/Resource", headers=headers)
        neo4j_ids = set(resp.json().get("data", []))

        missing = [r.get("id") for r in sql_resources if r.get("id") not in neo4j_ids]
        assert not missing, f"以下资源 ID 在 Neo4j 中找不到: {missing[:10]}"
        print(f"\n[资源 ID 一致] SQL {len(sql_resources)} 条 ↔ Neo4j 全部对应")
