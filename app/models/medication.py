import uuid
from datetime import datetime
from typing import List, TYPE_CHECKING
from sqlalchemy import String, DateTime, ForeignKey, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship
from sqlalchemy.dialects.postgresql import UUID
from app.models.base import Base, get_utc_now

if TYPE_CHECKING:
    from .user import User
    from .medication_schedule import MedicationSchedule
    from .dose_log import DoseLog
    from .side_effect_report import SideEffectReport
    from .reminder import Reminder

class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), index=True)
    medication_name: Mapped[str] = mapped_column(String(255), nullable=False)
    dosage: Mapped[str] = mapped_column(String(100))
    frequency_per_day: Mapped[int] = mapped_column(default=1)
    instructions: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, index=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=get_utc_now, onupdate=get_utc_now)

    # Relationships
    user: Mapped["User"] = relationship(back_populates="medications")
    schedules: Mapped[List["MedicationSchedule"]] = relationship(back_populates="medication", cascade="all, delete-orphan")
    dose_logs: Mapped[List["DoseLog"]] = relationship(back_populates="medication", cascade="all, delete-orphan")
    side_effects: Mapped[List["SideEffectReport"]] = relationship(back_populates="medication", cascade="all, delete-orphan")
    reminders: Mapped[List["Reminder"]] = relationship(back_populates="medication", cascade="all, delete-orphan")
