from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reminder import Reminder, ReminderStatus
from datetime import datetime
from typing import List, Optional

class ReminderRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, reminder_data: dict) -> Reminder:
        reminder = Reminder(**reminder_data)
        self.db.add(reminder)
        await self.db.commit()
        await self.db.refresh(reminder)
        return reminder

    async def get_by_id(self, reminder_id: UUID) -> Optional[Reminder]:
        result = await self.db.execute(select(Reminder).where(Reminder.id == reminder_id))
        return result.scalar_one_or_none()

    async def get_user_reminders(self, user_id: UUID) -> List[Reminder]:
        result = await self.db.execute(select(Reminder).where(Reminder.user_id == user_id))
        return list(result.scalars().all())

    async def get_pending_reminders(self) -> List[Reminder]:
        result = await self.db.execute(select(Reminder).where(Reminder.status == ReminderStatus.PENDING))
        return list(result.scalars().all())

    async def get_due_reminders(self, now: datetime) -> List[Reminder]:
        result = await self.db.execute(
            select(Reminder)
            .where(Reminder.status == ReminderStatus.PENDING)
            .where(Reminder.scheduled_time <= now)
        )
        return list(result.scalars().all())

    async def get_sent_reminders_past_grace_period(self, grace_limit: datetime) -> List[Reminder]:
        result = await self.db.execute(
            select(Reminder)
            .where(Reminder.status == ReminderStatus.SENT)
            .where(Reminder.reminder_sent_at <= grace_limit)
        )
        return list(result.scalars().all())

    async def update(self, reminder_id: UUID, update_data: dict) -> Optional[Reminder]:
        await self.db.execute(
            update(Reminder)
            .where(Reminder.id == reminder_id)
            .values(**update_data)
        )
        await self.db.commit()
        return await self.get_by_id(reminder_id)

    async def delete(self, reminder_id: UUID) -> None:
        await self.db.execute(delete(Reminder).where(Reminder.id == reminder_id))
        await self.db.commit()
