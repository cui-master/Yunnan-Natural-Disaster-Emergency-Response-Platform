"""AI Agent 路由

对接两个 Dify 工作流 + 一个检索工作流：
  1. POST /api/v1/agent/extract-incident  事件抽取（从自然语言抽取结构化灾情）
  2. POST /api/v1/agent/retrieve-plans     预案检索（从知识库检索应急预案）
  3. POST /api/v1/agent/review-plan        方案审查（对生成方案做合规性审查）

调用链：前端 → Spring Boot /ai/agent/* → FastAPI /api/v1/agent/* → Dify Workflow

Dify 工作流输出统一为 {"task_id", "workflow_run_id", "data": {"outputs": {...}}, "status"}
本路由把 Dify 原始响应包装成 {"task_id", "result", "raw"} 返回。
"""
from __future__ import annotations

import uuid
from typing import Any, Dict, Optional

from fastapi import APIRouter, HTTPException
from loguru import logger
from pydantic import BaseModel, Field

from app.services.dify_client import dify_client

router = APIRouter(prefix="/agent", tags=["AI Agent - Dify 工作流"])


# ============ 请求模型 ============

class ExtractIncidentReq(BaseModel):
    text: str = Field(..., description="原始灾情上报文本")
    task_id: Optional[str] = Field(None, description="可选：前端预先生成的 task_id")


class RetrievePlansReq(BaseModel):
    query: str = Field(..., description="检索查询（灾害类型/关键词）")
    top_k: int = Field(5, description="返回条数")
    task_id: Optional[str] = None


class ReviewPlanReq(BaseModel):
    plan_content: str = Field(..., description="待审查的应急方案内容")
    incident_id: Optional[int] = Field(None, description="关联灾情 ID")
    task_id: Optional[str] = None


class RiskAssessReq(BaseModel):
    incident: Dict[str, Any] = Field(..., description="灾情信息（标题、类型、等级、位置、描述等）")
    task_id: Optional[str] = None


# ============ 工作流调用 ============

def _wrap(task_id: str, dify_resp: Dict[str, Any]) -> Dict[str, Any]:
    """统一包装 Dify 工作流响应"""
    return {
        "task_id": task_id,
        "status": dify_resp.get("status", "unknown"),
        "workflow_run_id": dify_resp.get("workflow_run_id"),
        "result": (dify_resp.get("data") or {}).get("outputs", {}),
        "raw": dify_resp,
    }


@router.post("/extract-incident", summary="事件抽取（Dify 工作流 #1）")
async def extract_incident(req: ExtractIncidentReq) -> Dict[str, Any]:
    """从自然语言文本抽取结构化灾情信息（灾害类型、地点、等级、人数等）"""
    task_id = req.task_id or f"extract-{uuid.uuid4().hex[:12]}"
    logger.info(f"[agent] 事件抽取 task_id={task_id} text_len={len(req.text)}")
    try:
        dify_resp = await dify_client.run_workflow_async(
            workflow_key="extract",
            inputs={"text": req.text, "task_id": task_id},
            user=task_id,
        )
        return _wrap(task_id, dify_resp)
    except Exception as e:
        logger.error(f"[agent] 事件抽取失败 task_id={task_id}: {e}")
        raise HTTPException(status_code=502, detail=f"事件抽取失败: {e}")


@router.post("/retrieve-plans", summary="预案检索（Dify 工作流 #2）")
async def retrieve_plans(req: RetrievePlansReq) -> Dict[str, Any]:
    """从知识库检索相关应急预案"""
    task_id = req.task_id or f"retrieve-{uuid.uuid4().hex[:12]}"
    logger.info(f"[agent] 预案检索 task_id={task_id} query={req.query!r} top_k={req.top_k}")
    try:
        dify_resp = await dify_client.run_workflow_async(
            workflow_key="retrieve",
            inputs={"query": req.query, "top_k": req.top_k, "task_id": task_id},
            user=task_id,
        )
        return _wrap(task_id, dify_resp)
    except Exception as e:
        logger.error(f"[agent] 预案检索失败 task_id={task_id}: {e}")
        raise HTTPException(status_code=502, detail=f"预案检索失败: {e}")


@router.post("/review-plan", summary="方案审查（Dify 工作流 #3）")
async def review_plan(req: ReviewPlanReq) -> Dict[str, Any]:
    """对应急方案进行合规性与可行性审查"""
    task_id = req.task_id or f"review-{uuid.uuid4().hex[:12]}"
    logger.info(f"[agent] 方案审查 task_id={task_id} plan_len={len(req.plan_content)}")
    try:
        dify_resp = await dify_client.run_workflow_async(
            workflow_key="review",
            inputs={
                "plan_content": req.plan_content,
                "incident_id": req.incident_id or 0,
                "task_id": task_id,
            },
            user=task_id,
        )
        return _wrap(task_id, dify_resp)
    except Exception as e:
        logger.error(f"[agent] 方案审查失败 task_id={task_id}: {e}")
        raise HTTPException(status_code=502, detail=f"方案审查失败: {e}")


@router.post("/risk-assess", summary="风险评估（Dify 工作流 #4）")
async def risk_assess(req: RiskAssessReq) -> Dict[str, Any]:
    """对灾情事件进行 AI 风险评估"""
    task_id = req.task_id or f"risk-{uuid.uuid4().hex[:12]}"
    logger.info(f"[agent] 风险评估 task_id={task_id} incident={req.incident}")
    try:
        dify_resp = await dify_client.run_workflow_async(
            workflow_key="review",
            inputs={
                "incident": req.incident,
                "task_id": task_id,
            },
            user=task_id,
        )
        return _wrap(task_id, dify_resp)
    except Exception as e:
        logger.error(f"[agent] 风险评估失败 task_id={task_id}: {e}")
        raise HTTPException(status_code=502, detail=f"风险评估失败: {e}")


@router.get("/health", summary="AI Agent 服务健康检查")
async def health() -> Dict[str, Any]:
    return {"status": "ok", "service": "ai-agent", "dify": dify_client.cfg.BASE_URL}
