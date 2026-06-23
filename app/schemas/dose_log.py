import uuid
from datetime import datetime, timezone
from enum import Enum
from pydantic import field_validator
from app.schemas.base import BaseSchema

class DoseStatus(str, Enum):
    TAKEN = "taken"
    MISSED = "missed"
    SKIPPED = "skipped"

class DoseLogBase(BaseSchema):
    scheduled_time: datetime
    taken_at: datetime | None = None
    status: DoseStatus = DoseStatus.MISSED
    notes: str | None = None

    @field_validator('taken_at')
    @classmethod
    def taken_at_not_in_future(cls, v):
        if v and v > datetime.now(timezone.utc):
            raise ValueError('taken_at cannot be in the future')
        return v

class DoseLogCreate(DoseLogBase):
    user_id: uuid.UUID
    medication_id: uuid.UUID

class DoseLogResponse(DoseLogBase):
    id: uuid.UUID
    user_id: uuid.UUID
    medication_id: uuid.UUID
    created_at: datetime
