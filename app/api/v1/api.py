from fastapi import APIRouter
from app.api.v1.endpoints import (
    auth,
    medication,
    dose_log,
    adherence,
    side_effect,
    agent,
    reminder,
    schedules,
)

api_router = APIRouter()

api_router.include_router(auth.router, tags=["Authentication"])
api_router.include_router(medication.router, prefix="/medications", tags=["Medications"])
api_router.include_router(dose_log.router, prefix="/doses", tags=["Dose Tracking"])
api_router.include_router(adherence.router, prefix="/adherence", tags=["Analytics"])
api_router.include_router(side_effect.router, prefix="/side-effects", tags=["Side Effects"])
api_router.include_router(agent.router, prefix="/agent", tags=["AI Agent"])
api_router.include_router(reminder.router, prefix="/reminders", tags=["Reminders"])
api_router.include_router(schedules.router, prefix="/schedules", tags=["Schedules"])
