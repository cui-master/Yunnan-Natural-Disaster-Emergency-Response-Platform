"""Dify HTTP 客户端

封装 Dify 平台调用：
  1. Workflow 工作流（事件抽取、预案检索/方案审查）—— streaming / blocking 两种模式
  2. Knowledge Base 知识库 dataset API —— 创建/列出/删除知识库、上传文档、检索

Dify API 文档：
  - Workflow: POST {base}/v1/workflows/run
  - Chat:     POST {base}/v1/chat-messages
  - Dataset:  POST {base}/v1/datasets
  - Retrieve: POST {base}/v1/datasets/{dataset_id}/retrieve

环境变量（参见 .env）：
  DIFY_BASE_URL          Dify 服务地址（如 http://localhost:8080）
  DIFY_API_KEY_WORKFLOW  Workflow App API Key（app-xxx）
  DIFY_API_KEY_DATASET   知识库 API Key（dataset-xxx）
  DIFY_WORKFLOW_EXTRACT  事件抽取工作流 ID
  DIFY_WORKFLOW_RETRIEVE 预案检索工作流 ID
  DIFY_WORKFLOW_REVIEW   方案审查工作流 ID
"""
from __future__ import annotations

import os
import time
from typing import Any, Dict, Optional

import httpx
from loguru import logger


# ============ 重试机制 ============

MAX_RETRIES = 3
RETRY_DELAYS = [1, 2, 4]  # 指数退避：1s, 2s, 4s
RETRYABLE_STATUS = {500, 502, 503, 504}  # 可重试的 HTTP 状态码


def _should_retry(exc: Exception) -> bool:
    """判断异常是否可重试"""
    if isinstance(exc, httpx.HTTPStatusError):
        return exc.response.status_code in RETRYABLE_STATUS
    if isinstance(exc, (httpx.ConnectError, httpx.ReadTimeout, httpx.ConnectTimeout)):
        return True
    return False


def _retry_sync(fn, *args, **kwargs):
    """同步重试包装"""
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES and _should_retry(e):
                delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                logger.warning(f"[dify-retry] 第 {attempt + 1} 次失败，{delay}s 后重试: {e}")
                time.sleep(delay)
            else:
                raise
    raise last_exc


async def _retry_async(fn, *args, **kwargs):
    """异步重试包装"""
    import asyncio
    last_exc = None
    for attempt in range(MAX_RETRIES + 1):
        try:
            return await fn(*args, **kwargs)
        except Exception as e:
            last_exc = e
            if attempt < MAX_RETRIES and _should_retry(e):
                delay = RETRY_DELAYS[attempt] if attempt < len(RETRY_DELAYS) else RETRY_DELAYS[-1]
                logger.warning(f"[dify-retry] 第 {attempt + 1} 次失败，{delay}s 后重试: {e}")
                await asyncio.sleep(delay)
            else:
                raise
    raise last_exc


class DifyConfig:
    """Dify 配置（从环境变量读取）"""

    BASE_URL: str = os.getenv("DIFY_BASE_URL", "http://localhost:8080")
    API_KEY_WORKFLOW: str = os.getenv("DIFY_API_KEY_WORKFLOW", "")
    API_KEY_DATASET: str = os.getenv("DIFY_API_KEY_DATASET", "")
    WORKFLOW_EXTRACT: str = os.getenv("DIFY_WORKFLOW_EXTRACT", "natural-disaster-extract")
    WORKFLOW_RETRIEVE: str = os.getenv("DIFY_WORKFLOW_RETRIEVE", "natural-disaster-retrieve")
    WORKFLOW_REVIEW: str = os.getenv("DIFY_WORKFLOW_REVIEW", "natural-disaster-review")
    TIMEOUT: float = float(os.getenv("DIFY_TIMEOUT", "60"))


