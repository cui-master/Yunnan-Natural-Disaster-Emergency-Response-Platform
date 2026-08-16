from fastapi import APIRouter, HTTPException, Query
from app.graph import graph_repo
from app.schemas import (
    DisasterSpotCreate, DisasterSpotResponse,
    WarehouseCreate, WarehouseResponse,
    MaterialCreate, MaterialResponse,
    RescueTeamCreate, RescueTeamResponse,
    ShelterCreate, ShelterResponse,
    DispatchPlanResponse, RiskLevelUpdateRequest,
)
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/graph", tags=["图数据库-节点管理"])


# ==================== 受灾点位 ====================
@router.post("/disaster-spots", response_model=DisasterSpotResponse, summary="创建受灾点位/高风险区域")
async def create_disaster_spot(spot: DisasterSpotCreate):
    try:
        result = await graph_repo.create_disaster_spot(spot)
        return result
    except Exception as e:
        logger.error(f"创建受灾点位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disaster-spots", summary="列出受灾点位/高风险区域")
async def list_disaster_spots(risk_level: str | None = Query(None, description="按风险等级过滤")):
    try:
        return await graph_repo.list_high_risk_spots(risk_level)
    except Exception as e:
        logger.error(f"查询受灾点位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/disaster-spots/risk-level", summary="更新风险等级")
async def update_risk_level(req: RiskLevelUpdateRequest):
    try:
        result = await graph_repo.update_risk_level(
            spot_id=req.spot_id,
            risk_level=req.risk_level,
            urgent_level=req.urgent_level,
            disaster_type=req.disaster_type,
        )
        if not result:
            raise HTTPException(status_code=404, detail="点位不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新风险等级失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 仓库 ====================
@router.post("/warehouses", response_model=WarehouseResponse, summary="创建应急物资仓库")
async def create_warehouse(warehouse: WarehouseCreate):
    try:
        return await graph_repo.create_warehouse(warehouse)
    except Exception as e:
        logger.error(f"创建仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 物资 ====================
@router.post("/materials", response_model=MaterialResponse, summary="创建物资品类")
async def create_material(material: MaterialCreate):
    try:
        return await graph_repo.create_material(material)
    except Exception as e:
        logger.error(f"创建物资失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/warehouses/{warehouse_id}/stock", summary="设置仓库库存")
async def set_stock(warehouse_id: str, material_id: str, stock_num: int, safe_stock: int = 0):
    try:
        ok = await graph_repo.add_stock(warehouse_id, material_id, stock_num, safe_stock)
        return {"success": ok}
    except Exception as e:
        logger.error(f"设置库存失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 救援队伍 ====================
@router.post("/rescue-teams", response_model=RescueTeamResponse, summary="创建救援队伍")
async def create_rescue_team(team: RescueTeamCreate):
    try:
        return await graph_repo.create_rescue_team(team)
    except Exception as e:
        logger.error(f"创建救援队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 避难场所 ====================
@router.post("/shelters", response_model=ShelterResponse, summary="创建避难场所")
async def create_shelter(shelter: ShelterCreate):
    try:
        return await graph_repo.create_shelter(shelter)
    except Exception as e:
        logger.error(f"创建避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 道路连接 ====================
@router.post("/road-connect", summary="建立道路连通关系")
async def add_road_connect(
    from_id: str, to_id: str,
    from_label: str = Query(..., description="起点节点Label"),
    to_label: str = Query(..., description="终点节点Label"),
    distance: float = Query(..., description="距离(km)"),
    blocked: bool = False,
    speed: float = 40.0,
):
    try:
        ok = await graph_repo.add_road_connect(from_id, to_id, from_label, to_label, distance, blocked, speed)
        return {"success": ok}
    except Exception as e:
        logger.error(f"建立道路关系失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/disaster-spots/{spot_id}/need", summary="添加物资需求")
async def add_need(spot_id: str, material_id: str, need_num: int, urgent: int = 3):
    try:
        ok = await graph_repo.add_need(spot_id, material_id, need_num, urgent)
        return {"success": ok}
    except Exception as e:
        logger.error(f"添加需求失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ==================== 图可视化（前端调度看板） ====================
@router.get("/visualization", summary="全图可视化数据（前端调度看板用）")
async def get_graph_visualization(limit: int = Query(500, description="最大节点数")):
    """返回全图节点和关系数据，格式兼容 vis.js Network

    返回：
    - nodes: [{id, label, group, title, properties}]
    - edges: [{from, to, label, title, arrows}]
    - stats: {total_nodes, total_edges, by_label}
    """
    try:
        return await graph_repo.get_full_graph(limit)
    except Exception as e:
        logger.error(f"图可视化查询失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
