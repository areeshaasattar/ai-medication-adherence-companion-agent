from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medication import Medication
from app.repositories.base import BaseRepository

class MedicationRepository(BaseRepository[Medication]):
    def __init__(self, db: AsyncSession):
        super().__init__(Medication, db)

    async def get_user_medications(self, user_id: UUID) -> Sequence[Medication]:
        result = await self.db.execute(
            select(Medication).where(Medication.user_id == user_id)
        )
        return result.scalars().all()

    async def get_active_medications(self, user_id: UUID) -> Sequence[Medication]:
        return await self.get_user_medications(user_id)
