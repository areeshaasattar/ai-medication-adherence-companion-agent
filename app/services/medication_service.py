from uuid import UUID
from typing import Sequence, List
from fastapi import HTTPException, status
from sqlalchemy.orm import selectinload
from sqlalchemy import select

from app.repositories.medication_repository import MedicationRepository
from app.repositories.user_repository import UserRepository
from app.repositories.medication_schedule_repository import MedicationScheduleRepository
from app.services.medication_schedule_service import MedicationScheduleService
from app.schemas.medication import MedicationCreate, MedicationUpdate, MedicationResponse

from app.schemas.medication_schedule import MedicationScheduleCreate, MedicationScheduleUpdate, MedicationScheduleResponse
from app.models.medication import Medication
from app.models.medication_schedule import MedicationSchedule

import logging
import traceback

logger = logging.getLogger(__name__)

class MedicationService:
    def __init__(
        self, 
        medication_repo: MedicationRepository,
        user_repo: UserRepository,
        schedule_repo: MedicationScheduleRepository
    ):
        self.medication_repo = medication_repo
        self.user_repo = user_repo
        self.schedule_repo = schedule_repo
        self.schedule_service = MedicationScheduleService(medication_repo.db)

    async def create_medication(self, medication_in: MedicationCreate) -> MedicationResponse:
        user = await self.user_repo.db.get(self.user_repo.model, medication_in.user_id)
        if not user:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"User with ID {medication_in.user_id} not found"
            )

        if not medication_in.medication_name.strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication name cannot be empty"
            )

        medication_data = medication_in.model_dump(mode="json", exclude={"schedules"})
        db_medication = await self.medication_repo.create(medication_data)

        for sched_in in medication_in.schedules:
            sched_data = sched_in.model_dump(mode="json")
            sched_data["medication_id"] = str(db_medication.id)
            await self.schedule_repo.create(sched_data)

        # Auto-generate schedules if none provided
        if not medication_in.schedules:
            freq_map = {
                1: "once_daily",
                2: "twice_daily",
                3: "three_times_daily",
                4: "four_times_daily"
            }
            frequency_str = freq_map.get(db_medication.frequency_per_day, "once_daily")
            await self.schedule_service.generate_schedule_from_frequency(
                medication_id=str(db_medication.id),
                user_id=str(db_medication.user_id),
                frequency=frequency_str,
                start_date=db_medication.created_at.date()
            )

        return await self.get_medication(db_medication.id)

    async def get_medication(self, medication_id: UUID) -> MedicationResponse:
        result = await self.medication_repo.db.execute(
            select(Medication)
            .where(Medication.id == medication_id)
            .options(selectinload(Medication.schedules))
        )
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medication with ID {medication_id} not found"
            )
        return MedicationResponse.model_validate(db_obj)

    async def get_user_medications(self, user_id: UUID) -> Sequence[MedicationResponse]:
        result = await self.medication_repo.db.execute(
            select(Medication)
            .where(Medication.user_id == user_id)
            .options(selectinload(Medication.schedules))
        )
        db_objs = result.scalars().all()
        return [MedicationResponse.model_validate(obj) for obj in db_objs]

    async def get_active_medications(self, user_id: UUID) -> Sequence[MedicationResponse]:
        return await self.get_user_medications(user_id)

    async def update_medication(
        self, medication_id: UUID, medication_in: MedicationUpdate
    ) -> MedicationResponse:
        result = await self.medication_repo.db.execute(
            select(Medication)
            .where(Medication.id == medication_id)
            .options(selectinload(Medication.schedules))
        )
        db_obj = result.scalar_one_or_none()
        
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medication with ID {medication_id} not found"
            )
        
        update_data = medication_in.model_dump(mode="json", exclude_unset=True, exclude={"schedules"})
        
        if "medication_name" in update_data and not update_data["medication_name"].strip():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Medication name cannot be empty"
            )

        updated_obj = await self.medication_repo.update(db_obj, update_data)
        
        if medication_in.schedules is not None:
            for old_sched in db_obj.schedules:
                await self.schedule_repo.delete(old_sched.id)
            
            for sched_in in medication_in.schedules:
                sched_data = sched_in.model_dump(mode="json")
                sched_data["medication_id"] = str(medication_id)
                await self.schedule_repo.create(sched_data)

        return await self.get_medication(medication_id)

    async def delete_medication(self, medication_id: UUID) -> bool:
        success = await self.medication_repo.delete(medication_id)
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Medication with ID {medication_id} not found"
            )
        return True

    async def get_medication_schedules(self, medication_id: UUID) -> Sequence[MedicationScheduleResponse]:
        db_objs = await self.schedule_repo.get_by_medication_id(medication_id)
        return [MedicationScheduleResponse.model_validate(obj) for obj in db_objs]

    async def create_schedule(self, medication_id: UUID, schedule_in: MedicationScheduleCreate) -> MedicationScheduleResponse:
        medication = await self.get_medication(medication_id)

        sched_data = schedule_in.model_dump(mode="json")
        sched_data["medication_id"] = str(medication_id)
        sched_data["user_id"] = str(medication.user_id)

        db_obj = await self.schedule_repo.create(sched_data)
        return MedicationScheduleResponse.model_validate(db_obj)


    async def update_schedule(self, schedule_id: UUID, schedule_in: MedicationScheduleUpdate) -> MedicationScheduleResponse:
        db_obj = await self.schedule_repo.get_by_id(schedule_id)
        if not db_obj:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Schedule with ID {schedule_id} not found"
            )
        
        update_data = schedule_in.model_dump(mode="json", exclude_unset=True)
        updated_obj = await self.schedule_repo.update(db_obj, update_data)
        return MedicationScheduleResponse.model_validate(updated_obj)