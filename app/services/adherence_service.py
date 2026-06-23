from uuid import UUID
from datetime import datetime, timedelta, timezone
from typing import Dict, Any, Sequence, List
from fastapi import HTTPException, status
from collections import Counter

from app.repositories.dose_log_repository import DoseLogRepository
from app.repositories.medication_repository import MedicationRepository
from app.schemas.dose_log import DoseStatus
from app.schemas.adherence import (
    AdherenceTrend,
    MedicationInsight,
    AdherenceRisk,
    RiskLevel
)

class AdherenceService:
    def __init__(
        self,
        dose_log_repo: DoseLogRepository,
        medication_repo: MedicationRepository
    ):
        self.dose_log_repo = dose_log_repo
        self.medication_repo = medication_repo

    async def _calculate_percentage(self, user_id: UUID, start_date: datetime, end_date: datetime) -> float:
        logs = await self.dose_log_repo.get_logs_between_dates(user_id, start_date, end_date)
        if not logs:
            return 100.0  
        
        total_scheduled = len(logs)
        taken_count = sum(1 for log in logs if log.status == DoseStatus.TAKEN)
        
        return (taken_count / total_scheduled) * 100

    async def calculate_daily_adherence(self, user_id: UUID) -> float:
        now = datetime.now(timezone.utc)
        start_of_day = now.replace(hour=0, minute=0, second=0, microsecond=0)
        return await self._calculate_percentage(user_id, start_of_day, now)

    async def calculate_weekly_adherence(self, user_id: UUID) -> float:
        now = datetime.now(timezone.utc)
        start_of_week = now - timedelta(days=7)
        return await self._calculate_percentage(user_id, start_of_week, now)

    async def calculate_monthly_adherence(self, user_id: UUID) -> float:
        now = datetime.now(timezone.utc)
        start_of_month = now - timedelta(days=30)
        return await self._calculate_percentage(user_id, start_of_month, now)

    async def calculate_overall_adherence(self, user_id: UUID) -> float:
        logs = await self.dose_log_repo.get_user_logs(user_id)
        if not logs:
            return 100.0
        
        total_scheduled = len(logs)
        taken_count = sum(1 for log in logs if log.status == DoseStatus.TAKEN)
        
        return (taken_count / total_scheduled) * 100

    async def calculate_current_streak(self, user_id: UUID) -> int:
        logs = await self.dose_log_repo.get_user_logs(user_id)
        if not logs:
            return 0
        
        # Sort by scheduled time descending
        sorted_logs = sorted(logs, key=lambda x: x.scheduled_time, reverse=True)
        
        streak = 0
        now = datetime.now(timezone.utc)
        for log in sorted_logs:
            # Skip future logs
            if log.scheduled_time > now:
                continue
            if log.status == DoseStatus.TAKEN:
                streak += 1
            elif log.status == DoseStatus.MISSED or log.status == DoseStatus.SKIPPED:
                break
        return streak

    async def calculate_missed_dose_streak(self, user_id: UUID) -> int:
        logs = await self.dose_log_repo.get_user_logs(user_id)
        if not logs:
            return 0
        
        sorted_logs = sorted(logs, key=lambda x: x.scheduled_time, reverse=True)
        
        streak = 0
        now = datetime.now(timezone.utc)
        for log in sorted_logs:
            if log.scheduled_time > now:
                continue
            if log.status == DoseStatus.MISSED:
                streak += 1
            elif log.status == DoseStatus.TAKEN:
                break
        return streak

    async def calculate_adherence_trend(self, user_id: UUID) -> AdherenceTrend:
        now = datetime.now(timezone.utc)
        last_7_days_start = now - timedelta(days=7)
        prev_7_days_start = now - timedelta(days=14)
        
        current_score = await self._calculate_percentage(user_id, last_7_days_start, now)
        prev_score = await self._calculate_percentage(user_id, prev_7_days_start, last_7_days_start)
        
        diff = current_score - prev_score
        direction = "stable"
        if diff > 2:
            direction = "up"
        elif diff < -2:
            direction = "down"
            
        return AdherenceTrend(
            current_period_score=round(current_score, 2),
            previous_period_score=round(prev_score, 2),
            trend_percentage=round(diff, 2),
            direction=direction
        )

    async def get_most_missed_medication(self, user_id: UUID) -> MedicationInsight | None:
        insights = await self.generate_medication_insights(user_id)
        if not insights:
            return None
        return max(insights, key=lambda x: x.missed_count)

    async def generate_medication_insights(self, user_id: UUID) -> List[MedicationInsight]:
        medications = await self.medication_repo.get_user_medications(user_id)
        logs = await self.dose_log_repo.get_user_logs(user_id)
        
        insights = []
        for med in medications:
            med_logs = [l for l in logs if l.medication_id == med.id]
            if not med_logs:
                continue
                
            total = len(med_logs)
            taken = sum(1 for l in med_logs if l.status == DoseStatus.TAKEN)
            missed = sum(1 for l in med_logs if l.status == DoseStatus.MISSED)
            score = (taken / total) * 100
            
            recommendation = "Great job! Keep it up."
            if score < 80:
                recommendation = f"Consider setting a reminder for {med.medication_name}."
            if score < 50:
                recommendation = f"High priority: Talk to your doctor about difficulties taking {med.medication_name}."
                
            insights.append(MedicationInsight(
                medication_id=med.id,
                medication_name=med.medication_name,
                adherence_score=round(score, 2),
                missed_count=missed,
                recommendation=recommendation
            ))
        return insights

    async def predict_non_adherence_risk(self, user_id: UUID) -> AdherenceRisk:
        score = await self.calculate_weekly_adherence(user_id)
        missed_streak = await self.calculate_missed_dose_streak(user_id)
        
        logs = await self.dose_log_repo.get_user_logs(user_id)
        risk_factors = []
        
        # Factor 1: Adherence below 80%
        if score < 80:
            risk_factors.append(f"Weekly adherence is low ({round(score, 1)}%)")
            
        # Factor 2: Missed dose streak > 3
        if missed_streak > 3:
            risk_factors.append(f"Consecutive missed doses: {missed_streak}")
            
        # Factor 3: No activity for 7 days
        if logs:
            last_activity = max(l.created_at for l in logs if l.status == DoseStatus.TAKEN) if any(l.status == DoseStatus.TAKEN for l in logs) else None
            if last_activity and (datetime.now(timezone.utc) - last_activity).days >= 7:
                risk_factors.append("No medication activity recorded in the last 7 days")
        elif not logs:
             risk_factors.append("No activity recorded yet")

        # Risk Classification
        level = RiskLevel.LOW
        if len(risk_factors) >= 2 or score < 60:
            level = RiskLevel.HIGH
        elif len(risk_factors) == 1:
            level = RiskLevel.MEDIUM
            
        return AdherenceRisk(
            risk_level=level,
            risk_factors=risk_factors,
            predicted_at=datetime.now(timezone.utc)
        )

    async def calculate_adherence_by_time_of_day(self, user_id: UUID) -> Dict[str, float]:
        logs = await self.dose_log_repo.get_user_logs(user_id)
        
        buckets = {"morning": [], "afternoon": [], "evening": []}
        for log in logs:
            hour = log.scheduled_time.hour
            if 6 <= hour < 12: buckets["morning"].append(log)
            elif 12 <= hour < 18: buckets["afternoon"].append(log)
            else: buckets["evening"].append(log)
            
        def calc_score(items):
            if not items: return 100.0
            return (sum(1 for i in items if i.status == DoseStatus.TAKEN) / len(items)) * 100
            
        return {k: round(calc_score(v), 2) for k, v in buckets.items()}

    async def generate_adherence_summary(self, user_id: UUID) -> Dict[str, Any]:
        medications = await self.medication_repo.get_user_medications(user_id)
        if not medications:
            return {
                "message": "No medications found for this user.",
                "adherence_scores": {
                    "daily": 0.0,
                    "weekly": 0.0,
                    "monthly": 0.0,
                    "overall": 0.0
                },
                "streaks": {
                    "current_streak": 0,
                    "missed_dose_streak": 0
                }
            }

        daily = await self.calculate_daily_adherence(user_id)
        weekly = await self.calculate_weekly_adherence(user_id)
        monthly = await self.calculate_monthly_adherence(user_id)
        overall = await self.calculate_overall_adherence(user_id)
        current_streak = await self.calculate_current_streak(user_id)
        missed_streak = await self.calculate_missed_dose_streak(user_id)

        return {
            "user_id": user_id,
            "total_medications": len(medications),
            "adherence_scores": {
                "daily": round(daily, 2),
                "weekly": round(weekly, 2),
                "monthly": round(monthly, 2),
                "overall": round(overall, 2)
            },
            "streaks": {
                "current_streak": current_streak,
                "missed_dose_streak": missed_streak
            },
            "timestamp": datetime.now(timezone.utc)
        }

    async def get_weekly_adherence(self, user_id: UUID | str) -> dict:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=7)
        logs = await self.dose_log_repo.get_logs_between_dates(uid, start_date, now)
        
        total = len(logs)
        taken = sum(1 for log in logs if log.status == DoseStatus.TAKEN)
        missed = sum(1 for log in logs if log.status == DoseStatus.MISSED)
        percentage = (taken / total * 100) if total > 0 else 100.0
        
        return {
            "percentage": round(percentage, 1),
            "taken": taken,
            "missed": missed,
            "total": total
        }

    async def get_monthly_adherence(self, user_id: UUID | str) -> dict:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        now = datetime.now(timezone.utc)
        start_date = now - timedelta(days=30)
        logs = await self.dose_log_repo.get_logs_between_dates(uid, start_date, now)
        
        total = len(logs)
        taken = sum(1 for log in logs if log.status == DoseStatus.TAKEN)
        missed = sum(1 for log in logs if log.status == DoseStatus.MISSED)
        percentage = (taken / total * 100) if total > 0 else 100.0
        
        return {
            "percentage": round(percentage, 1),
            "taken": taken,
            "missed": missed,
            "total": total
        }

    async def get_streak(self, user_id: UUID | str) -> int:
        uid = UUID(user_id) if isinstance(user_id, str) else user_id
        logs = await self.dose_log_repo.get_user_logs(uid)
        if not logs:
            return 0
            
        from collections import defaultdict
        daily_logs = defaultdict(list)
        now = datetime.now(timezone.utc)
        for log in logs:
            if log.scheduled_time <= now:
                daily_logs[log.scheduled_time.date()].append(log)
        
        if not daily_logs:
            return 0
            
        sorted_dates = sorted(daily_logs.keys(), reverse=True)
        streak = 0
        today = now.date()
        
        for d in sorted_dates:
            day_logs = daily_logs[d]
            all_taken = all(l.status == DoseStatus.TAKEN for l in day_logs)
            
            if all_taken:
                streak += 1
            else:
                if d == today:
                    if any(l.status in [DoseStatus.MISSED, DoseStatus.SKIPPED] for l in day_logs):
                        break
                    else:
                        continue
                else:
                    break
        return streak
