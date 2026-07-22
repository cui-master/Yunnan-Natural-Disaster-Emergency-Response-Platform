from pydantic import BaseModel, Field
from typing import Optional, Any


class DispatchRecommendation(BaseModel):
    warehouse_name: str
    material_name: str
    stock_num: int
    total_dist: float
    score: float


class AvailableTeam(BaseModel):
    team_name: str
    dist: float


class ShelterInfo(BaseModel):
    name: str
    max_capacity: int
    remain_space: int
    dist: float


class DispatchPlanResponse(BaseModel):
    area_name: str
    disaster_type: str
    risk_level: str
    recommendations: list[DispatchRecommendation] = Field(default_factory=list)
    available_teams: list[AvailableTeam] = Field(default_factory=list)
    shelters: list[ShelterInfo] = Field(default_factory=list)


class WorkflowRunRequest(BaseModel):
    area_name: str
    disaster_type: str
    risk_level: str
    input_risk_info: str
    vision_text: Optional[str] = None


class WorkflowRunResponse(BaseModel):
    task_id: str
    status: str
    result: Optional[str] = None


class RiskLevelUpdateRequest(BaseModel):
    spot_id: str
    risk_level: str
    urgent_level: Optional[int] = None
    disaster_type: Optional[list[str]] = None
