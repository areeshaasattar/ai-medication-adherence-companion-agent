from uuid import UUID
from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.medication import MedicationCreate, MedicationUpdate, MedicationResponse
from app.schemas.medication_schedule import MedicationScheduleCreate, MedicationScheduleUpdate, MedicationScheduleResponse
from app.services.medication_service import MedicationService
from app.repositories.medication_repository import MedicationRepository
from app.repositories.medication_schedule_repository import MedicationScheduleRepository
from app.repositories.user_repository import UserRepository
from app.models.user import User

router = APIRouter()

def get_medication_service(db: AsyncSession = Depends(get_db)) -> MedicationService:
    med_repo = MedicationRepository(db)
    user_repo = UserRepository(db)
    sched_repo = MedicationScheduleRepository(db)
    return MedicationService(med_repo, user_repo, sched_repo)

# --- Medication CRUD ---

@router.post("/", response_model=MedicationResponse, status_code=status.HTTP_201_CREATED)
async def create_medication(
    medication_in: MedicationCreate,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Register a new medication with optional schedules.
    """
    if medication_in.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await service.create_medication(medication_in)

@router.get("/", response_model=List[MedicationResponse])
async def list_medications(
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    List all medications (with schedules) for the current user.
    """
    return await service.get_user_medications(current_user.id)

@router.get("/{id}", response_model=MedicationResponse)
async def get_medication(
    id: UUID,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Get details of a specific medication and its schedules.
    """
    med = await service.get_medication(id)
    if med.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return med

@router.patch("/{id}", response_model=MedicationResponse)
async def update_medication(
    id: UUID,
    medication_in: MedicationUpdate,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Update medication details and optionally replace schedules.
    """
    med = await service.get_medication(id)
    if med.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await service.update_medication(id, medication_in)

@router.delete("/{id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_medication(
    id: UUID,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Delete a medication and all its schedules.
    """
    med = await service.get_medication(id)
    if med.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    await service.delete_medication(id)

# --- Schedule Management ---

@router.get("/{medication_id}/schedule", response_model=List[MedicationScheduleResponse])
async def get_medication_schedule(
    medication_id: UUID,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Retrieve the schedule for a specific medication.
    """
    med = await service.get_medication(medication_id)
    if med.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await service.get_medication_schedules(medication_id)

import logging
import traceback

logger = logging.getLogger(__name__)

@router.post("/{medication_id}/schedule", response_model=MedicationScheduleResponse, status_code=status.HTTP_201_CREATED)
async def create_medication_schedule(
    medication_id: UUID,
    schedule_in: MedicationScheduleCreate,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Add a new schedule entry to an existing medication.
    """
    # Log incoming request
    logger.info(
        "Incoming POST /medications/%s/schedule payload=%s", medication_id, schedule_in
    )
    try:
        med = await service.get_medication(medication_id)
        if med.user_id != current_user.id and current_user.role != "admin":
            raise HTTPException(status_code=403, detail="Not enough permissions")
        return await service.create_schedule(medication_id, schedule_in)
    except HTTPException:
        # Re-raise known HTTP exceptions without modification
        raise
    except Exception as e:
        # Capture full traceback and log it
        tb = traceback.format_exc()
        logger.exception("Unhandled exception in create_medication_schedule")
        # Expose the exception traceback in the HTTP 500 response
        raise HTTPException(status_code=500, detail=tb)

@router.put("/{medication_id}/schedule/{schedule_id}", response_model=MedicationScheduleResponse)
async def update_medication_schedule(
    medication_id: UUID,
    schedule_id: UUID,
    schedule_in: MedicationScheduleUpdate,
    current_user: User = Depends(get_current_user),
    service: MedicationService = Depends(get_medication_service)
):
    """
    Update a specific schedule entry.
    """
    med = await service.get_medication(medication_id)
    if med.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
    return await service.update_schedule(schedule_id, schedule_in)
