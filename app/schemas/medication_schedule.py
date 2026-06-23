import uuid
from datetime import datetime, time
from enum import Enum
from typing import List, Optional
from pydantic import Field
from app.schemas.base import BaseSchema


class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"


class MedicationScheduleBase(BaseSchema):
    time_of_day: time
    frequency: FrequencyType = FrequencyType.DAILY
    days_of_week: List[str] = Field(default_factory=list)
    start_date: datetime = Field(default_factory=datetime.utcnow)
    end_date: Optional[datetime] = None
    is_active: bool = True


class MedicationScheduleCreate(MedicationScheduleBase):
    pass


class MedicationScheduleUpdate(BaseSchema):
    time_of_day: Optional[time] = None
    frequency: Optional[FrequencyType] = None
    days_of_week: Optional[List[str]] = None
    start_date: Optional[datetime] = None
    end_date: Optional[datetime] = None
    is_active: Optional[bool] = None


class MedicationScheduleResponse(MedicationScheduleBase):
    id: uuid.UUID
    user_id: uuid.UUID
    medication_id: uuid.UUID
    created_at: datetime
    updated_at: datetime