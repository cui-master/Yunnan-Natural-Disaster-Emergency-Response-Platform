from fastapi import APIRouter, HTTPException, Query, BackgroundTasks
from app.pipeline import data_pipeline, pipeline_status
from app.core.logging import logger

router = APIRouter(prefix="/api/v1/pipeline", tags=["数据管线-Pipeline"])


@router.get("/status", summary="获取管线运行状态")
async def get_pipeline_status():
    """获取当前管线状态、最近运行统计、历史记录"""
    return {
        "status": pipeline_status.to_dict(),
        "recent_history": pipeline_status.history[-5:],
    }


@router.post("/run", summary="手动触发完整数据管线")
async def run_pipeline(
    background_tasks: BackgroundTasks,
    trigger_dify: bool = Query(False, description="是否对高风险区域触发Dify方案生成"),
    sync: bool = Query(False, description="是否同步等待执行完成（默认后台异步）"),
):
    """
    手动触发完整数据管线：采集 → 校验 → 融合 → 研判 → Neo4j更新 → (Dify)
    """
    if pipeline_status.current_status == "running":
        raise HTTPException(status_code=400, detail="管线正在运行中，请稍后再试")

    if sync:
        result = await data_pipeline.run_full_pipeline(trigger_dify=trigger_dify)
        return result
    else:
        background_tasks.add_task(data_pipeline.run_full_pipeline, trigger_dify=trigger_dify)
        return {
            "status": "accepted",
            "message": "数据管线已在后台启动，请通过 /status 查看进度",
        }


@router.post("/run/area", summary="对指定区域执行管线")
async def run_pipeline_for_area(
    area_name: str = Query(..., description="区域名称"),
    trigger_dify: bool = Query(False, description="是否触发Dify方案生成"),
):
    """对单个区域执行管线研判"""
    try:
        result = await data_pipeline.run_full_pipeline(
            area_list=[area_name],
            trigger_dify=trigger_dify,
        )
        return result
    except Exception as e:
        logger.error(f"区域管线执行失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/collect/weather", summary="采集气象数据（测试用）")
async def collect_weather(area_name: str = Query("昆明市东川区")):
    from app.pipeline import collector_manager
    data = await collector_manager.collect_by_type("weather", [area_name])
    return {"count": len(data), "data": [d.model_dump() for d in data]}


@router.get("/collect/geology", summary="采集地质数据（测试用）")
async def collect_geology(area_name: str = Query("大理州漾濞县")):
    from app.pipeline import collector_manager
    data = await collector_manager.collect_by_type("geology", [area_name])
    return {"count": len(data), "data": [d.model_dump() for d in data]}


@router.get("/assess/area", summary="单区域风险研判（测试用）")
async def assess_area(area_name: str = Query("昆明市东川区")):
    """直接对指定区域做风险研判（走完整管线但只返回研判结果）"""
    from app.pipeline import collector_manager, data_validator, fusion_engine, risk_model

    raw = await collector_manager.collect_all([area_name])
    validated = data_validator.validate_all(
        raw.get("weather", []),
        raw.get("geology", []),
        raw.get("hydrology", []),
        raw.get("public_opinion", []),
    )
    features = fusion_engine.fuse_area_data(
        area_name,
        validated.get("weather", []),
        validated.get("geology", []),
        validated.get("hydrology", []),
        validated.get("public_opinion", []),
    )
    results = risk_model.assess_area(features)
    return {
        "area_name": area_name,
        "features": features,
        "risk_results": [r.model_dump() for r in results],
    }
