from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from app.services import event_store
from app.models.schemas import DisasterEvent

router = APIRouter(prefix="/events", tags=["灾害事件"])


@router.get("", response_model=List[DisasterEvent], summary="获取灾害事件列表")
async def list_events(
    disaster_type: Optional[str] = Query(None, description="灾害类型过滤"),
    severity: Optional[str] = Query(None, description="严重程度过滤"),
    location: Optional[str] = Query(None, description="地点关键词"),
    hours: Optional[int] = Query(None, description="最近N小时内"),
    limit: int = Query(100, ge=1, le=1000, description="返回数量限制"),
):
    """分页查询灾害事件列表"""
    events = await event_store.get_events(
        disaster_type=disaster_type,
        severity=severity,
        location=location,
        limit=limit,
        hours=hours,
    )
    return events


@router.get("/{event_id}", response_model=DisasterEvent, summary="获取事件详情")
async def get_event(event_id: str):
    """根据事件ID获取详细信息"""
    event = await event_store.get_event_by_id(event_id)
    if not event:
        raise HTTPException(status_code=404, detail="事件不存在")
    return event


@router.get("/stats/summary", response_model=dict, summary="获取事件统计")
async def event_stats():
    """获取灾害事件统计信息"""
    return await event_store.get_stats()