class DifyClient:
    """Dify HTTP 客户端（同步 + 异步）"""

    def __init__(self, cfg: Optional[DifyConfig] = None) -> None:
        self.cfg = cfg or DifyConfig()

    # ---------- Workflow 工作流 ----------

    def run_workflow(self, workflow_key: str, inputs: Dict[str, Any], user: str = "system",
                     response_mode: str = "blocking") -> Dict[str, Any]:
        """调用 Workflow 工作流（blocking 模式同步返回结果，带重试）

        Args:
            workflow_key: workflow 标识（extract / retrieve / review）
            inputs: 工作流输入参数
            user: 终端用户标识
            response_mode: blocking | streaming
        Returns:
            Dify 返回的 JSON 响应
        """

        def _do():
            url = f"{self.cfg.BASE_URL}/v1/workflows/run"
            api_key = self._workflow_api_key(workflow_key)
            payload = {"inputs": inputs, "response_mode": response_mode, "user": user}
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            logger.info(f"[dify] 调用工作流 {workflow_key}: inputs={list(inputs.keys())}")
            with httpx.Client(timeout=self.cfg.TIMEOUT) as client:
                resp = client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                data = resp.json()
                logger.info(f"[dify] 工作流 {workflow_key} 调用成功: task_id={data.get('task_id')}")
                return data

        return _retry_sync(_do)

    async def run_workflow_async(self, workflow_key: str, inputs: Dict[str, Any],
                                 user: str = "system") -> Dict[str, Any]:
        """异步调用 Workflow 工作流（带重试）"""

        async def _do():
            url = f"{self.cfg.BASE_URL}/v1/workflows/run"
            api_key = self._workflow_api_key(workflow_key)
            payload = {"inputs": inputs, "response_mode": "blocking", "user": user}
            headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
            logger.info(f"[dify] 异步调用工作流 {workflow_key}")
            async with httpx.AsyncClient(timeout=self.cfg.TIMEOUT) as client:
                resp = await client.post(url, json=payload, headers=headers)
                resp.raise_for_status()
                return resp.json()

        return await _retry_async(_do)

    def _workflow_api_key(self, workflow_key: str) -> str:
        """根据 workflow_key 选择 API Key（当前三个工作流共用一个 App Key，可扩展）"""
        if workflow_key not in ("extract", "retrieve", "review"):
            raise ValueError(f"未知的工作流标识: {workflow_key}（应为 extract/retrieve/review）")
        return self.cfg.API_KEY_WORKFLOW

    # ---------- SSE 流式进度 ----------

    async def run_workflow_streaming(self, workflow_key: str, inputs: Dict[str, Any],
                                      user: str = "system", sse_manager=None,
                                      task_id: str = "") -> Dict[str, Any]:
        """流式调用 Workflow 工作流，逐行读取 Dify SSE 事件并通过 sse_manager 推送进度

        Dify streaming 事件类型：
          - workflow_started: 工作流开始
          - node_started: 节点开始执行
          - node_finished: 节点执行完成
          - workflow_finished: 工作流完成
          - error: 错误

        Args:
            workflow_key: workflow 标识
            inputs: 工作流输入参数
            user: 终端用户标识
            sse_manager: SSE 推送管理器（app.services.sse_manager.SseManager 实例）
            task_id: 前端订阅的 SSE 任务 ID
        Returns:
            最终 workflow_finished 事件中的 data
        """
        url = f"{self.cfg.BASE_URL}/v1/workflows/run"
        api_key = self._workflow_api_key(workflow_key)
        payload = {"inputs": inputs, "response_mode": "streaming", "user": user}
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        logger.info(f"[dify-stream] 流式调用工作流 {workflow_key}, task_id={task_id}")

        final_data = {}
        try:
            async with httpx.AsyncClient(timeout=self.cfg.TIMEOUT) as client:
                async with client.stream("POST", url, json=payload, headers=headers) as resp:
                    resp.raise_for_status()
                    async for line in resp.aiter_lines():
                        if not line.startswith("data:"):
                            continue
                        data_str = line[5:].strip()
                        if not data_str:
                            continue
                        try:
                            import json
                            event = json.loads(data_str)
                        except Exception:
                            continue

                        event_type = event.get("event", "")
                        event_data = event.get("data", {})

                        # 构建进度消息
                        progress = {
                            "workflow": workflow_key,
                            "event": event_type,
                            "task_id": event_data.get("task_id", task_id),
                        }

                        if event_type == "workflow_started":
                            progress["stage"] = "started"
                            progress["progress"] = 0
                        elif event_type == "node_started":
                            progress["stage"] = "running"
                            progress["node"] = event_data.get("title", event_data.get("node_id", ""))
                            progress["progress"] = event_data.get("progress", 50)
                        elif event_type == "node_finished":
                            progress["stage"] = "running"
                            progress["node"] = event_data.get("title", "")
                            progress["progress"] = event_data.get("progress", 75)
                        elif event_type == "workflow_finished":
                            progress["stage"] = "completed"
                            progress["progress"] = 100
                            final_data = event_data
                        elif event_type == "error":
                            progress["stage"] = "error"
                            progress["error"] = event.get("message", "未知错误")

                        # 推送进度
                        if sse_manager and task_id:
                            try:
                                sse_manager.broadcast(task_id, progress)
                            except Exception as e:
                                logger.debug(f"[dify-stream] SSE 广播失败: {e}")

                        if event_type in ("workflow_finished", "error"):
                            break

        except Exception as e:
            logger.error(f"[dify-stream] 流式工作流 {workflow_key} 异常: {e}")
            if sse_manager and task_id:
                try:
                    sse_manager.broadcast(task_id, {"stage": "error", "error": str(e)})
                except Exception:
                    pass
            raise

        return final_data

    # ---------- 健康检查 ----------

    def check_workflows_status(self) -> Dict[str, Any]:
        """检查 Dify 工作流连通性（用最小输入试调一次 extract 工作流）"""
        result: Dict[str, Any] = {
            "base_url": self.cfg.BASE_URL,
            "workflows": {},
        }
        for key, name in [
            ("extract", "事件抽取"),
            ("retrieve", "预案检索"),
            ("review", "方案审查"),
        ]:
            try:
                # 用空输入 ping 一下，只要返回 200 或 4xx（参数错误也算连通）就算连通
                url = f"{self.cfg.BASE_URL}/v1/workflows/run"
                headers = {
                    "Authorization": f"Bearer {self._workflow_api_key(key)}",
                    "Content-Type": "application/json",
                }
                payload = {"inputs": {}, "response_mode": "blocking", "user": "health-check"}
                with httpx.Client(timeout=10) as client:
                    resp = client.post(url, json=payload, headers=headers)
                # 200/400/422 说明 Dify 服务可达；500 说明可达但不健康
                reachable = resp.status_code in (200, 400, 422)
                healthy = resp.status_code == 200
                result["workflows"][key] = {
                    "name": name,
                    "reachable": reachable or resp.status_code == 500,
                    "healthy": healthy,
                    "http_status": resp.status_code,
                }
            except Exception as e:
                result["workflows"][key] = {
                    "name": name,
                    "reachable": False,
                    "error": str(e)[:200],
                }
        result["status"] = "connected" if all(
            w.get("reachable") for w in result["workflows"].values()
        ) else "partial"
        return result

    # ---------- 知识库 Dataset API ----------

    def list_datasets(self, page: int = 1, limit: int = 20) -> Dict[str, Any]:
        """列出 Dify 上的所有知识库"""
        url = f"{self.cfg.BASE_URL}/v1/datasets"
        headers = {"Authorization": f"Bearer {self.cfg.API_KEY_DATASET}"}
        params = {"page": page, "limit": limit}
        with httpx.Client(timeout=self.cfg.TIMEOUT) as client:
            resp = client.get(url, headers=headers, params=params)
            resp.raise_for_status()
            return resp.json()

    def create_dataset(self, name: str, description: str = "", index_mode: str = "high_quality",
                       permission: str = "only_me") -> Dict[str, Any]:
        """创建 Dify 知识库"""
        url = f"{self.cfg.BASE_URL}/v1/datasets"
        headers = {"Authorization": f"Bearer {self.cfg.API_KEY_DATASET}",
                   "Content-Type": "application/json"}
        payload = {
            "name": name,
            "description": description,
            "indexing_technique": index_mode,
            "permission": permission,
        }
        with httpx.Client(timeout=self.cfg.TIMEOUT) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def delete_dataset(self, dataset_id: str) -> bool:
        """删除 Dify 知识库"""
        url = f"{self.cfg.BASE_URL}/v1/datasets/{dataset_id}"
        headers = {"Authorization": f"Bearer {self.cfg.API_KEY_DATASET}"}
        with httpx.Client(timeout=self.cfg.TIMEOUT) as client:
            resp = client.delete(url, headers=headers)
            return resp.status_code in (200, 204)

    def retrieve_from_dataset(self, dataset_id: str, query: str, top_k: int = 5) -> Dict[str, Any]:
        """从指定知识库检索相关文档片段"""
        url = f"{self.cfg.BASE_URL}/v1/datasets/{dataset_id}/retrieve"
        headers = {"Authorization": f"Bearer {self.cfg.API_KEY_DATASET}",
                   "Content-Type": "application/json"}
        payload = {
            "query": query,
            "retrieval_model": {
                "search_method": "semantic_search",
                "top_k": top_k,
                "score_threshold": 0.5,
            },
        }
        with httpx.Client(timeout=self.cfg.TIMEOUT) as client:
            resp = client.post(url, json=payload, headers=headers)
            resp.raise_for_status()
            return resp.json()

    def check_dataset_status(self) -> Dict[str, Any]:
        """检查知识库 dataset API 连通性"""
        try:
            data = self.list_datasets(page=1, limit=1)
            return {
                "reachable": True,
                "datasets_count": len(data.get("data", [])) if isinstance(data, dict) else 0,
                "raw": data,
            }
        except Exception as e:
            return {
                "reachable": False,
                "error": str(e)[:200],
            }


# 单例
dify_client = DifyClient()
