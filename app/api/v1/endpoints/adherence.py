from typing import Dict, Any
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.adherence import AdherenceAnalytics
from app.services.adherence_service import AdherenceService
from app.repositories.dose_log_repository import DoseLogRepository
from app.repositories.medication_repository import MedicationRepository
from app.models.user import User

router = APIRouter()

@router.get("/summary", response_model=Dict[str, Any])
async def get_adherence_summary(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get a summary of medication adherence scores and streaks.
    """
    dose_log_repo = DoseLogRepository(db)
    medication_repo = MedicationRepository(db)
    service = AdherenceService(dose_log_repo, medication_repo)
    return await service.generate_adherence_summary(current_user.id)

@router.get("/analytics", response_model=AdherenceAnalytics)
async def get_adherence_analytics(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Get detailed adherence analytics, trends, and risk predictions.
    """
    dose_log_repo = DoseLogRepository(db)
    medication_repo = MedicationRepository(db)
    service = AdherenceService(dose_log_repo, medication_repo)
    
    overall_score = await service.calculate_overall_adherence(current_user.id)
    trend = await service.calculate_adherence_trend(current_user.id)
    most_missed = await service.get_most_missed_medication(current_user.id)
    risk = await service.predict_non_adherence_risk(current_user.id)
    insights = await service.generate_medication_insights(current_user.id)
    
    return AdherenceAnalytics(
        user_id=current_user.id,
        overall_score=overall_score,
        trend=trend,
        most_missed_medication=most_missed,
        risk_prediction=risk,
        insights=insights
    )
