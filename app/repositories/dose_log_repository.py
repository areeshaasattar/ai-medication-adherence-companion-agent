from typing import Sequence
from uuid import UUID
from datetime import datetime
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.dose_log import DoseLog
from app.repositories.base import BaseRepository

class DoseLogRepository(BaseRepository[DoseLog]):
    def __init__(self, db: AsyncSession):
        super().__init__(DoseLog, db)

    async def get_user_logs(self, user_id: UUID) -> Sequence[DoseLog]:
        result = await self.db.execute(
            select(DoseLog).where(DoseLog.user_id == user_id)
        )
        return result.scalars().all()

    async def get_logs_by_medication(self, medication_id: UUID) -> Sequence[DoseLog]:
        result = await self.db.execute(
            select(DoseLog).where(DoseLog.medication_id == medication_id)
        )
        return result.scalars().all()

    async def get_logs_between_dates(
        self, user_id: UUID, start_date: datetime, end_date: datetime
    ) -> Sequence[DoseLog]:
        result = await self.db.execute(
            select(DoseLog).where(
                and_(
                    DoseLog.user_id == user_id,
                    DoseLog.scheduled_time >= start_date,
                    DoseLog.scheduled_time <= end_date,
                )
            )
        )
        return result.scalars().all()
