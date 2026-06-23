import uuid
from datetime import datetime
from app.schemas.base import BaseSchema

class ChatHistoryBase(BaseSchema):
    user_message: str
    agent_response: str

class ChatHistoryCreate(ChatHistoryBase):
    user_id: uuid.UUID

class ChatHistoryResponse(ChatHistoryBase):
    id: uuid.UUID
    user_id: uuid.UUID
    created_at: datetime
