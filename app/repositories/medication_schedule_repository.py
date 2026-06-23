from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medication_schedule import MedicationSchedule
from app.repositories.base import BaseRepository

class MedicationScheduleRepository(BaseRepository[MedicationSchedule]):
    def __init__(self, db: AsyncSession):
        super().__init__(MedicationSchedule, db)

    async def get_by_medication_id(self, medication_id: UUID) -> Sequence[MedicationSchedule]:
        result = await self.db.execute(
            select(MedicationSchedule).where(MedicationSchedule.medication_id == medication_id)
        )
        return result.scalars().all()

    async def get_by_user_id(self, user_id: UUID) -> Sequence[MedicationSchedule]:
        result = await self.db.execute(
            select(MedicationSchedule).where(MedicationSchedule.user_id == user_id)
        )
        return result.scalars().all()
