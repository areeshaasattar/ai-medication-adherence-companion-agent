import uuid
from datetime import datetime, time, date
from enum import Enum
from typing import TYPE_CHECKING, List, Optional
from sqlalchemy import DateTime, ForeignKey, Time, String, Date, Boolean, Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID, ARRAY
from app.models.base import Base, get_utc_now

if TYPE_CHECKING:
    from .medication import Medication
    from .reminder import Reminder
    from .user import User

class FrequencyType(str, Enum):
    DAILY = "daily"
    WEEKLY = "weekly"
    MONTHLY = "monthly"
    AS_NEEDED = "as_needed"

class MedicationSchedule(Base):
    __tablename__ = "medication_schedules"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), index=True, nullable=False)
    medication_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("medications.id", ondelete="CASCADE"), index=True, nullable=False)
    
    # Detailed Schedule Fields
    time_of_day: Mapped[time] = mapped_column(Time, nullable=False)
    frequency: Mapped[FrequencyType] = mapped_column(SQLEnum(FrequencyType), default=FrequencyType.DAILY)
    days_of_week: Mapped[Optional[List[str]]] = mapped_column(ARRAY(String), nullable=True) # e.g., ["Monday", "Wednesday"]
    
    start_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now)
    end_date: Mapped[Optional[datetime]] = mapped_column(DateTime(timezone=True), nullable=True)
    
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, index=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    user: Mapped["User"] = relationship()
    medication: Mapped["Medication"] = relationship(back_populates="schedules")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="schedule", cascade="all, delete-orphan")
