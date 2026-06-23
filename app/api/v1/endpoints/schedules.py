from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession
from uuid import UUID
from typing import List
from app.api.dependencies.auth import get_current_user
from app.core.database import get_db
from app.models.user import User
from app.schemas.medication_schedule import MedicationScheduleCreate, MedicationScheduleResponse, MedicationScheduleUpdate
from app.services.medication_schedule_service import MedicationScheduleService

router = APIRouter(prefix="", tags=["schedules"])

@router.post("/", response_model=MedicationScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_schedule(
    schedule_in: MedicationScheduleCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MedicationScheduleService(db)
    return await service.create_schedule(current_user.id, schedule_in)

@router.get("/", response_model=List[MedicationScheduleResponse])
async def get_user_schedules(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MedicationScheduleService(db)
    return await service.get_user_schedules(current_user.id)

@router.get("/{schedule_id}", response_model=MedicationScheduleResponse)
async def get_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MedicationScheduleService(db)
    schedule = await service.get_schedule(schedule_id)
    if not schedule or schedule.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    return schedule

@router.patch("/{schedule_id}", response_model=MedicationScheduleResponse)
async def update_schedule(
    schedule_id: UUID,
    schedule_in: MedicationScheduleUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MedicationScheduleService(db)
    # Check ownership
    existing = await service.get_schedule(schedule_id)
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    updated = await service.update_schedule(schedule_id, schedule_in)
    return updated

@router.delete("/{schedule_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_schedule(
    schedule_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    service = MedicationScheduleService(db)
    # Check ownership
    existing = await service.get_schedule(schedule_id)
    if not existing or existing.user_id != current_user.id:
        raise HTTPException(status_code=404, detail="Schedule not found")
    
    await service.delete_schedule(schedule_id)
    return None
