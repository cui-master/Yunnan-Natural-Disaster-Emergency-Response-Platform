"""应急指挥人员 —— 审核事件 + 生成处置方案

职责：
1. 审核事件：调用 Dify 风险评估工作流（降级：LLM → 规则引擎）
2. 生成处置方案：查 Neo4j 关联三元组 → 调用 Dify 调度工作流（降级：LLM → 模板）
3. 查灾害点关联图（避难所/仓库/队伍/道路）
"""
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
from app.graph import graph_repo
from app.agents import dify_client
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/commander", tags=["应急指挥-审核与处置"])


# ════════════════════════════════════════════
# 请求模型
# ════════════════════════════════════════════

class ReviewRequest(BaseModel):
    """审核事件请求"""
    area_name: str = Field(..., description="区域名称")
    disaster_type: str = Field(..., description="灾害类型")
    description: str = Field(..., description="灾情描述")
    features: Optional[dict] = Field(None, description="环境特征（降雨/地质/水位等）")


class DispatchPlanRequest(BaseModel):
    """生成处置方案请求"""
    area_name: str = Field(..., description="目标区域名称")
    disaster_type: str = Field(..., description="灾害类型")
    risk_level: str = Field("中", description="风险等级")
    input_risk_info: str = Field(..., description="风险情报摘要")
    vision_text: Optional[str] = Field(None, description="图像识别文本（可选）")


# ════════════════════════════════════════════
# 接口
# ════════════════════════════════════════════

@router.post("/review", summary="审核事件（风险评估）")
async def review_event(req: ReviewRequest):
    """
    应急指挥人员审核灾情事件。

    调用 Dify 风险评估工作流，降级链：
    1. Dify 风险评估工作流
    2. LLM（DeepSeek/千问）风险研判
    3. 规则引擎兜底
    """
    try:
        result = await dify_client.run_risk_assessment(
            area_name=req.area_name,
            disaster_type=req.disaster_type,
            description=req.description,
            features=req.features,
        )
        return {
            "success": True,
            "area_name": req.area_name,
            "disaster_type": req.disaster_type,
            "task_id": result.get("task_id"),
            "status": result.get("status"),
            "fallback_level": result.get("fallback_level", "none"),
            "result": result.get("result"),
        }
    except Exception as e:
        logger.error(f"审核事件失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/dispatch-plan", summary="生成处置方案")
async def generate_dispatch_plan(req: DispatchPlanRequest):
    """
    生成应急处置方案。

    流程：
    1. 查 Neo4j 获取灾害点关联三元组（避难所/仓库/队伍/道路）
    2. 调用 Dify 调度方案工作流
    3. 降级链：Dify → LLM（DeepSeek/千问）→ 模板兜底
    """
    try:
        result = await dify_client.run_workflow(
            area_name=req.area_name,
            disaster_type=req.disaster_type,
            risk_level=req.risk_level,
            input_risk_info=req.input_risk_info,
            vision_text=req.vision_text,
        )
        return {
            "success": True,
            "task_id": result.get("task_id"),
            "status": result.get("status"),
            "fallback_level": result.get("fallback_level", "none"),
            "result": result.get("result"),
        }
    except Exception as e:
        logger.error(f"生成处置方案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disasters/{spot_id}/graph", summary="查灾害点关联三元组")
async def get_disaster_graph(spot_id: str):
    """
    查询灾害点关联的三元组数据：
    - 避难场所（NEED_EVACUATE）
    - 物资仓库（NEED → Material ← HAS_STOCK ← Warehouse）
    - 救援队伍（ALLOCATED）
    - 道路连接（ROAD_CONNECT）
    """
    try:
        graph = await graph_repo.get_disaster_graph(spot_id)
        if not graph:
            raise HTTPException(status_code=404, detail="灾害点不存在或无关联数据")
        return {
            "success": True,
            "spot_id": spot_id,
            "spot": graph.get("spot", {}),
            "relations": graph.get("relations", []),
        }
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询灾害点关联图失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/dispatch-resources", summary="查询调度资源（物资+队伍+避难所）")
async def get_dispatch_resources(
    area_name: str = Query(..., description="区域名称"),
    disaster_type: str = Query(..., description="灾害类型"),
):
    """
    直接查询某区域的调度资源三元组（不经过 Dify）。
    用于前端展示或 Dify HTTP 节点调用。
    """
    try:
        plan = await graph_repo.get_dispatch_plan(area_name, disaster_type)
        return {
            "success": True,
            "area_name": area_name,
            "disaster_type": disaster_type,
            "recommendations": plan.get("recommendations", []),
            "available_teams": plan.get("available_teams", []),
            "shelters": plan.get("shelters", []),
        }
    except Exception as e:
        logger.error(f"查询调度资源失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
