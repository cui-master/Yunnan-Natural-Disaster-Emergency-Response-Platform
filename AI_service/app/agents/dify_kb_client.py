import httpx
from typing import Optional

from app.core.config import settings
from app.core.logging import logger

# 知识库名称 -> Dify dataset_id 映射（来自 .env 配置）
KB_MAP = {
    "优化调度": settings.KB_OPTIMIZE_DISPATCH_ID,
    "风险评估": settings.KB_RISK_ASSESSMENT_ID,
}
SUPPORTED_KB = list(KB_MAP.keys())


class DifyKBClient:
    """Dify 知识库（Dataset）客户端。

    注意：知识库文件上传使用 **Dataset API Key**（`dataset-xxx`），
    与 Dify 工作流的应用密钥（`app-xxx`）不是同一把密钥。
    """

    def __init__(self):
        self.base_url = (settings.DIFY_DATASET_BASE_URL or settings.DIFY_BASE_URL).rstrip("/")
        self.api_key = settings.DIFY_DATASET_API_KEY
        self.headers = {"Authorization": f"Bearer {self.api_key}"}

    def _resolve_dataset_id(self, kb_name: str) -> str:
        ds_id = KB_MAP.get(kb_name)
        if not ds_id:
            raise ValueError(f"未知知识库：{kb_name}，仅支持：{' / '.join(SUPPORTED_KB)}")
        return ds_id

    async def upload_file(
        self,
        kb_name: str,
        filename: str,
        file_bytes: bytes,
        content_type: str = "application/octet-stream",
        indexing_technique: str = "high_quality",
    ) -> dict:
        """上传文件到指定知识库（Dify create-by-file）。"""
        dataset_id = self._resolve_dataset_id(kb_name)
        url = f"{self.base_url}/v1/datasets/{dataset_id}/documents/create-by-file"
        files = {"file": (filename, file_bytes, content_type)}
        data = {
            "indexing_technique": indexing_technique,
            "process_rule": '{"mode":"automatic"}',
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, headers=self.headers, files=files, data=data)
        except httpx.HTTPError as e:
            logger.error(f"Dify 知识库上传请求异常: {e}")
            raise RuntimeError(f"Dify 请求失败: {e}")
        if resp.status_code not in (200, 201):
            logger.error(f"Dify 知识库上传失败 {resp.status_code}: {resp.text}")
            raise RuntimeError(f"Dify 返回 {resp.status_code}: {resp.text}")
        return resp.json()

    async def upload_text(
        self,
        kb_name: str,
        name: str,
        text: str,
        indexing_technique: str = "high_quality",
    ) -> dict:
        """通过纯文本创建文档。"""
        dataset_id = self._resolve_dataset_id(kb_name)
        url = f"{self.base_url}/v1/datasets/{dataset_id}/document/create-by-text"
        payload = {
            "name": name,
            "text": text,
            "indexing_technique": indexing_technique,
            "process_rule": {"mode": "automatic"},
        }
        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(url, headers=self.headers, json=payload)
        except httpx.HTTPError as e:
            logger.error(f"Dify 文本上传请求异常: {e}")
            raise RuntimeError(f"Dify 请求失败: {e}")
        if resp.status_code not in (200, 201):
            logger.error(f"Dify 文本上传失败 {resp.status_code}: {resp.text}")
            raise RuntimeError(f"Dify 返回 {resp.status_code}: {resp.text}")
        return resp.json()

    async def list_documents(
        self, kb_name: str, page: int = 1, limit: int = 20, keyword: Optional[str] = None
    ) -> dict:
        dataset_id = self._resolve_dataset_id(kb_name)
        url = f"{self.base_url}/v1/datasets/{dataset_id}/documents"
        params = {"page": page, "limit": limit}
        if keyword:
            params["keyword"] = keyword
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url, headers=self.headers, params=params)
        except httpx.HTTPError as e:
            raise RuntimeError(f"Dify 请求失败: {e}")
        if resp.status_code != 200:
            raise RuntimeError(f"Dify 返回 {resp.status_code}: {resp.text}")
        return resp.json()

    async def delete_document(self, kb_name: str, document_id: str) -> dict:
        dataset_id = self._resolve_dataset_id(kb_name)
        url = f"{self.base_url}/v1/datasets/{dataset_id}/documents/{document_id}"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.delete(url, headers=self.headers)
        except httpx.HTTPError as e:
            raise RuntimeError(f"Dify 请求失败: {e}")
        if resp.status_code not in (200, 204):
            raise RuntimeError(f"Dify 返回 {resp.status_code}: {resp.text}")
        return resp.json() if resp.content else {"success": True}

    async def document_status(self, kb_name: str, document_id: str) -> dict:
        dataset_id = self._resolve_dataset_id(kb_name)
        url = f"{self.base_url}/v1/datasets/{dataset_id}/documents/{document_id}/indexing-status"
        try:
            async with httpx.AsyncClient(timeout=60.0) as client:
                resp = await client.get(url, headers=self.headers)
        except httpx.HTTPError as e:
            raise RuntimeError(f"Dify 请求失败: {e}")
        if resp.status_code != 200:
            raise RuntimeError(f"Dify 返回 {resp.status_code}: {resp.text}")
        return resp.json()


dify_kb_client = DifyKBClient()
