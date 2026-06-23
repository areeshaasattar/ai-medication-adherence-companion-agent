from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.dose_log import DoseLogCreate, DoseLogResponse
from app.repositories.dose_log_repository import DoseLogRepository
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=DoseLogResponse, status_code=status.HTTP_201_CREATED)
async def log_dose(
    log_in: DoseLogCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Log a medication dose (taken, missed, or skipped).
    """
    if log_in.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    repo = DoseLogRepository(db)
    return await repo.create(log_in.model_dump())

@router.get("/", response_model=List[DoseLogResponse])
async def list_dose_logs(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all dose logs for the current user.
    """
    repo = DoseLogRepository(db)
    return await repo.get_user_logs(current_user.id)

@router.get("/medication/{medication_id}", response_model=List[DoseLogResponse])
async def list_medication_logs(
    medication_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all dose logs for a specific medication.
    """
    repo = DoseLogRepository(db)
    return await repo.get_logs_by_medication(medication_id)
