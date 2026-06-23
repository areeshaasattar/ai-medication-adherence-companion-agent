from uuid import UUID
from datetime import date, time, datetime
from typing import List, Optional
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.medication_schedule import MedicationSchedule
from app.repositories.medication_schedule_repository import MedicationScheduleRepository
from app.schemas.medication_schedule import MedicationScheduleCreate, MedicationScheduleUpdate

class MedicationScheduleService:
    def __init__(self, db: AsyncSession):
        self.repository = MedicationScheduleRepository(db)

    async def generate_schedule_from_frequency(
        self, 
        medication_id: str, 
        user_id: str, 
        frequency: str,  # "once_daily", "twice_daily", "three_times_daily", "four_times_daily"
        start_date: date,
        end_date: date | None = None
    ) -> list:
        mapping = {
            "once_daily": ["09:00"],
            "twice_daily": ["09:00", "21:00"],
            "three_times_daily": ["08:00", "14:00", "20:00"],
            "four_times_daily": ["08:00", "12:00", "16:00", "20:00"]
        }
        
        times = mapping.get(frequency.lower(), ["09:00"])
        created_schedules = []
        
        # Convert str IDs to UUID if needed
        u_id = UUID(user_id) if isinstance(user_id, str) else user_id
        m_id = UUID(medication_id) if isinstance(medication_id, str) else medication_id
        
        for t_str in times:
            t = time.fromisoformat(t_str)
            schedule_data = {
                "user_id": u_id,
                "medication_id": m_id,
                "time_of_day": t,
                "frequency": "daily",
                "start_date": datetime.combine(start_date, time.min),
                "end_date": datetime.combine(end_date, time.max) if end_date else None,
                "is_active": True
            }
            created_schedules.append(await self.repository.create(schedule_data))
            
        return created_schedules

    async def create_schedule(self, user_id: UUID, schedule_in: MedicationScheduleCreate) -> MedicationSchedule:
        data = schedule_in.model_dump()
        data["user_id"] = user_id
        if "frequency" in data and isinstance(data["frequency"], str):
            data["frequency"] = data["frequency"].lower()
        return await self.repository.create(data)

    async def get_schedule(self, schedule_id: UUID) -> Optional[MedicationSchedule]:
        return await self.repository.get_by_id(schedule_id)

    async def get_user_schedules(self, user_id: UUID) -> List[MedicationSchedule]:
        return list(await self.repository.get_by_user_id(user_id))

    async def update_schedule(self, schedule_id: UUID, schedule_in: MedicationScheduleUpdate) -> Optional[MedicationSchedule]:
        schedule = await self.repository.get_by_id(schedule_id)
        if not schedule:
            return None
        return await self.repository.update(schedule, schedule_in.model_dump(exclude_unset=True))

    async def delete_schedule(self, schedule_id: UUID) -> bool:
        return await self.repository.delete(schedule_id)
