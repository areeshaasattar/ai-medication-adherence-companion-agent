# test_agent_quick.py
# Run:
# python -m scripts.test_agent

import asyncio
import uuid
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timezone


def make_mock_deps(user_id: uuid.UUID):
    from app.agents.medication_agent import AgentDependencies

    # =====================
    # Mock Adherence Service
    # =====================
    adherence_svc = MagicMock()

    adherence_svc.generate_adherence_summary = AsyncMock(
        return_value={
            "overall_score": 78.5,
            "weekly_score": 85.0,
            "current_streak": 3,
            "total_doses_taken": 45,
            "total_doses_missed": 12,
        }
    )

    adherence_svc.predict_non_adherence_risk = AsyncMock(
        return_value=MagicMock(
            model_dump=lambda: {
                "risk_level": "medium",
                "risk_score": 0.42,
                "reasons": ["Evening doses often missed"]
            }
        )
    )

    adherence_svc.calculate_adherence_trend = AsyncMock(
        return_value=MagicMock(
            model_dump=lambda: {
                "trend": "improving",
                "change_percent": 5.2
            }
        )
    )

    adherence_svc.get_most_missed_medication = AsyncMock(
        return_value=MagicMock(
            model_dump=lambda: {
                "medication_name": "Metformin 500mg",
                "missed_count": 8
            }
        )
    )

    adherence_svc.calculate_missed_dose_streak = AsyncMock(return_value=2)

    adherence_svc.get_streak = AsyncMock(return_value=3)

    adherence_svc.get_weekly_adherence = AsyncMock(
        return_value={
            "percentage": 85.0,
            "taken": 12,
            "missed": 2,
            "total": 14
        }
    )

    adherence_svc.get_monthly_adherence = AsyncMock(
        return_value={
            "percentage": 78.0,
            "taken": 45,
            "missed": 13,
            "total": 58
        }
    )

    # =====================
    # Mock Medication Service
    # =====================
    medication_svc = MagicMock()

    mock_med_1 = MagicMock()
    mock_med_1.id = uuid.UUID("00000000-0000-0000-0000-000000000010")
    mock_med_1.medication_name = "Metformin 500mg"
    mock_med_1.dosage = "500mg"
    mock_med_1.frequency_per_day = 2
    mock_med_1.schedules = [
        MagicMock(time_of_day="09:00 AM", dosage="500mg", is_active=True),
        MagicMock(time_of_day="09:00 PM", dosage="500mg", is_active=True),
    ]

    mock_med_2 = MagicMock()
    mock_med_2.id = uuid.UUID("00000000-0000-0000-0000-000000000011")
    mock_med_2.medication_name = "Lisinopril 10mg"
    mock_med_2.dosage = "10mg"
    mock_med_2.frequency_per_day = 1
    mock_med_2.schedules = [
        MagicMock(time_of_day="08:00 AM", dosage="10mg", is_active=True),
    ]

    medication_svc.get_active_medications = AsyncMock(
        return_value=[mock_med_1, mock_med_2]
    )

    # =====================
    # Mock Dose Log Repo
    # =====================
    dose_log_repo = MagicMock()

    sample_log = MagicMock()
    sample_log.medication_id = uuid.uuid4()
    sample_log.scheduled_time = datetime(2026, 6, 9, 8, 0, tzinfo=timezone.utc)
    sample_log.status = "missed"
    sample_log.taken_at = None

    dose_log_repo.get_user_logs = AsyncMock(return_value=[sample_log])
    dose_log_repo.create = AsyncMock(return_value=MagicMock())

    # =====================
    # Mock Side Effect Repo
    # =====================
    side_effect_repo = MagicMock()

    side_effect_repo.get_reports_by_user = AsyncMock(
        return_value=[
            MagicMock(
                symptom_description="Mild nausea after Metformin",
                severity="mild",
                created_at=datetime(2026, 6, 8, tzinfo=timezone.utc),
                recommendation="Take with food"
            )
        ]
    )
    side_effect_repo.create = AsyncMock(return_value=MagicMock())

    # =====================
    # Mock Reminder Service
    # =====================
    reminder_svc = MagicMock()

    reminder_svc.get_pending_reminders = AsyncMock(
        return_value=[
            {
                "medication_name": "Metformin 500mg",
                "scheduled_time": "09:00 AM"
            }
        ]
    )

    reminder_svc.get_upcoming_reminders = AsyncMock(
        return_value=[
            {
                "medication_name": "Metformin 500mg",
                "scheduled_time": "09:00 PM"
            },
            {
                "medication_name": "Lisinopril 10mg",
                "scheduled_time": "08:00 AM tomorrow"
            }
        ]
    )

    reminder_svc.create_followup_reminder = AsyncMock(
        return_value={"id": str(uuid.uuid4())}
    )

    reminder_svc.get_user_reminders = AsyncMock(
        return_value=[
            MagicMock(
                id=uuid.UUID("00000000-0000-0000-0000-000000000020"),
                medication_id=uuid.UUID("00000000-0000-0000-0000-000000000010"),
                scheduled_time=datetime(2026, 6, 10, 9, 0, tzinfo=timezone.utc)
            )
        ]
    )

    reminder_svc.mark_reminder_sent = AsyncMock(return_value=True)
    reminder_svc.check_and_followup = AsyncMock(return_value="Follow-up reminder created.")

    # =====================
    # Create Dependencies
    # =====================
    deps = AgentDependencies(
        user_id=user_id,
        adherence_service=adherence_svc,
        medication_service=medication_svc,
        reminder_service=reminder_svc,
        user_repo=MagicMock(),
        medication_repo=MagicMock(),
        dose_log_repo=dose_log_repo,
        side_effect_repo=side_effect_repo,
    )

    return deps


async def test():
    from app.agents.medication_agent import run_medication_agent

    user_id = uuid.UUID("00000000-0000-0000-0000-000000000001")
    deps = make_mock_deps(user_id)

    print("\n🤖 Medication Agent Interactive Test Mode")
    print("Type your questions below")
    print("Type 'exit' or 'quit' to stop\n")

    while True:
        try:
            msg = input("USER >>> ").strip()

            if msg.lower() in ["exit", "quit"]:
                print("\n👋 Exiting test mode...")
                break

            if not msg:
                print("⚠️ Please type a question")
                continue

            print("\n⏳ Thinking...\n")

            response = await run_medication_agent(
                user_message=msg,
                deps=deps
            )

            print("AGENT >>>")
            print(response)
            print("\n" + "-" * 60)

        except Exception as e:
            print("\n❌ ERROR:")
            print(type(e).__name__, str(e))
            print("-" * 60)


if __name__ == "__main__":
    asyncio.run(test())