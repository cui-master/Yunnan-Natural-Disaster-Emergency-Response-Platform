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


class DisasterSpotCreate(DisasterSpotBase):
    id: str


class DisasterSpotResponse(DisasterSpotBase):
    id: str
    create_time: Optional[datetime] = None

    class Config:
        from_attributes = True


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


class ShelterBase(BaseModel):
    name: str
    max_capacity: int = 0
    remain_space: int = 0
    lng: Optional[float] = None
    lat: Optional[float] = None


class ShelterCreate(ShelterBase):
    id: str


class ShelterResponse(ShelterBase):
    id: str

    class Config:
        from_attributes = True
