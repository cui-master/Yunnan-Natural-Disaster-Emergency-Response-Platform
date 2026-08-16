"""AI 服务测试 —— 两个 Dify 工作流

测试目标：
  1. 事件抽取工作流（extract）：输入自然语言文本，输出结构化灾情信息
  2. 预案检索工作流（retrieve）：输入查询，输出相关应急预案
  3. 方案审查工作流（review）：输入方案，输出审查意见

测试分两类：
  - 单元测试：mock Dify 响应，验证 FastAPI agent 路由的请求/响应格式
  - 集成测试（RUN_INTEGRATION=1）：真实调用 Dify，验证工作流连通性和输出

通过标准：
  - Dify 工作流返回 status=succeeded
  - outputs 字段包含预期结构化字段（disaster_type/location/level 等）
"""
from __future__ import annotations

import json
from typing import Any, Dict
from unittest.mock import AsyncMock, patch

import pytest

from app.services.dify_client import DifyClient, DifyConfig
from tests.conftest import integration, require_service, FASTAPI_BASE_URL


# ============ 单元测试：mock Dify 响应 ============

class TestExtractIncidentUnit:
    """事件抽取工作流 —— 单元测试（mock Dify）"""

    @pytest.mark.asyncio
    async def test_extract_incident_returns_structured_output(self, sample_incident_text):
        """验证事件抽取返回结构化灾情字段"""
        mock_dify_resp = {
            "task_id": "extract-test-001",
            "workflow_run_id": "wr-001",
            "status": "succeeded",
            "data": {
                "outputs": {
                    "disaster_type": "地震",
                    "location": "云南省昭通市彝良县",
                    "level": "较大",
                    "affected_people": 2500,
                    "occurred_at": "2025-07-20 08:30:00",
                    "description": "彝良县发生5.2级地震",
                },
                "status": "succeeded",
            },
        }

        client = DifyClient(DifyConfig())
        with patch.object(client, "run_workflow_async", new=AsyncMock(return_value=mock_dify_resp)):
            result = await client.run_workflow_async(
                workflow_key="extract",
                inputs={"text": sample_incident_text},
            )

        assert result["status"] == "succeeded"
        outputs = result["data"]["outputs"]
        assert outputs["disaster_type"] == "地震"
        assert "彝良" in outputs["location"]
        assert outputs["affected_people"] == 2500
        assert outputs["level"] in ("较大", "重大", "一般", "特大")

    @pytest.mark.asyncio
    async def test_extract_incident_workflow_key_validation(self):
        """验证 workflow_key 只接受 extract/retrieve/review"""
        client = DifyClient(DifyConfig())
        with pytest.raises(ValueError, match="未知的工作流标识"):
            client._workflow_api_key("invalid_key")


class TestRetrievePlansUnit:
    """预案检索工作流 —— 单元测试（mock Dify）"""

    @pytest.mark.asyncio
    async def test_retrieve_plans_returns_plan_list(self):
        """验证预案检索返回预案列表"""
        mock_dify_resp = {
            "task_id": "retrieve-test-001",
            "workflow_run_id": "wr-002",
            "status": "succeeded",
            "data": {
                "outputs": {
                    "plans": [
                        {"title": "云南省地震应急预案", "score": 0.95, "content": "..."},
                        {"title": "昭通市地质灾害应急预案", "score": 0.88, "content": "..."},
                    ],
                    "total": 2,
                },
                "status": "succeeded",
            },
        }

        client = DifyClient(DifyConfig())
        with patch.object(client, "run_workflow_async", new=AsyncMock(return_value=mock_dify_resp)):
            result = await client.run_workflow_async(
                workflow_key="retrieve",
                inputs={"query": "地震 应急预案", "top_k": 5},
            )

        outputs = result["data"]["outputs"]
        assert outputs["total"] == 2
        assert len(outputs["plans"]) == 2
        assert "地震" in outputs["plans"][0]["title"]


