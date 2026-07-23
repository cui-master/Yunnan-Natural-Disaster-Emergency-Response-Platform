import httpx
from typing import Optional, Dict, List
from app.core.config import settings
from app.core.logging import logger


class DifyDatasetService:
    """Dify 知识库（Dataset）服务

    封装 Dify Dataset API，提供：
    - 文件上传到指定知识库
    - 查询知识库文档列表
    - 删除指定文档
    """

    def __init__(self):
        self.base_url = settings.DIFY_DATASET_BASE_URL.rstrip("/")
        self.api_key = settings.DIFY_DATASET_API_KEY
        self.kb_map = settings.KB_MAP
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
        }

    def validate_kb_name(self, kb_name: str) -> str:
        """校验知识库名称，返回 dataset_id"""
        if kb_name not in self.kb_map:
            valid_names = "、".join(self.kb_map.keys())
            raise ValueError(f"知识库名称错误，仅支持：{valid_names}")
        return self.kb_map[kb_name]

    async def upload_file(
        self,
        kb_name: str,
        filename: str,
        file_bytes: bytes,
        indexing_technique: str = "high_quality",
        process_rule: Optional[dict] = None,
    ) -> dict:
        """上传文件到指定知识库

        Args:
            kb_name: 知识库名称（优化调度 / 风险评估）
            filename: 文件名
            file_bytes: 文件二进制内容
            indexing_technique: 索引方式（high_quality / economy）
            process_rule: 处理规则

        Returns:
            Dify API 返回的文档信息
        """
        dataset_id = self.validate_kb_name(kb_name)

        if process_rule is None:
            process_rule = {"mode": "automatic"}

        url = f"{self.base_url}/v1/datasets/{dataset_id}/document/create-by-file"

        files = {
            "file": (filename, file_bytes),
        }
        data = {
            "indexing_technique": indexing_technique,
            "process_rule": str(process_rule).replace("'", '"'),
        }

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    url,
                    headers=self.headers,
                    files=files,
                    data=data,
                )

                if resp.status_code not in (200, 201):
                    logger.error(
                        f"Dify知识库上传失败: status={resp.status_code}, "
                        f"body={resp.text[:500]}"
                    )
                    raise RuntimeError(
                        f"Dify API 错误 ({resp.status_code}): {resp.text[:200]}"
                    )

                result = resp.json()
                logger.info(
                    f"文件 {filename} 成功上传至【{kb_name}】知识库, "
                    f"document_id={result.get('document', {}).get('id', 'N/A')}"
                )
                return result

        except httpx.RequestError as e:
            logger.error(f"Dify知识库上传请求异常: {e}")
            raise RuntimeError(f"Dify服务连接失败: {str(e)}") from e

    async def list_documents(
        self,
        kb_name: str,
        page: int = 1,
        limit: int = 20,
        keyword: Optional[str] = None,
    ) -> dict:
        """查询知识库内的文档列表

        Args:
            kb_name: 知识库名称
            page: 页码
            limit: 每页数量
            keyword: 搜索关键词

        Returns:
            文档列表数据
        """
        dataset_id = self.validate_kb_name(kb_name)

        url = f"{self.base_url}/v1/datasets/{dataset_id}/documents"
        params = {
            "page": page,
            "limit": limit,
        }
        if keyword:
            params["keyword"] = keyword

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.get(
                    url,
                    headers=self.headers,
                    params=params,
                )
                resp.raise_for_status()
                return resp.json()

        except httpx.RequestError as e:
            logger.error(f"查询文档列表失败: {e}")
            raise RuntimeError(f"Dify服务连接失败: {str(e)}") from e

    async def delete_document(
        self,
        kb_name: str,
        document_id: str,
    ) -> bool:
        """删除知识库中的指定文档

        Args:
            kb_name: 知识库名称
            document_id: 文档 ID

        Returns:
            是否删除成功
        """
        dataset_id = self.validate_kb_name(kb_name)

        url = f"{self.base_url}/v1/datasets/{dataset_id}/documents/{document_id}"

        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                resp = await client.delete(
                    url,
                    headers=self.headers,
                )

                if resp.status_code not in (200, 204):
                    logger.error(
                        f"删除文档失败: status={resp.status_code}, "
                        f"body={resp.text[:200]}"
                    )
                    return False

                logger.info(f"文档 {document_id} 已从【{kb_name}】知识库删除")
                return True

        except httpx.RequestError as e:
            logger.error(f"删除文档请求异常: {e}")
            raise RuntimeError(f"Dify服务连接失败: {str(e)}") from e

    async def get_document_status(
        self,
        kb_name: str,
        document_id: str,
    ) -> dict:
        """获取文档解析状态（通过列表查询匹配）

        Args:
            kb_name: 知识库名称
            document_id: 文档 ID

        Returns:
            文档状态信息
        """
        result = await self.list_documents(kb_name, page=1, limit=100)
        documents = result.get("data", [])
        for doc in documents:
            if doc.get("id") == document_id:
                return doc
        return {}

    async def upload_text(
        self,
        kb_name: str,
        name: str,
        text: str,
        indexing_technique: str = "high_quality",
        process_rule: Optional[dict] = None,
    ) -> dict:
        """通过文本方式创建文档（用于程序化写入）

        Args:
            kb_name: 知识库名称
            name: 文档名称
            text: 文档内容
            indexing_technique: 索引方式
            process_rule: 处理规则

        Returns:
            Dify API 返回结果
        """
        dataset_id = self.validate_kb_name(kb_name)

        if process_rule is None:
            process_rule = {"mode": "automatic"}

        url = f"{self.base_url}/v1/datasets/{dataset_id}/document/create-by-text"

        payload = {
            "name": name,
            "text": text,
            "indexing_technique": indexing_technique,
            "process_rule": process_rule,
        }

        headers = {**self.headers, "Content-Type": "application/json"}

        try:
            async with httpx.AsyncClient(timeout=120.0) as client:
                resp = await client.post(
                    url,
                    headers=headers,
                    json=payload,
                )

                if resp.status_code not in (200, 201):
                    logger.error(
                        f"创建文本文档失败: status={resp.status_code}, "
                        f"body={resp.text[:500]}"
                    )
                    raise RuntimeError(
                        f"Dify API 错误 ({resp.status_code}): {resp.text[:200]}"
                    )

                result = resp.json()
                logger.info(f"文本文档 {name} 已创建至【{kb_name}】知识库")
                return result

        except httpx.RequestError as e:
            logger.error(f"创建文本文档请求异常: {e}")
            raise RuntimeError(f"Dify服务连接失败: {str(e)}") from e

    def list_kb_names(self) -> List[str]:
        """获取所有可用知识库名称"""
        return list(self.kb_map.keys())


dify_dataset_service = DifyDatasetService()
