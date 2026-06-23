import uuid
from datetime import datetime
from enum import Enum
from pydantic import Field
from app.schemas.base import BaseSchema

class SeverityLevel(str, Enum):
    MILD = "mild"
    MODERATE = "moderate"
    SEVERE = "severe"
    EMERGENCY = "emergency"

class SideEffectReportBase(BaseSchema):
    symptom_description: str
    severity: SeverityLevel = SeverityLevel.MILD
    recommendation: str | None = None

class SideEffectReportCreate(SideEffectReportBase):
    user_id: uuid.UUID
    medication_id: uuid.UUID

class SideEffectReportResponse(SideEffectReportBase):
    id: uuid.UUID
    user_id: uuid.UUID
    medication_id: uuid.UUID
    created_at: datetime
