"""资源管理员 —— 增删改查 Neo4j 资源节点

维护：受灾点位、仓库、物资、救援队伍、避难场所。
关系管理（道路连接/库存/需求）保留在 graph_nodes.py。
"""
from fastapi import APIRouter, HTTPException, Query
from app.graph import graph_repo
from app.schemas import (
    DisasterSpotCreate, DisasterSpotUpdate,
    WarehouseCreate, WarehouseUpdate,
    MaterialCreate, MaterialUpdate,
    RescueTeamCreate, RescueTeamUpdate,
    ShelterCreate, ShelterUpdate,
)
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/resource", tags=["资源管理-增删改查"])


# ════════════════════════════════════════════
# 受灾点位
# ════════════════════════════════════════════

@router.post("/disaster-spots", summary="创建受灾点位")
async def create_disaster_spot(spot: DisasterSpotCreate):
    try:
        return await graph_repo.create_disaster_spot(spot)
    except Exception as e:
        logger.error(f"创建受灾点位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disaster-spots", summary="列出受灾点位")
async def list_disaster_spots(limit: int = Query(100, ge=1, le=500)):
    try:
        return await graph_repo.list_disaster_spots(limit)
    except Exception as e:
        logger.error(f"查询受灾点位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/disaster-spots/{spot_id}", summary="更新受灾点位")
async def update_disaster_spot(spot_id: str, data: DisasterSpotUpdate):
    try:
        result = await graph_repo.update_disaster_spot(spot_id, data.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="受灾点位不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新受灾点位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/disaster-spots/{spot_id}", summary="删除受灾点位")
async def delete_disaster_spot(spot_id: str):
    try:
        ok = await graph_repo.delete_disaster_spot(spot_id)
        if not ok:
            raise HTTPException(status_code=404, detail="受灾点位不存在")
        return {"success": True, "id": spot_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除受灾点位失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 仓库
# ════════════════════════════════════════════

@router.post("/warehouses", summary="创建仓库")
async def create_warehouse(warehouse: WarehouseCreate):
    try:
        return await graph_repo.create_warehouse(warehouse)
    except Exception as e:
        logger.error(f"创建仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/warehouses", summary="列出仓库")
async def list_warehouses(limit: int = Query(100, ge=1, le=500)):
    try:
        return await graph_repo.list_warehouses(limit)
    except Exception as e:
        logger.error(f"查询仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/warehouses/{warehouse_id}", summary="更新仓库")
async def update_warehouse(warehouse_id: str, data: WarehouseUpdate):
    try:
        result = await graph_repo.update_warehouse(warehouse_id, data.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="仓库不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/warehouses/{warehouse_id}", summary="删除仓库")
async def delete_warehouse(warehouse_id: str):
    try:
        ok = await graph_repo.delete_warehouse(warehouse_id)
        if not ok:
            raise HTTPException(status_code=404, detail="仓库不存在")
        return {"success": True, "id": warehouse_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除仓库失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 物资
# ════════════════════════════════════════════

@router.post("/materials", summary="创建物资品类")
async def create_material(material: MaterialCreate):
    try:
        return await graph_repo.create_material(material)
    except Exception as e:
        logger.error(f"创建物资失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/materials", summary="列出物资品类")
async def list_materials(limit: int = Query(100, ge=1, le=500)):
    try:
        return await graph_repo.list_materials(limit)
    except Exception as e:
        logger.error(f"查询物资失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/materials/{material_id}", summary="更新物资品类")
async def update_material(material_id: str, data: MaterialUpdate):
    try:
        result = await graph_repo.update_material(material_id, data.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="物资不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新物资失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/materials/{material_id}", summary="删除物资品类")
async def delete_material(material_id: str):
    try:
        ok = await graph_repo.delete_material(material_id)
        if not ok:
            raise HTTPException(status_code=404, detail="物资不存在")
        return {"success": True, "id": material_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除物资失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 救援队伍
# ════════════════════════════════════════════

@router.post("/rescue-teams", summary="创建救援队伍")
async def create_rescue_team(team: RescueTeamCreate):
    try:
        return await graph_repo.create_rescue_team(team)
    except Exception as e:
        logger.error(f"创建救援队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/rescue-teams", summary="列出救援队伍")
async def list_rescue_teams(limit: int = Query(100, ge=1, le=500)):
    try:
        return await graph_repo.list_rescue_teams(limit)
    except Exception as e:
        logger.error(f"查询救援队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/rescue-teams/{team_id}", summary="更新救援队伍")
async def update_rescue_team(team_id: str, data: RescueTeamUpdate):
    try:
        result = await graph_repo.update_rescue_team(team_id, data.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="救援队伍不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新救援队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/rescue-teams/{team_id}", summary="删除救援队伍")
async def delete_rescue_team(team_id: str):
    try:
        ok = await graph_repo.delete_rescue_team(team_id)
        if not ok:
            raise HTTPException(status_code=404, detail="救援队伍不存在")
        return {"success": True, "id": team_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除救援队伍失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


# ════════════════════════════════════════════
# 避难场所
# ════════════════════════════════════════════

@router.post("/shelters", summary="创建避难场所")
async def create_shelter(shelter: ShelterCreate):
    try:
        return await graph_repo.create_shelter(shelter)
    except Exception as e:
        logger.error(f"创建避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/shelters", summary="列出避难场所")
async def list_shelters(limit: int = Query(100, ge=1, le=500)):
    try:
        return await graph_repo.list_shelters(limit)
    except Exception as e:
        logger.error(f"查询避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.put("/shelters/{shelter_id}", summary="更新避难场所")
async def update_shelter(shelter_id: str, data: ShelterUpdate):
    try:
        result = await graph_repo.update_shelter(shelter_id, data.model_dump(exclude_unset=True))
        if not result:
            raise HTTPException(status_code=404, detail="避难场所不存在")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"更新避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/shelters/{shelter_id}", summary="删除避难场所")
async def delete_shelter(shelter_id: str):
    try:
        ok = await graph_repo.delete_shelter(shelter_id)
        if not ok:
            raise HTTPException(status_code=404, detail="避难场所不存在")
        return {"success": True, "id": shelter_id}
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"删除避难场所失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
