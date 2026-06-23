from apscheduler.schedulers.asyncio import AsyncIOScheduler
from datetime import datetime, timedelta
from app.core.database import AsyncSessionLocal
from app.services.reminder_service import ReminderService
from app.repositories.medication_schedule_repository import MedicationScheduleRepository
from app.repositories.reminder_repository import ReminderRepository

def get_db_session():
    return AsyncSessionLocal()

async def generate_reminders_job():
    async with get_db_session() as db:
        print("Running generate_reminders_job")
        schedule_repo = MedicationScheduleRepository(db)
        reminder_service = ReminderService(db)
        
        # Get active schedules
        schedules = await schedule_repo.get_all()
        active_schedules = [s for s in schedules if s.is_active]
        
        now = datetime.now()
        for schedule in active_schedules:
            # Simple logic: check if a reminder exists for the scheduled time today
            # If not, create one.
            
            # This is extremely simplified and would need robust time handling.
            scheduled_time = datetime.combine(now.date(), schedule.time_of_day)
            if scheduled_time < now:
                scheduled_time += timedelta(days=1)
                
            await reminder_service.create_reminder_from_schedule(schedule, scheduled_time)
            print(f"Reminder created for schedule {schedule.id}")

async def send_reminders_job():
    async with get_db_session() as db:
        service = ReminderService(db)
        await service.process_due_reminders(datetime.now())
        print("Running send_reminders_job")

async def missed_dose_detection_job():
    async with get_db_session() as db:
        service = ReminderService(db)
        await service.detect_missed_doses(datetime.now(), 60)
        print("Running missed_dose_detection_job")

def start_scheduler():
    scheduler = AsyncIOScheduler()
    
    scheduler.add_job(generate_reminders_job, 'interval', minutes=5)
    scheduler.add_job(send_reminders_job, 'interval', minutes=5)
    scheduler.add_job(missed_dose_detection_job, 'interval', minutes=5)
    
    scheduler.start()
    return scheduler
