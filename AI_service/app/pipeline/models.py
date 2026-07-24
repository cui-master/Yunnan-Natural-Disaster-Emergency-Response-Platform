<<<<<<< HEAD
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DataSourceType(str, Enum):
    WEATHER = "weather"
    GEOLOGY = "geology"
    HYDROLOGY = "hydrology"
    PUBLIC_OPINION = "public_opinion"


class WeatherData(BaseModel):
    source: str = "weather"
    area_name: str
    data_type: str = "weather"
    temperature: Optional[float] = None
    rainfall_24h: float = Field(0.0, description="24小时降雨量(mm)")
    rainfall_3d: float = Field(0.0, description="3天累计降雨(mm)")
    rainfall_7d: float = Field(0.0, description="7天累计降雨(mm)")
    rainfall_intensity: Optional[str] = Field(None, description="小雨/中雨/大雨/暴雨/大暴雨")
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    warning_level: Optional[str] = Field(None, description="蓝/黄/橙/红")
    forecast_hours: Optional[int] = Field(24, description="预报时效(小时)")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.9, description="数据源可信度 0~1")


class GeologyData(BaseModel):
    source: str = "geology"
    area_name: str
    data_type: str = "geology"
    event_type: Optional[str] = Field(None, description="地震/滑坡/泥石流")
    magnitude: Optional[float] = Field(None, description="震级")
    depth: Optional[float] = Field(None, description="震源深度(km)")
    lng: Optional[float] = None
    lat: Optional[float] = None
    occurrence_time: Optional[datetime] = None
    geological_risk_level: Optional[str] = Field(None, description="地质灾害气象风险等级")
    slope_stability: Optional[float] = Field(None, description="边坡稳定系数")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.95, description="数据源可信度")


class HydrologyData(BaseModel):
    source: str = "hydrology"
    area_name: str
    data_type: str = "hydrology"
    river_name: Optional[str] = None
    water_level: Optional[float] = Field(None, description="水位(m)")
    warning_water_level: Optional[float] = Field(None, description="警戒水位(m)")
    flow_rate: Optional[float] = Field(None, description="流量(m³/s)")
    reservoir_level: Optional[float] = None
    reservoir_storage: Optional[float] = None
    flood_warning: Optional[str] = Field(None, description="水情预警等级")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.85, description="数据源可信度")


class PublicOpinionData(BaseModel):
    source: str = "public_opinion"
    area_name: str
    data_type: str = "public_opinion"
    keyword: Optional[str] = None
    hot_post_count: int = 0
    negative_count: int = 0
    sentiment_score: float = Field(0.5, description="舆情情感分 0负~1正")
    hot_topics: list[str] = Field(default_factory=list)
    first_report_time: Optional[datetime] = None
    spreading_speed: Optional[str] = Field(None, description="传播速度等级")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.6, description="数据源可信度")


class RiskResult(BaseModel):
    area_name: str
    disaster_type: str
    risk_level: str = Field(..., description="低/中/高/极高")
    risk_score: float = Field(0.0, description="风险评分 0~100")
    urgent_level: int = Field(3, ge=1, le=5)
    contributing_factors: dict = Field(default_factory=dict, description="贡献因子明细")
    model_version: str = "v1.0-sim"
    generate_time: datetime = Field(default_factory=datetime.now)
    data_sources: list[str] = Field(default_factory=list)
=======
from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime
from enum import Enum


class DataSourceType(str, Enum):
    WEATHER = "weather"
    GEOLOGY = "geology"
    HYDROLOGY = "hydrology"
    PUBLIC_OPINION = "public_opinion"


class WeatherData(BaseModel):
    source: str = "weather"
    area_name: str
    data_type: str = "weather"
    temperature: Optional[float] = None
    rainfall_24h: float = Field(0.0, description="24小时降雨量(mm)")
    rainfall_3d: float = Field(0.0, description="3天累计降雨(mm)")
    rainfall_7d: float = Field(0.0, description="7天累计降雨(mm)")
    rainfall_intensity: Optional[str] = Field(None, description="小雨/中雨/大雨/暴雨/大暴雨")
    wind_speed: Optional[float] = None
    humidity: Optional[float] = None
    warning_level: Optional[str] = Field(None, description="蓝/黄/橙/红")
    forecast_hours: Optional[int] = Field(24, description="预报时效(小时)")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.9, description="数据源可信度 0~1")


class GeologyData(BaseModel):
    source: str = "geology"
    area_name: str
    data_type: str = "geology"
    event_type: Optional[str] = Field(None, description="地震/滑坡/泥石流")
    magnitude: Optional[float] = Field(None, description="震级")
    depth: Optional[float] = Field(None, description="震源深度(km)")
    lng: Optional[float] = None
    lat: Optional[float] = None
    occurrence_time: Optional[datetime] = None
    geological_risk_level: Optional[str] = Field(None, description="地质灾害气象风险等级")
    slope_stability: Optional[float] = Field(None, description="边坡稳定系数")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.95, description="数据源可信度")


class HydrologyData(BaseModel):
    source: str = "hydrology"
    area_name: str
    data_type: str = "hydrology"
    river_name: Optional[str] = None
    water_level: Optional[float] = Field(None, description="水位(m)")
    warning_water_level: Optional[float] = Field(None, description="警戒水位(m)")
    flow_rate: Optional[float] = Field(None, description="流量(m³/s)")
    reservoir_level: Optional[float] = None
    reservoir_storage: Optional[float] = None
    flood_warning: Optional[str] = Field(None, description="水情预警等级")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.85, description="数据源可信度")


class PublicOpinionData(BaseModel):
    source: str = "public_opinion"
    area_name: str
    data_type: str = "public_opinion"
    keyword: Optional[str] = None
    hot_post_count: int = 0
    negative_count: int = 0
    sentiment_score: float = Field(0.5, description="舆情情感分 0负~1正")
    hot_topics: list[str] = Field(default_factory=list)
    first_report_time: Optional[datetime] = None
    spreading_speed: Optional[str] = Field(None, description="传播速度等级")
    raw_data: Optional[dict] = None
    collect_time: datetime = Field(default_factory=datetime.now)
    reliability: float = Field(0.6, description="数据源可信度")


class RiskResult(BaseModel):
    area_name: str
    disaster_type: str
    risk_level: str = Field(..., description="低/中/高/极高")
    risk_score: float = Field(0.0, description="风险评分 0~100")
    urgent_level: int = Field(3, ge=1, le=5)
    contributing_factors: dict = Field(default_factory=dict, description="贡献因子明细")
    model_version: str = "v1.0-sim"
    generate_time: datetime = Field(default_factory=datetime.now)
    data_sources: list[str] = Field(default_factory=list)
>>>>>>> feature-cui
