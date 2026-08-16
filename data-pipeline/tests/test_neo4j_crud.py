"""Neo4j CRUD 测试

测试目标：
  1. 通过 Spring Boot /neo4j/nodes/{label} 接口完成节点增删改查
  2. 验证 Neo4j 节点的业务主键与 SQL 表 ID 对应
  3. 验证关系创建/删除

通过标准：
  - 创建节点后能查询到
  - 更新节点属性后能反映
  - 删除节点后查询返回 null
  - 关系能正确建立和删除
"""
from __future__ import annotations

import json
import uuid

import pytest

from tests.conftest import integration, require_service


# ============ 集成测试：真实 Neo4j（通过 Spring Boot 接口） ============

@integration
class TestNeo4jCrudIntegration:
    """Neo4j 节点/关系 CRUD 集成测试"""

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

    def test_resource_node_full_crud(self, http_client, spring_boot_base):
        """资源节点完整 CRUD 周期：创建→查询→更新→删除"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        # 用一个不与 SQL 冲突的大随机 ID 做测试
        test_id = 9_999_000 + int(uuid.uuid4().hex[:5], 16) % 1000
        label = "Resource"
        unique_name = f"测试资源-{uuid.uuid4().hex[:6]}"

        try:
            # 1. 创建节点
            resp = http_client.post(
                f"{spring_boot_base}/neo4j/nodes/{label}",
                json={
                    "resourceId": test_id,
                    "resourceNo": "RES-TEST-" + str(test_id),
                    "name": unique_name,
                    "category": "测试",
                    "totalQty": 100,
                    "availableQty": 100,
                },
                headers=headers,
            )
            assert resp.status_code == 200, f"创建节点失败: {resp.text}"
            print(f"\n[创建节点] label={label}, resourceId={test_id}")

            # 2. 查询节点
            resp = http_client.get(f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}", headers=headers)
            assert resp.status_code == 200, f"查询节点失败: {resp.text}"
            node = resp.json().get("data", {})
            assert node is not None, "查询返回 null"
            props = node.get("properties", {})
            assert props.get("name") == unique_name
            assert props.get("resourceId") == test_id
            print(f"[查询节点] properties={json.dumps(props, ensure_ascii=False)}")

            # 3. 更新节点
            new_name = unique_name + "-已更新"
            resp = http_client.put(
                f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}",
                json={"name": new_name, "availableQty": 80},
                headers=headers,
            )
            assert resp.status_code == 200, f"更新节点失败: {resp.text}"

            # 4. 验证更新
            resp = http_client.get(f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}", headers=headers)
            props = resp.json().get("data", {}).get("properties", {})
            assert props.get("name") == new_name, f"更新未生效: {props}"
            assert props.get("availableQty") == 80
            print(f"[更新节点] name={new_name}, availableQty=80")

            # 5. 统计节点数（应 > 0）
            resp = http_client.get(f"{spring_boot_base}/neo4j/count/{label}", headers=headers)
            assert resp.status_code == 200
            count = resp.json().get("data", 0)
            assert count > 0, f"节点数应为 >0, 实际 {count}"

        finally:
            # 6. 删除节点（无论前面是否失败都要清理）
            http_client.delete(f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}", headers=headers)

            # 7. 确认已删除
            resp = http_client.get(f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}", headers=headers)
            data = resp.json().get("data")
            assert data is None, f"删除后仍能查询到节点: {data}"
            print(f"[删除节点] resourceId={test_id} 已删除并验证")

    def test_incident_node_crud(self, http_client, spring_boot_base):
        """灾情节点 CRUD"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        test_id = 9_990_000 + int(uuid.uuid4().hex[:5], 16) % 1000
        label = "Incident"

        try:
            # 创建
            resp = http_client.post(
                f"{spring_boot_base}/neo4j/nodes/{label}",
                json={
                    "incidentId": test_id,
                    "incidentNo": "INC-TEST-" + str(test_id),
                    "title": "集成测试灾情",
                    "disasterType": "地震",
                    "riskLevel": "中",
                    "status": "待核验",
                    "locationName": "测试地点",
                },
                headers=headers,
            )
            assert resp.status_code == 200, f"创建灾情节点失败: {resp.text}"

            # 查询
            resp = http_client.get(f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}", headers=headers)
            props = resp.json().get("data", {}).get("properties", {})
            assert props.get("disasterType") == "地震"
            assert props.get("incidentId") == test_id
            print(f"\n[灾情节点] 创建并查询成功: {props}")

        finally:
            http_client.delete(f"{spring_boot_base}/neo4j/nodes/{label}/{test_id}", headers=headers)

    def test_relationship_create_and_delete(self, http_client, spring_boot_base):
        """关系创建与删除"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        incident_id = 9_980_000 + int(uuid.uuid4().hex[:5], 16) % 1000
        resource_id = 9_980_500 + int(uuid.uuid4().hex[:5], 16) % 1000

        try:
            # 创建两个节点
            http_client.post(f"{spring_boot_base}/neo4j/nodes/Incident",
                json={"incidentId": incident_id, "title": "关系测试灾情", "disasterType": "地震"},
                headers=headers)
            http_client.post(f"{spring_boot_base}/neo4j/nodes/Resource",
                json={"resourceId": resource_id, "name": "关系测试资源", "category": "救援队"},
                headers=headers)

            # 创建关系
            resp = http_client.post(
                f"{spring_boot_base}/neo4j/relationships",
                json={
                    "fromLabel": "Resource",
                    "fromId": resource_id,
                    "toLabel": "Incident",
                    "toId": incident_id,
                    "relType": "RESPONDS_TO",
                    "properties": {"qty": 50},
                },
                headers=headers,
            )
            assert resp.status_code == 200, f"创建关系失败: {resp.text}"
            rel = resp.json().get("data", {})
            rel_id = rel.get("id")
            assert rel_id is not None
            print(f"\n[创建关系] Resource-{resource_id} -[RESPONDS_TO]-> Incident-{incident_id}, relId={rel_id}")

            # 删除关系
            resp = http_client.delete(f"{spring_boot_base}/neo4j/relationships/{rel_id}", headers=headers)
            assert resp.status_code == 200, f"删除关系失败: {resp.text}"
            print(f"[删除关系] relId={rel_id} 已删除")

        finally:
            http_client.delete(f"{spring_boot_base}/neo4j/nodes/Incident/{incident_id}", headers=headers)
            http_client.delete(f"{spring_boot_base}/neo4j/nodes/Resource/{resource_id}", headers=headers)

    def test_dispatch_graph_returns_nodes_and_edges(self, http_client, spring_boot_base):
        """调度大屏图谱查询应返回 nodes 和 edges 数组"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")
        headers = {"Authorization": f"Bearer {token}"}

        resp = http_client.get(f"{spring_boot_base}/neo4j/dispatch-graph", headers=headers)
        assert resp.status_code == 200, f"查询图谱失败: {resp.text}"
        data = resp.json().get("data", {})
        assert "nodes" in data
        assert "edges" in data
        assert isinstance(data["nodes"], list)
        assert isinstance(data["edges"], list)
        print(f"\n[调度图谱] nodes={data.get('nodeCount', 0)}, edges={data.get('edgeCount', 0)}")
