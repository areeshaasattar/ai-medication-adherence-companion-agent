from typing import Sequence
from uuid import UUID
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.chat_history import ChatHistory
from app.repositories.base import BaseRepository

class ChatHistoryRepository(BaseRepository[ChatHistory]):
    def __init__(self, db: AsyncSession):
        super().__init__(ChatHistory, db)

    async def get_recent_conversations(
        self, user_id: UUID, limit: int = 10
    ) -> Sequence[ChatHistory]:
        result = await self.db.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc())
            .limit(limit)
        )
        return result.scalars().all()
