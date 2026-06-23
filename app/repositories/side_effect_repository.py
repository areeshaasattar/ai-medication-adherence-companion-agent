from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.side_effect_report import SideEffectReport
from app.repositories.base import BaseRepository

class SideEffectRepository(BaseRepository[SideEffectReport]):
    def __init__(self, db: AsyncSession):
        super().__init__(SideEffectReport, db)

    async def get_reports_by_user(self, user_id: UUID) -> Sequence[SideEffectReport]:
        result = await self.db.execute(
            select(SideEffectReport).where(SideEffectReport.user_id == user_id)
        )
        return result.scalars().all()
