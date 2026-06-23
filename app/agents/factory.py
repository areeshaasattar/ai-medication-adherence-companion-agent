import uuid
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.medication_agent import (
    medication_agent,
    AgentDependencies,
    run_medication_agent     
)

from app.repositories.user_repository import UserRepository
from app.repositories.medication_repository import MedicationRepository
from app.repositories.dose_log_repository import DoseLogRepository
from app.repositories.side_effect_repository import SideEffectRepository
from app.repositories.medication_schedule_repository import MedicationScheduleRepository
from app.services.adherence_service import AdherenceService
from app.services.medication_service import MedicationService
from app.services.reminder_service import ReminderService


async def get_medication_agent_deps(db: AsyncSession, user_id: uuid.UUID) -> AgentDependencies:
    """
    Initializes and returns the dependencies for the medication agent.
    """
    user_repo = UserRepository(db)
    med_repo = MedicationRepository(db)
    dose_log_repo = DoseLogRepository(db)
    side_effect_repo = SideEffectRepository(db)
    schedule_repo = MedicationScheduleRepository(db)
    
    med_service = MedicationService(med_repo, user_repo, schedule_repo)
    adherence_service = AdherenceService(dose_log_repo, med_repo)
    reminder_service = ReminderService(db)
    
    return AgentDependencies(
        user_id=user_id,
        adherence_service=adherence_service,
        medication_service=med_service,
        reminder_service=reminder_service,
        user_repo=user_repo,
        medication_repo=med_repo,
        dose_log_repo=dose_log_repo,
        side_effect_repo=side_effect_repo
    )


def get_medication_agent():
    """Returns the pre-configured agent"""
    return medication_agent


async def run_medication_adherence_agent(
    user_message: str,
    db: AsyncSession,
    user_id: uuid.UUID,
    context: dict = None
) -> str:
    """
    Complete flow to run the agent.
    """
    deps = await get_medication_agent_deps(db, user_id)
    
    response = await run_medication_agent(
        user_message=user_message,
        deps=deps
    )
    
    return response