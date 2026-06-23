from pydantic import BaseModel, ConfigDict
from datetime import datetime
from uuid import UUID
from app.models.reminder import ReminderStatus

class ReminderBase(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    
    scheduled_time: datetime
    message: str

class ReminderCreate(ReminderBase):
    medication_id: UUID
    schedule_id: UUID

class ReminderUpdate(BaseModel):
    status: ReminderStatus | None = None
    reminder_sent_at: datetime | None = None

class ReminderResponse(ReminderBase):
    id: UUID
    user_id: UUID
    medication_id: UUID
    schedule_id: UUID
    reminder_sent_at: datetime | None
    status: ReminderStatus
    created_at: datetime
