# app/api/v1/endpoints/agent.py

import uuid
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from pydantic import BaseModel
from typing import Optional, List, Dict

from app.core.database import get_db
from app.agents.medication_agent import run_medication_agent, AgentDependencies
from app.services.adherence_service import AdherenceService
from app.services.medication_service import MedicationService
from app.repositories.user_repository import UserRepository
from app.repositories.medication_repository import MedicationRepository
from app.repositories.dose_log_repository import DoseLogRepository
from app.repositories.side_effect_repository import SideEffectRepository
from app.repositories.chat_history_repository import ChatHistoryRepository

router = APIRouter()


# ---- Request / Response schemas ----
class AgentChatRequest(BaseModel):
    message: str
    include_history: Optional[bool] = True


class AgentChatResponse(BaseModel):
    response: str
    user_id: str


# ---- Dependency: build AgentDependencies from db session + user_id ----
def get_agent_deps(
    user_id: uuid.UUID,
    db: AsyncSession,
) -> AgentDependencies:
    return AgentDependencies(
        user_id=user_id,
        adherence_service=AdherenceService(db),
        medication_service=MedicationService(db),
        user_repo=UserRepository(db),
        medication_repo=MedicationRepository(db),
        dose_log_repo=DoseLogRepository(db),
        side_effect_repo=SideEffectRepository(db),
    )


# ---- Endpoint ----
@router.post("/agent/chat", response_model=AgentChatResponse)
async def chat_with_agent(
    request: AgentChatRequest,
    db: AsyncSession = Depends(get_db),
):
    """
    Chat with the Medication Adherence Companion agent.
    For demo/lead review: user_id is hardcoded.
    Replace with: user_id = current_user.id
    """

    demo_user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")

    # Fetch conversation history (optional)
    conversation_history = None
    if request.include_history:
        try:
            chat_repo = ChatHistoryRepository(db)
            history_records = await chat_repo.get_recent_messages(demo_user_id, limit=6)
            conversation_history = [
                {"role": r.role, "content": r.content}
                for r in history_records
            ]
        except Exception:
            conversation_history = None  

    # Build dependencies
    deps = get_agent_deps(demo_user_id, db)

    # Run agent
    try:
        response = await run_medication_agent(
            user_message=request.message,
            deps=deps,
            conversation_history=conversation_history,
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Agent error: {str(e)}")

    return AgentChatResponse(
        response=response,
        user_id=str(demo_user_id),
    )