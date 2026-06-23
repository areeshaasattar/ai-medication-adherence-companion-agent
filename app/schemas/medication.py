import uuid
from datetime import datetime
from typing import List, Optional
from pydantic import Field
from app.schemas.base import BaseSchema
from app.schemas.medication_schedule import MedicationScheduleCreate, MedicationScheduleResponse

class MedicationBase(BaseSchema):
    medication_name: str = Field(..., max_length=255)
    dosage: str = Field(..., max_length=100)
    frequency_per_day: int = Field(default=1, ge=1, le=24)
    instructions: str | None = None

class MedicationCreate(MedicationBase):
    user_id: uuid.UUID
    schedules: List[MedicationScheduleCreate] = Field(default_factory=list)

class MedicationUpdate(BaseSchema):
    medication_name: Optional[str] = Field(None, max_length=255)
    dosage: Optional[str] = Field(None, max_length=100)
    frequency_per_day: Optional[int] = Field(None, ge=1, le=24)
    instructions: Optional[str] = None
    schedules: Optional[List[MedicationScheduleCreate]] = None

class MedicationResponse(MedicationBase):
    id: uuid.UUID
    user_id: uuid.UUID
    schedules: List[MedicationScheduleResponse] = Field(default_factory=list)
    created_at: datetime
    updated_at: datetime