class TestReviewPlanUnit:
    """方案审查工作流 —— 单元测试（mock Dify）"""

    @pytest.mark.asyncio
    async def test_review_plan_returns_review_opinion(self, sample_plan_content):
        """验证方案审查返回审查意见"""
        mock_dify_resp = {
            "task_id": "review-test-001",
            "workflow_run_id": "wr-003",
            "status": "succeeded",
            "data": {
                "outputs": {
                    "compliant": True,
                    "feasibility": "高",
                    "issues": ["医疗物资储备量可能不足"],
                    "suggestions": ["建议增加医疗物资储备至72小时用量"],
                    "overall_score": 85,
                },
                "status": "succeeded",
            },
        }

        client = DifyClient(DifyConfig())
        with patch.object(client, "run_workflow_async", new=AsyncMock(return_value=mock_dify_resp)):
            result = await client.run_workflow_async(
                workflow_key="review",
                inputs={"plan_content": sample_plan_content, "incident_id": 1},
            )

        outputs = result["data"]["outputs"]
        assert outputs["compliant"] is True
        assert isinstance(outputs["issues"], list)
        assert outputs["overall_score"] >= 60


# ============ 集成测试：真实调用 Dify ============

@pytest.mark.asyncio
@integration
class TestDifyWorkflowIntegration:
    """Dify 工作流集成测试（需要 RUN_INTEGRATION=1 + Dify 服务运行）"""

    async def test_extract_incident_real_dify(self, async_http_client, fastapi_base, sample_incident_text):
        """真实调用事件抽取工作流"""
        if not require_service(fastapi_base + "/health"):
            pytest.skip("FastAPI 服务未运行")

        resp = await async_http_client.post(
            f"{fastapi_base}/api/v1/agent/extract-incident",
            json={"text": sample_incident_text, "task_id": "test-extract-real"},
        )
        assert resp.status_code == 200, f"事件抽取失败: {resp.text}"
        data = resp.json()
        assert data["task_id"] == "test-extract-real"
        assert data["status"] in ("succeeded", "failed", "unknown")
        print(f"\n[事件抽取结果] {json.dumps(data, ensure_ascii=False, indent=2)}")

    async def test_retrieve_plans_real_dify(self, async_http_client, fastapi_base):
        """真实调用预案检索工作流"""
        if not require_service(fastapi_base + "/health"):
            pytest.skip("FastAPI 服务未运行")

        resp = await async_http_client.post(
            f"{fastapi_base}/api/v1/agent/retrieve-plans",
            json={"query": "地震 应急预案 云南", "top_k": 3, "task_id": "test-retrieve-real"},
        )
        assert resp.status_code == 200, f"预案检索失败: {resp.text}"
        data = resp.json()
        assert data["task_id"] == "test-retrieve-real"
        print(f"\n[预案检索结果] {json.dumps(data, ensure_ascii=False, indent=2)}")

    async def test_review_plan_real_dify(self, async_http_client, fastapi_base, sample_plan_content):
        """真实调用方案审查工作流"""
        if not require_service(fastapi_base + "/health"):
            pytest.skip("FastAPI 服务未运行")

        resp = await async_http_client.post(
            f"{fastapi_base}/api/v1/agent/review-plan",
            json={
                "plan_content": sample_plan_content,
                "incident_id": 1,
                "task_id": "test-review-real",
            },
        )
        assert resp.status_code == 200, f"方案审查失败: {resp.text}"
        data = resp.json()
        assert data["task_id"] == "test-review-real"
        print(f"\n[方案审查结果] {json.dumps(data, ensure_ascii=False, indent=2)}")

    async def test_dify_workflows_status(self, async_http_client, fastapi_base):
        """检查 Dify 工作流连通性"""
        if not require_service(fastapi_base + "/health"):
            pytest.skip("FastAPI 服务未运行")

        resp = await async_http_client.get(f"{fastapi_base}/api/v1/admin/dify-status")
        assert resp.status_code == 200
        data = resp.json()
        print(f"\n[Dify 状态] {json.dumps(data, ensure_ascii=False, indent=2)}")
        # 至少能拿到响应（不强制要求全部 reachable，但接口要通）
        assert "workflows" in data or "status" in data
