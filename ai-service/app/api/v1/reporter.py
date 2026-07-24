"""普通信息员 —— 灾情上报

职责：上报灾情到 Neo4j（DisasterSpot 节点 + 上报扩展字段），
返回完整数据给 SpringBoot 存 SQL。
"""
import uuid
from datetime import datetime
from fastapi import APIRouter, HTTPException, Query
from app.graph import graph_repo
from app.schemas import DisasterSpotCreate
from app.core.logging import logger


def _serialize(node):
    """转换 Neo4j 节点为可 JSON 序列化的 dict

    处理 neo4j.time.DateTime 等特殊类型。
    """
    if not isinstance(node, dict):
        return node
    out = {}
    for k, v in node.items():
        # neo4j.time.DateTime / neo4j.time.Date 等都有 iso_format()
        if hasattr(v, "iso_format") and callable(v.iso_format):
            out[k] = v.iso_format()
        elif isinstance(v, (list, tuple)):
            out[k] = list(v)
        else:
            out[k] = v
    return out


router = APIRouter(prefix="/api/v1/reporter", tags=["普通信息员-灾情上报"])


@router.post("/disasters", summary="上报灾情")
async def report_disaster(spot: DisasterSpotCreate):
    """
    普通信息员上报灾情。

    - 在 Neo4j 创建 DisasterSpot 节点（含上报人、伤亡、受灾人数、现场描述等）
    - 返回完整数据，SpringBoot 可同步存入 SQL

    若未传 id，自动生成。
    """
    try:
        if not spot.id:
            spot.id = f"ds-{uuid.uuid4().hex[:8]}"
        if not spot.report_time:
            spot.report_time = datetime.now()

        result = await graph_repo.create_disaster_spot(spot)
        logger.info(f"灾情上报成功: id={spot.id}, name={spot.name}, reporter={spot.reporter}")

        # 返回完整数据（SpringBoot 存 SQL 用），转换 Neo4j 特殊类型
        return _serialize(result)
    except Exception as e:
        logger.error(f"灾情上报失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disasters", summary="列出灾情事件")
async def list_disasters(
    risk_level: str | None = Query(None, description="按风险等级过滤"),
    limit: int = Query(100, ge=1, le=500),
):
    """查询已上报的灾情事件列表"""
    try:
        spots = await graph_repo.list_high_risk_spots(risk_level)
        return {"total": len(spots), "disasters": [_serialize(s) for s in spots[:limit]]}
    except Exception as e:
        logger.error(f"查询灾情列表失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/disasters/{spot_id}", summary="查询灾情详情")
async def get_disaster(spot_id: str):
    """查询单个灾情事件详情"""
    try:
        node = await graph_repo.get_node("DisasterSpot", spot_id)
        if not node:
            raise HTTPException(status_code=404, detail="灾情事件不存在")
        return _serialize(node)
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"查询灾情详情失败: {e}")
        raise HTTPException(status_code=500, detail=str(e))
