from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum


class DisasterType(str, Enum):
    EARTHQUAKE = "earthquake"
    FLOOD = "flood"
    TYPHOON = "typhoon"
    DROUGHT = "drought"
    LANDSLIDE = "landslide"
    FOREST_FIRE = "forest_fire"
    STORM = "storm"
    OTHER = "other"


class SeverityLevel(str, Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class DisasterEvent(BaseModel):
    id: str = Field(description="事件唯一标识")
    disaster_type: DisasterType = Field(description="灾害类型")
    title: str = Field(description="事件标题")
    description: Optional[str] = Field(None, description="事件描述")
    location: str = Field(description="发生地点")
    latitude: Optional[float] = Field(None, description="纬度")
    longitude: Optional[float] = Field(None, description="经度")
    severity: SeverityLevel = Field(description="严重程度")
    occurred_at: datetime = Field(description="发生时间")
    source: str = Field(description="数据来源")
    source_url: Optional[str] = Field(None, description="来源链接")
    affected_people: Optional[int] = Field(None, description="受影响人数")
    casualties: Optional[int] = Field(None, description="伤亡人数")
    economic_loss: Optional[float] = Field(None, description="经济损失（万元）")
    raw_data: Optional[dict] = Field(None, description="原始数据")

    class Config:
        from_attributes = True


class CrawlResult(BaseModel):
    source: str
    total_count: int = 0
    new_count: int = 0
    events: List[DisasterEvent] = []
    error: Optional[str] = None
    crawled_at: datetime = Field(default_factory=datetime.now)


class SSEMessage(BaseModel):
    event: str = Field(default="message")
    data: dict
    id: Optional[str] = None
    retry: Optional[int] = None
