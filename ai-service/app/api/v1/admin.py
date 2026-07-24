"""系统管理员 —— 模型配置 + 数据源管理

职责：
1. 模型配置管理（查询/动态修改 LLM provider，控制 Dify 失败后的降级行为）
2. 数据源状态查询（Neo4j / Dify 连通性）
3. 知识库管理（已在 knowledge_base.py 实现，不重复）
"""
import httpx
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, Field
from typing import Optional
from app.agents.llm_client import llm_client
from app.core.config import settings
from app.core.neo4j_client import neo4j_manager
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/admin", tags=["系统管理-模型与数据源"])


# ════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════

class LLMConfigUpdate(BaseModel):
    """LLM 配置更新请求"""
    provider: Optional[str] = Field(None, description="LLM provider: deepseek / qwen")
    api_key: Optional[str] = Field(None, description="API Key")
    api_base: Optional[str] = Field(None, description="API Base URL")
    model: Optional[str] = Field(None, description="模型名称")


# ════════════════════════════════════════════
# 模型配置管理
# ════════════════════════════════════════════

@router.get("/llm/config", summary="查询当前 LLM 配置")
async def get_llm_config():
    """
    查询当前 LLM 降级配置（api_key 脱敏）。
    该配置控制 Dify 工作流失败后使用的 LLM（deepseek / qwen）。
    """
    config = llm_client.get_config()
    return {
        "success": True,
        "config": config,
        "supported_providers": ["deepseek", "qwen"],
        "description": "此配置控制 Dify 失败后的 LLM 降级行为",
    }


@router.put("/llm/config", summary="动态修改 LLM 配置")
async def update_llm_config(req: LLMConfigUpdate):
    """
    动态修改 LLM 配置，即时生效。

    - 修改 provider：切换 deepseek / qwen
    - 修改 api_key/model：更新对应 provider 的配置
    - 下次 Dify 失败降级时使用新配置
    """
    try:
        current = llm_client.get_config()
        target_provider = req.provider or current["provider"]

        if req.provider:
            llm_client.set_provider(req.provider)

        if req.api_key or req.api_base or req.model:
            llm_client.update_config(
                provider=target_provider,
                api_key=req.api_key,
                api_base=req.api_base,
                model=req.model,
            )

        new_config = llm_client.get_config()
        logger.info(f"LLM 配置已更新: provider={new_config['provider']}, model={new_config['model']}")
        return {
            "success": True,
            "message": "LLM 配置已更新，即时生效",
            "config": new_config,
        }
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        logger.error(f"更新 LLM 配置失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/llm/test", summary="测试 LLM 连通性")
async def test_llm():
    """
    测试当前 LLM 配置是否可用（发送一个简单请求）。
    """
    try:
        result = await llm_client.test_connectivity()
        return result
    except Exception as e:
        logger.error(f"LLM 测试失败: {e}")
        return {
            "success": False,
            "error": str(e),
        }


# ════════════════════════════════════════════
# 数据源状态
# ════════════════════════════════════════════

@router.get("/datasources", summary="查询数据源状态")
async def get_datasources_status():
    """
    查询各数据源连通性状态：
    - Neo4j 图数据库
    - Dify 工作流
    - Dify 知识库
    - LLM 降级服务
    """
    statuses = {}

    # Neo4j
    try:
        neo4j_manager.execute_query_sync("RETURN 1 AS ok")
        statuses["neo4j"] = {"status": "connected", "uri": settings.NEO4J_URI}
    except Exception as e:
        statuses["neo4j"] = {"status": "disconnected", "error": str(e)[:100]}

    # Dify 工作流
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{settings.DIFY_BASE_URL}/health")
            statuses["dify_workflow"] = {
                "status": "connected" if resp.status_code < 500 else "error",
                "url": settings.DIFY_BASE_URL,
                "http_code": resp.status_code,
            }
    except Exception as e:
        statuses["dify_workflow"] = {"status": "disconnected", "url": settings.DIFY_BASE_URL, "error": str(e)[:100]}

    # Dify 知识库
    statuses["dify_dataset"] = {
        "status": "configured" if settings.DIFY_DATASET_API_KEY else "not_configured",
        "url": settings.DIFY_DATASET_BASE_URL,
    }

    # LLM 降级
    llm_cfg = llm_client.get_config()
    statuses["llm_fallback"] = {
        "status": "configured" if llm_cfg["api_key_masked"] != "***" else "not_configured",
        "provider": llm_cfg["provider"],
        "model": llm_cfg["model"],
    }

    return {
        "success": True,
        "datasources": statuses,
    }
