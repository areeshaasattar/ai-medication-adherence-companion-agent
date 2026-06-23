from uuid import UUID
from datetime import datetime, timedelta
from typing import List
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.reminder import Reminder, ReminderStatus
from app.models.medication_schedule import MedicationSchedule
from app.repositories.reminder_repository import ReminderRepository
from app.repositories.medication_schedule_repository import MedicationScheduleRepository
from app.repositories.dose_log_repository import DoseLogRepository

class ReminderService:
    def __init__(self, db: AsyncSession):
        self.db = db
        self.reminder_repo = ReminderRepository(db)
        self.schedule_repo = MedicationScheduleRepository(db)
        self.dose_log_repo = DoseLogRepository(db)

    async def get_user_reminders(self, user_id: UUID) -> List[Reminder]:
        return await self.reminder_repo.get_user_reminders(user_id)

    async def create_reminder_from_schedule(self, schedule: MedicationSchedule, scheduled_time: datetime) -> Reminder:
        reminder_data = {
            "user_id": schedule.user_id,
            "medication_id": schedule.medication_id,
            "schedule_id": schedule.id,
            "scheduled_time": scheduled_time,
            "message": f"Time to take your medication: {schedule.medication.name}",
            "status": ReminderStatus.PENDING
        }
        return await self.reminder_repo.create(reminder_data)

    async def process_due_reminders(self, now: datetime):
        due_reminders = await self.reminder_repo.get_due_reminders(now)
        for reminder in due_reminders:
            await self.reminder_repo.update(reminder.id, {"status": ReminderStatus.SENT, "reminder_sent_at": now})
            # Log the sending
            print(f"Reminder {reminder.id} sent to user {reminder.user_id}")

    async def detect_missed_doses(self, now: datetime, grace_minutes: int):
        # Grace period logic
        limit = now - timedelta(minutes=grace_minutes)
        
        # Get sent reminders that are past grace period
        reminders_to_check = await self.reminder_repo.get_sent_reminders_past_grace_period(limit)
        
        for reminder in reminders_to_check:
            # Check if a TAKEN dose log exists for this medication, user, and time frame
            dose_logs = await self.dose_log_repo.get_logs_by_medication_and_user(
                medication_id=reminder.medication_id,
                user_id=reminder.user_id
            )
            # Filter logs to see if one was taken near the scheduled time
            taken_dose = next((log for log in dose_logs if log.status == "taken" and abs((log.created_at - reminder.scheduled_time).total_seconds()) < grace_minutes * 60), None)
            
            if taken_dose:
                # Mark reminder as completed
                await self.reminder_repo.update(reminder.id, {"status": ReminderStatus.COMPLETED})
                print(f"Reminder {reminder.id} marked completed")
            else:
                # Create MISSED dose log if it doesn't exist
                # Logic: Check if missed log already exists to avoid duplicates
                existing_missed = next((log for log in dose_logs if log.status == "missed" and (log.created_at - reminder.scheduled_time).total_seconds() < 3600), None)
                if not existing_missed:
                    await self.dose_log_repo.create_dose_log({
                        "user_id": reminder.user_id,
                        "medication_id": reminder.medication_id,
                        "status": "missed",
                        "created_at": now
                    })
                
                # Mark reminder as missed
                await self.reminder_repo.update(reminder.id, {"status": ReminderStatus.MISSED})
                print(f"Reminder {reminder.id} marked missed")

    async def get_pending_reminders(self, user_id: UUID | str) -> list:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now()
        reminders = await self.reminder_repo.get_user_reminders(uid)
        pending = [
            {
                "id": str(r.id),
                "medication_name": r.medication.medication_name if r.medication else "Medication",
                "scheduled_time": r.scheduled_time.strftime("%I:%M %p"),
                "status": r.status
            }
            for r in reminders 
            if r.status == ReminderStatus.PENDING and r.scheduled_time <= now
        ]
        return pending

    async def mark_reminder_sent(self, reminder_id: UUID | str) -> bool:
        rid = UUID(reminder_id) if isinstance(reminder_id, str) else reminder_id
        now = datetime.now()
        updated = await self.reminder_repo.update(rid, {"status": ReminderStatus.SENT, "reminder_sent_at": now})
        return updated is not None

    async def get_upcoming_reminders(self, user_id: UUID | str) -> list:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now()
        tomorrow = now + timedelta(hours=24)
        reminders = await self.reminder_repo.get_user_reminders(uid)
        upcoming = [
            {
                "medication_name": r.medication.medication_name if r.medication else "Medication",
                "scheduled_time": r.scheduled_time.strftime("%I:%M %p"),
                "time_raw": r.scheduled_time
            }
            for r in reminders
            if r.status == ReminderStatus.PENDING and now < r.scheduled_time <= tomorrow
        ]
        upcoming.sort(key=lambda x: x["time_raw"])
        return upcoming

    async def create_followup_reminder(
        self,
        user_id: UUID | str,
        medication_id: UUID | str,
        original_reminder_id: UUID | str,
        delay_minutes: int = 30
    ) -> dict:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        mid = UUID(medication_id) if isinstance(medication_id, str) else medication_id
        orid = UUID(original_reminder_id) if isinstance(original_reminder_id, str) else original_reminder_id
        
        original = await self.reminder_repo.get_by_id(orid)
        if not original:
            raise ValueError("Original reminder not found")
            
        scheduled_time = datetime.now() + timedelta(minutes=delay_minutes)
        reminder_data = {
            "user_id": uid,
            "medication_id": mid,
            "schedule_id": original.schedule_id,
            "scheduled_time": scheduled_time,
            "message": f"FOLLOW-UP: Time to take your medication: {original.medication.medication_name if original.medication else 'Medication'}",
            "status": ReminderStatus.PENDING
        }
        reminder = await self.reminder_repo.create(reminder_data)
        return {"id": str(reminder.id), "scheduled_time": reminder.scheduled_time}

    async def check_and_followup(self, user_id: UUID | str, medication_id: UUID | str) -> str:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        mid = UUID(medication_id) if isinstance(medication_id, str) else medication_id
        
        now = datetime.now()
        two_hours_ago = now - timedelta(hours=2)
        
        # Check if dose was taken in last 2 hours
        logs = await self.dose_log_repo.get_logs_by_medication_and_user(mid, uid)
        taken = any(l.status == "taken" and l.created_at >= two_hours_ago for l in logs)
        
        if taken:
            return "Dose already logged, no followup needed"
        
        # Get latest reminder to use its schedule_id
        reminders = await self.reminder_repo.get_user_reminders(uid)
        relevant = [r for r in reminders if r.medication_id == mid]
        if not relevant:
            return "No previous reminders found for this medication"
        
        latest_reminder = max(relevant, key=lambda r: r.scheduled_time)
        await self.create_followup_reminder(uid, mid, latest_reminder.id, delay_minutes=30)
        return f"Follow-up reminder created for 30 minutes from now"
