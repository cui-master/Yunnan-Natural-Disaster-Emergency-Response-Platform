from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class DisasterSpotBase(BaseModel):
    name: str = Field(..., description="区域名称")
    disaster_type: list[str] = Field(default_factory=list, description="灾害类型数组")
    risk_level: str = Field("中", description="风险等级：低/中/高/极高")
    urgent_level: int = Field(3, ge=1, le=5, description="紧急等级 1~5")
    lng: Optional[float] = None
    lat: Optional[float] = None
    # 上报扩展字段（保持 snake_case，不新增 Label）
    reporter: Optional[str] = Field(None, description="上报人")
    report_time: Optional[datetime] = Field(None, description="上报时间")
    casualties: Optional[int] = Field(None, description="伤亡人数")
    affected_people: Optional[int] = Field(None, description="受灾人数")
    description: Optional[str] = Field(None, description="现场描述")
    severity: Optional[str] = Field(None, description="严重程度")


class DisasterSpotCreate(DisasterSpotBase):
    id: str


class DisasterSpotResponse(DisasterSpotBase):
    id: str
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


class DisasterSpotUpdate(BaseModel):
    """灾情点位更新（所有字段可选）"""
    name: Optional[str] = None
    disaster_type: Optional[list[str]] = None
    risk_level: Optional[str] = None
    urgent_level: Optional[int] = Field(None, ge=1, le=5)
    lng: Optional[float] = None
    lat: Optional[float] = None
    reporter: Optional[str] = None
    report_time: Optional[datetime] = None
    casualties: Optional[int] = None
    affected_people: Optional[int] = None
    description: Optional[str] = None
    severity: Optional[str] = None


class WarehouseBase(BaseModel):
    name: str
    address: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    manager: Optional[str] = None
    contact: Optional[str] = None


class WarehouseCreate(WarehouseBase):
    id: str


class WarehouseResponse(WarehouseBase):
    id: str

    class Config:
        from_attributes = True


class WarehouseUpdate(BaseModel):
    name: Optional[str] = None
    address: Optional[str] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
    manager: Optional[str] = None
    contact: Optional[str] = None


class MaterialBase(BaseModel):
    name: str
    type: str = Field(..., description="物资类型：防汛物资/地质灾害物资/地震救援物资")
    unit: Optional[str] = None
    weight: Optional[float] = None
    suitable_disaster: list[str] = Field(default_factory=list)


class MaterialCreate(MaterialBase):
    id: str


class MaterialResponse(MaterialBase):
    id: str

    class Config:
        from_attributes = True


class MaterialUpdate(BaseModel):
    name: Optional[str] = None
    type: Optional[str] = None
    unit: Optional[str] = None
    weight: Optional[float] = None
    suitable_disaster: Optional[list[str]] = None


class RescueTeamBase(BaseModel):
    team_name: str
    current_lng: Optional[float] = None
    current_lat: Optional[float] = None
    carry_limit: Optional[float] = None
    suitable_disaster: list[str] = Field(default_factory=list)
    status: str = Field("空闲", description="空闲/已调度")


class RescueTeamCreate(RescueTeamBase):
    id: str


class RescueTeamResponse(RescueTeamBase):
    id: str

    class Config:
        from_attributes = True


class RescueTeamUpdate(BaseModel):
    team_name: Optional[str] = None
    current_lng: Optional[float] = None
    current_lat: Optional[float] = None
    carry_limit: Optional[float] = None
    suitable_disaster: Optional[list[str]] = None
    status: Optional[str] = None


class ShelterBase(BaseModel):
    name: str
    max_capacity: int = 0
    accommodated_count: int = Field(0, description="已容纳人数")
    lng: Optional[float] = None
    lat: Optional[float] = None


class ShelterCreate(ShelterBase):
    id: str


class ShelterResponse(ShelterBase):
    id: str

    class Config:
        from_attributes = True


class ShelterUpdate(BaseModel):
    name: Optional[str] = None
    max_capacity: Optional[int] = None
    accommodated_count: Optional[int] = None
    lng: Optional[float] = None
    lat: Optional[float] = None
