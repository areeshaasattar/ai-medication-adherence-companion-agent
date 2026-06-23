import uuid
from typing import List
from pydantic import BaseModel, Field
from app.schemas.side_effect_report import SeverityLevel

class AgentChatRequest(BaseModel):
    user_id: uuid.UUID
    message: str

class AgentChatResponse(BaseModel):
    response: str
    recommendations: List[str] = Field(default_factory=list)
    adherence_score: float | None = None
    safety_warning: str | None = None

class MissedDoseAnalysisResponse(BaseModel):
    risk_level: str
    recommendation: str
    next_dose_guidance: str

class SideEffectAnalysisResponse(BaseModel):
    severity: SeverityLevel
    recommendation: str
    emergency_flag: bool
