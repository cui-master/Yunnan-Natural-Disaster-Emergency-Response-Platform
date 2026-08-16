"""Dify 管理路由

提供 Dify 工作流与知识库 dataset API 的连通性检查、知识库管理接口：
  GET  /api/v1/admin/dify-status              Dify 全局状态（工作流 + 知识库连通性）
  GET  /api/v1/admin/datasets                 列出 Dify 知识库
  POST /api/v1/admin/datasets                 创建 Dify 知识库
  DELETE /api/v1/admin/datasets/{dataset_id}  删除 Dify 知识库
  POST /api/v1/admin/datasets/{dataset_id}/retrieve  从知识库检索

Spring Boot 的 AiService.checkDifyWorkflowStatus() 会调 /dify-status。
Spring Boot 的 KnowledgeBaseController 在 CRUD 时可选调 /datasets 同步。
"""
from __future__ import annotations

from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException, Path
from loguru import logger
from pydantic import BaseModel, Field

from app.services.dify_client import dify_client

router = APIRouter(prefix="/admin", tags=["Dify 管理 - 工作流与知识库"])


class CreateDatasetReq(BaseModel):
    name: str = Field(..., description="知识库名称")
    description: str = Field("", description="知识库描述")
    index_mode: str = Field("high_quality", description="索引模式: high_quality / economical")
    permission: str = Field("only_me", description="权限: only_me / all_team_members")


class RetrieveReq(BaseModel):
    query: str = Field(..., description="检索查询")
    top_k: int = Field(5, description="返回条数")


@router.get("/dify-status", summary="Dify 工作流与知识库连通性")
async def dify_status() -> Dict[str, Any]:
    """汇总返回 Dify 工作流和知识库 dataset API 的连通状态"""
    workflows = dify_client.check_workflows_status()
    dataset = dify_client.check_dataset_status()
    return {
        "status": "connected" if (
            workflows.get("status") == "connected" and dataset.get("reachable")
        ) else "partial" if (
            workflows.get("status") == "partial" or dataset.get("reachable")
        ) else "disconnected",
        "base_url": dify_client.cfg.BASE_URL,
        "workflows": workflows.get("workflows", {}),
        "dataset": dataset,
    }


@router.get("/datasets", summary="列出 Dify 知识库")
async def list_datasets(page: int = 1, limit: int = 20) -> Dict[str, Any]:
    try:
        return dify_client.list_datasets(page=page, limit=limit)
    except Exception as e:
        logger.error(f"[dify-admin] 列出知识库失败: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/datasets", summary="创建 Dify 知识库")
async def create_dataset(req: CreateDatasetReq) -> Dict[str, Any]:
    try:
        return dify_client.create_dataset(
            name=req.name,
            description=req.description,
            index_mode=req.index_mode,
            permission=req.permission,
        )
    except Exception as e:
        logger.error(f"[dify-admin] 创建知识库失败: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.delete("/datasets/{dataset_id}", summary="删除 Dify 知识库")
async def delete_dataset(dataset_id: str = Path(..., description="Dify 知识库 ID")) -> Dict[str, Any]:
    try:
        ok = dify_client.delete_dataset(dataset_id)
        return {"deleted": ok, "dataset_id": dataset_id}
    except Exception as e:
        logger.error(f"[dify-admin] 删除知识库失败: {e}")
        raise HTTPException(status_code=502, detail=str(e))


@router.post("/datasets/{dataset_id}/retrieve", summary="从知识库检索文档")
async def retrieve(dataset_id: str, req: RetrieveReq) -> Dict[str, Any]:
    try:
        return dify_client.retrieve_from_dataset(dataset_id, req.query, top_k=req.top_k)
    except Exception as e:
        logger.error(f"[dify-admin] 知识库检索失败: {e}")
        raise HTTPException(status_code=502, detail=str(e))
