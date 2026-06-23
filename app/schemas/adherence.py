import uuid
from datetime import datetime
from enum import Enum
from typing import List
from pydantic import Field
from app.schemas.base import BaseSchema

class RiskLevel(str, Enum):
    LOW = "LOW"
    MEDIUM = "MEDIUM"
    HIGH = "HIGH"

class AdherenceTrend(BaseSchema):
    current_period_score: float
    previous_period_score: float
    trend_percentage: float
    direction: str  # "up", "down", "stable"

class MedicationInsight(BaseSchema):
    medication_id: uuid.UUID
    medication_name: str
    adherence_score: float
    missed_count: int
    recommendation: str

class AdherenceRisk(BaseSchema):
    risk_level: RiskLevel
    risk_factors: List[str]
    predicted_at: datetime = Field(default_factory=datetime.utcnow)

class AdherenceAnalytics(BaseSchema):
    user_id: uuid.UUID
    overall_score: float
    trend: AdherenceTrend
    most_missed_medication: MedicationInsight | None = None
    risk_prediction: AdherenceRisk
    insights: List[MedicationInsight]
