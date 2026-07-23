from fastapi import APIRouter, HTTPException, Query
from app.graph import graph_repo
from app.schemas import DispatchPlanResponse
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/dispatch", tags=["物资调度"])


@router.get("/optimal-warehouses", summary="接口1：高风险区域最优物资仓库（预防前置调度）")
async def get_optimal_warehouses(risk_level: str = Query("极高", description="风险等级")):
    """
    获取指定风险等级区域的最优物资仓库调配方案。
    综合考虑：物资可用性、路网距离、紧急程度，计算评分排序。
    """
    try:
        result = await graph_repo.get_optimal_warehouses(risk_level)
        return {"risk_level": risk_level, "recommendations": result}
    except Exception as e:
        logger.error(f"查询最优仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/available-teams", summary="接口2：筛选可调度救援队伍")
async def get_available_teams(
    area_name: str = Query(..., description="区域名称"),
    disaster_type: str | None = Query(None, description="灾害类型"),
):
    """
    筛选未被占用、可调度的救援队伍，按距离排序。
    Dify 工作流 HTTP 节点调用此接口。
    """
    try:
        teams = await graph_repo.get_available_teams_by_area(area_name, disaster_type)
        return {"area_name": area_name, "available_teams": teams}
    except Exception as e:
        logger.error(f"查询可用队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/nearby-shelters", summary="接口3：附近避难场所")
async def get_nearby_shelters(area_name: str = Query(..., description="区域名称")):
    """获取受灾点附近、有剩余容量的避难场所"""
    try:
        shelters = await graph_repo.get_nearby_shelters(area_name)
        return {"area_name": area_name, "shelters": shelters}
    except Exception as e:
        logger.error(f"查询避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/plan", response_model=DispatchPlanResponse, summary="综合调度方案（Dify 调用主接口）")
async def get_dispatch_plan(
    area_name: str = Query(..., description="目标区域名称"),
    disaster_type: str = Query(..., description="灾害类型"),
):
    """
    Dify 工作流 HTTP 节点主调用接口。
    一次性返回：物资仓库推荐 + 可用救援队伍 + 附近避难场所
    """
    try:
        plan = await graph_repo.get_dispatch_plan(area_name, disaster_type)
        risk_spots = await graph_repo.list_high_risk_spots()
        spot = next((s for s in risk_spots if s.get("name") == area_name), {})
        plan["risk_level"] = spot.get("risk_level", "中")
        return plan
    except Exception as e:
        logger.error(f"生成调度方案失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/teams/{team_id}/allocate", summary="派发救援队伍（标记已调度）")
async def allocate_team(team_id: str, spot_id: str):
    """标记队伍已派发，防止重复调度"""
    try:
        ok = await graph_repo.allocate_team(team_id, spot_id)
        return {"success": ok}
    except Exception as e:
        logger.error(f"派发队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
