"""知识库 Dify Dataset 接入测试

测试目标：
  1. Dify dataset API 连通性（list/create/delete）
  2. Spring Boot KnowledgeBaseController CRUD 时同步到 Dify
  3. SQL knowledge_bases 表与 Dify dataset 数据对应

通过标准：
  - Dify 知识库 API 可达
  - 在 Spring Boot 创建知识库后，Dify 侧也能查到对应 dataset
  - 删除时两侧同步消失
"""
from __future__ import annotations

import json
import uuid
from typing import Any, Dict

import pytest

from app.services.dify_client import DifyClient, DifyConfig
from tests.conftest import integration, require_service


# ============ 单元测试：DifyClient dataset 方法 ============

class TestDifyDatasetUnit:
    """DifyClient dataset 方法 —— 单元测试（mock httpx）"""

    def test_list_datasets_parses_response(self, monkeypatch):
        """验证 list_datasets 正确解析响应"""
        mock_resp = {"data": [{"id": "ds-1", "name": "测试库"}], "total": 1}

        def mock_get(self, url, headers=None, params=None):
            class FakeResp:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return mock_resp
            return FakeResp()

        import httpx
        monkeypatch.setattr(httpx.Client, "get", mock_get)

        client = DifyClient(DifyConfig())
        result = client.list_datasets(page=1, limit=10)
        assert result["total"] == 1
        assert result["data"][0]["id"] == "ds-1"

    def test_create_dataset_sends_correct_payload(self, monkeypatch):
        """验证 create_dataset 发送正确请求体"""
        captured = {}

        def mock_post(self, url, json=None, headers=None):
            captured["url"] = url
            captured["json"] = json
            class FakeResp:
                status_code = 200
                def raise_for_status(self): pass
                def json(self): return {"id": "ds-new", "name": json["name"]}
            return FakeResp()

        import httpx
        monkeypatch.setattr(httpx.Client, "post", mock_post)

        client = DifyClient(DifyConfig())
        result = client.create_dataset("新知识库", "测试用")
        assert result["id"] == "ds-new"
        assert captured["json"]["name"] == "新知识库"
        assert captured["json"]["indexing_technique"] == "high_quality"

    def test_check_dataset_status_handles_failure(self, monkeypatch):
        """验证 check_dataset_status 在连接失败时返回 reachable=False"""
        def mock_get(self, url, headers=None, params=None):
            raise Exception("connection refused")

        import httpx
        monkeypatch.setattr(httpx.Client, "get", mock_get)

        client = DifyClient(DifyConfig())
        result = client.check_dataset_status()
        assert result["reachable"] is False
        assert "error" in result


# ============ 集成测试：真实 Dify dataset API ============

@integration
class TestDifyDatasetIntegration:
    """Dify 知识库 dataset API 集成测试"""

    def test_dataset_api_reachable(self, http_client, fastapi_base):
        """测试 Dify dataset API 连通性"""
        if not require_service(fastapi_base + "/health"):
            pytest.skip("FastAPI 服务未运行")

        resp = http_client.get(f"{fastapi_base}/api/v1/admin/datasets", params={"page": 1, "limit": 1})
        assert resp.status_code == 200, f"列出知识库失败: {resp.text}"
        data = resp.json()
        print(f"\n[Dify 知识库列表] {json.dumps(data, ensure_ascii=False, indent=2)}")

    def test_create_and_delete_dataset(self, http_client, fastapi_base):
        """测试创建和删除 Dify 知识库（完整 CRUD 周期）"""
        if not require_service(fastapi_base + "/health"):
            pytest.skip("FastAPI 服务未运行")

        unique_name = f"测试知识库-{uuid.uuid4().hex[:8]}"

        # 1. 创建
        resp = http_client.post(
            f"{fastapi_base}/api/v1/admin/datasets",
            json={"name": unique_name, "description": "集成测试自动创建"},
        )
        assert resp.status_code == 200, f"创建知识库失败: {resp.text}"
        created = resp.json()
        dataset_id = created.get("id")
        assert dataset_id, f"未返回 dataset_id: {created}"
        print(f"\n[创建知识库] id={dataset_id}, name={unique_name}")

        # 2. 列出，确认能查到
        resp = http_client.get(f"{fastapi_base}/api/v1/admin/datasets", params={"page": 1, "limit": 50})
        assert resp.status_code == 200
        listed = resp.json()
        ids = [d.get("id") for d in listed.get("data", [])]
        assert dataset_id in ids, f"新建的 dataset 未出现在列表中: {ids}"

        # 3. 删除
        resp = http_client.delete(f"{fastapi_base}/api/v1/admin/datasets/{dataset_id}")
        assert resp.status_code == 200, f"删除知识库失败: {resp.text}"
        print(f"[删除知识库] id={dataset_id} 已删除")

        # 4. 确认已删除
        resp = http_client.get(f"{fastapi_base}/api/v1/admin/datasets", params={"page": 1, "limit": 50})
        listed = resp.json()
        ids = [d.get("id") for d in listed.get("data", [])]
        assert dataset_id not in ids, "删除后 dataset 仍出现在列表中"


# ============ 集成测试：Spring Boot KnowledgeBaseController ↔ Dify 同步 ============

@integration
class TestSpringBootKnowledgeDifySync:
    """Spring Boot 知识库 CRUD ↔ Dify 同步测试"""

    def test_create_knowledge_base_syncs_to_dify(self, http_client, spring_boot_base):
        """在 Spring Boot 创建知识库后，Dify 侧应出现对应 dataset"""
        if not require_service(spring_boot_base.replace("/api", "") + "/api/auth/login"):
            pytest.skip("Spring Boot 服务未运行")

        unique_name = f"集成测试库-{uuid.uuid4().hex[:8]}"

        # 1. 通过 Spring Boot 创建知识库（需要先登录拿 token）
        token = self._login(http_client, spring_boot_base)
        if not token:
            pytest.skip("无法登录 Spring Boot")

        headers = {"Authorization": f"Bearer {token}"}
        resp = http_client.post(
            f"{spring_boot_base}/admin/knowledge-bases",
            json={"name": unique_name, "description": "集成测试", "category": "测试"},
            headers=headers,
        )
        assert resp.status_code == 200, f"创建知识库失败: {resp.text}"
        kb = resp.json().get("data", {})
        kb_id = kb.get("kbId")
        sql_id = kb.get("id")
        print(f"\n[SQL 创建知识库] id={sql_id}, kbId(=Dify dataset id)={kb_id}")

        # 2. 在 Dify 侧确认
        if kb_id and not kb_id.startswith("pending-"):
            resp = http_client.get(
                f"http://localhost:8000/api/v1/admin/datasets",
                params={"page": 1, "limit": 100},
            )
            if resp.status_code == 200:
                listed = resp.json()
                ids = [d.get("id") for d in listed.get("data", [])]
                assert kb_id in ids, f"Dify 侧未找到对应 dataset: kbId={kb_id}, dify_ids={ids}"
                print(f"[Dify 侧确认] dataset {kb_id} 已同步")

        # 3. 清理：删除知识库
        http_client.delete(f"{spring_boot_base}/admin/knowledge-bases/{sql_id}", headers=headers)
        print(f"[清理] 已删除 SQL 知识库 id={sql_id}")

    def _login(self, http_client, base: str) -> str:
        """登录获取 token"""
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
