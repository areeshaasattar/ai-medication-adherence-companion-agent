import os
import uuid
from pydantic import BaseModel, ConfigDict, PrivateAttr
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta

from agents import Agent, Runner, OpenAIChatCompletionsModel, function_tool, RunContextWrapper
from openai import AsyncOpenAI
from agents import set_tracing_disabled

from dotenv import load_dotenv

# Load .env file
load_dotenv()

set_tracing_disabled(True)

# ====================== GEMINI CLIENT ======================
client = AsyncOpenAI(
    base_url="https://generativelanguage.googleapis.com/v1beta/openai/",
    api_key=os.getenv("GEMINI_API_KEY")
)

model = OpenAIChatCompletionsModel(
    model="gemini-2.5-flash",
    openai_client=client
)

# ====================== DEPENDENCIES ======================
class AgentDependencies(BaseModel):
    model_config = ConfigDict(arbitrary_types_allowed=True)

    user_id: uuid.UUID

    adherence_service: Any
    medication_service: Any
    reminder_service: Any
    user_repo: Any
    medication_repo: Any
    dose_log_repo: Any
    side_effect_repo: Any

    # def __init__(self, **data):
    #     adherence_service = data.pop('adherence_service')
    #     medication_service = data.pop('medication_service')
    #     user_repo = data.pop('user_repo')
    #     medication_repo = data.pop('medication_repo')
    #     dose_log_repo = data.pop('dose_log_repo')
    #     side_effect_repo = data.pop('side_effect_repo')
    #     super().__init__(**data)
    #     self.adherence_service = adherence_service
    #     self.medication_service = medication_service
    #     self.user_repo = user_repo
    #     self.medication_repo = medication_repo
    #     self.dose_log_repo = dose_log_repo
    #     self.side_effect_repo = side_effect_repo


# ====================== TOOLS ======================

def detect_severity(description: str) -> str:
    severe_keywords = ["bohat zyada", "severe", "unbearable", "emergency", "worse", "hospital"]
    mild_keywords = ["thora", "mild", "halka", "slight", "little", "thodi"]
    desc_lower = description.lower()
    if any(k in desc_lower for k in severe_keywords):
        return "severe"
    if any(k in desc_lower for k in mild_keywords):
        return "mild"
    return "moderate"


@function_tool
async def get_user_adherence(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Retrieves the user's medication adherence scores and streaks."""
    deps = ctx.context
    summary = await deps.adherence_service.generate_adherence_summary(deps.user_id)
    risk = await deps.adherence_service.predict_non_adherence_risk(deps.user_id)
    return {
        "summary": summary,
        "risk_assessment": risk.model_dump() if hasattr(risk, "model_dump") else risk
    }


@function_tool
async def get_medication_history(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Retrieves active medications and recent dose logs for the user."""
    deps = ctx.context
    medications = await deps.medication_service.get_active_medications(deps.user_id)
    logs = await deps.dose_log_repo.get_user_logs(deps.user_id)
    recent_logs = sorted(logs, key=lambda x: x.scheduled_time, reverse=True)[:10]
    return {
        "active_medications": [m.model_dump() for m in medications],
        "recent_logs": [
            {
                "medication_id": str(l.medication_id),
                "scheduled_time": l.scheduled_time.isoformat(),
                "status": l.status,
                "taken_at": l.taken_at.isoformat() if l.taken_at else None
            } for l in recent_logs
        ]
    }


@function_tool
async def analyze_side_effects(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Retrieves and analyzes the user's reported side effects."""
    deps = ctx.context
    reports = await deps.side_effect_repo.get_reports_by_user(deps.user_id)
    return [
        {
            "symptom": r.symptom_description,
            "severity": r.severity,
            "created_at": r.created_at.isoformat(),
            "recommendation": r.recommendation
        } for r in reports
    ]


@function_tool
async def get_high_risk_patterns(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Detects repeated missed doses or dangerous non-adherence patterns."""
    deps = ctx.context
    trend = await deps.adherence_service.calculate_adherence_trend(deps.user_id)
    most_missed = await deps.adherence_service.get_most_missed_medication(deps.user_id)
    missed_streak = await deps.adherence_service.calculate_missed_dose_streak(deps.user_id)
    return {
        "trend": trend.model_dump() if hasattr(trend, "model_dump") else trend,
        "most_missed_medication": most_missed.model_dump() if most_missed and hasattr(most_missed, "model_dump") else most_missed,
        "current_missed_streak": missed_streak
    }

@function_tool
async def get_todays_schedule(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Fetch today's medication schedule for the current user."""
    deps = ctx.context
    try:
        medications = await deps.medication_service.get_active_medications(deps.user_id)
        if not medications:
            return "You have no active medications in your schedule."
        
        schedule_items = []
        for med in medications:
            for sched in med.schedules:
                if sched.is_active:
                    schedule_items.append(f"- {med.medication_name}: {sched.time_of_day} ({sched.dosage})")
        
        if not schedule_items:
            return "You have no medications scheduled for today."
            
        return "Your schedule for today:\n" + "\n".join(schedule_items)
    except Exception as e:
        return f"Error fetching today's schedule: {str(e)}"


@function_tool
async def get_my_medications(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Fetch all active medications for the current user."""
    deps = ctx.context
    try:
        medications = await deps.medication_service.get_active_medications(deps.user_id)
        if not medications:
            return "You don't have any active medications registered."
            
        med_list = []
        for med in medications:
            freq = ", ".join([str(s.time_of_day) for s in med.schedules])
            med_list.append(f"- {med.medication_name}: {med.dosage} ({med.frequency_per_day} times/day, at {freq})")
            
        return "Your active medications:\n" + "\n".join(med_list)
    except Exception as e:
        return f"Error fetching medications: {str(e)}"


@function_tool
async def log_dose_taken(ctx: RunContextWrapper[AgentDependencies], medication_name: str) -> str:
    """Mark a specific dose as taken right now. Use this when the user says they took their medicine."""
    deps = ctx.context
    try:
        medications = await deps.medication_service.get_active_medications(deps.user_id)
        med = next((m for m in medications if m.medication_name.lower() == medication_name.lower()), None)
        
        if not med:
            return f"I couldn't find a medication named '{medication_name}'. Please tell me the exact name of the medication you took."
            
        await deps.dose_log_repo.create({
            "user_id": deps.user_id,
            "medication_id": med.id,
            "scheduled_time": datetime.now(timezone.utc),
            "taken_at": datetime.now(timezone.utc),
            "status": "taken"
        })
        
        return f"Great! I've logged that you took your {med.medication_name}. Keep it up!"
    except Exception as e:
        return f"Error logging dose: {str(e)}"


@function_tool
async def log_dose_missed(ctx: RunContextWrapper[AgentDependencies], medication_name: str, reason: Optional[str] = None) -> str:
    """Mark a specific dose as missed. Use this when the user says they missed or forgot a dose."""
    deps = ctx.context
    try:
        medications = await deps.medication_service.get_active_medications(deps.user_id)
        med = next((m for m in medications if m.medication_name.lower() == medication_name.lower()), None)
        
        if not med:
            return f"I couldn't find a medication named '{medication_name}'."
            
        await deps.dose_log_repo.create({
            "user_id": deps.user_id,
            "medication_id": med.id,
            "scheduled_time": datetime.now(timezone.utc),
            "status": "missed",
            "notes": reason
        })
        
        return f"I've noted that you missed your dose of {med.medication_name}. It's okay, let's try to stay on track. Is there anything making it hard to take your medication?"
    except Exception as e:
        return f"Error logging missed dose: {str(e)}"


@function_tool
async def get_adherence_summary(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Get adherence statistics for the user (weekly score, streaks)."""
    deps = ctx.context
    try:
        summary = await deps.adherence_service.generate_adherence_summary(deps.user_id)
        
        scores = summary.get("adherence_scores", {})
        streaks = summary.get("streaks", {})
        
        weekly = scores.get("weekly", 0.0)
        current_streak = streaks.get("current_streak", 0)
        
        response = f"Your adherence summary:\n- Weekly Score: {weekly}%\n- Current Streak: {current_streak} days\n\n"
        
        if weekly >= 90:
            response += "Excellent! You're doing a fantastic job staying on top of your health! 🌟"
        elif weekly >= 70:
            response += "Good job! You're mostly on track. Let's see if we can reach 90% next week! 👍"
        else:
            response += "It looks like you've missed a few doses recently. Don't worry, every day is a new chance to improve. How can I help you stay on track? 🤝"
            
        return response
    except Exception as e:
        return f"Error fetching adherence summary: {str(e)}"


@function_tool
async def report_side_effect(ctx: RunContextWrapper[AgentDependencies], medication_name: str, description: str) -> str:
    """Save a side effect report from the user. Severity is auto-detected from description."""
    deps = ctx.context
    try:
        medications = await deps.medication_service.get_active_medications(deps.user_id)
        med = next((m for m in medications if m.medication_name.lower() == medication_name.lower()), None)
        
        if not med:
            return f"I couldn't find a medication named '{medication_name}'."
            
        severity = detect_severity(description)
        
        await deps.side_effect_repo.create({
            "user_id": deps.user_id,
            "medication_id": med.id,
            "symptom_description": description,
            "severity": severity,
            "recommendation": "Consult your doctor."
        })
        
        response = f"I've recorded that you're experiencing {description} (Auto-detected Severity: {severity.capitalize()}) with {med.medication_name}."
        
        if severity == "severe":
            response += "\n\n⚠️ PLEASE APNE DOCTOR SE ABHI CONTACT KARO! This symptom sounds serious."
        else:
            response += " Please consult your doctor if symptoms persist or if you have concerns."
            
        return response
    except Exception as e:
        return f"Error reporting side effect: {str(e)}"


@function_tool
async def get_adherence_streak(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Get the user's current medication adherence streak (consecutive days of 100% adherence)."""
    deps = ctx.context
    try:
        streak = await deps.adherence_service.get_streak(deps.user_id)
        
        if streak == 0:
            return "No worries, today is a fresh start! I'm here to help you."
        elif 1 <= streak <= 3:
            return f"Good start, keep it up! You have a {streak} day streak."
        elif 4 <= streak <= 6:
            return f"Fantastic! {streak} day streak! Keep up the great work!"
        else:
            return f"Amazing! {streak} day streak, well done! You're an inspiration! 🌟"
    except Exception as e:
        return f"Error fetching streak: {str(e)}"


@function_tool
async def get_weekly_report(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Get a detailed weekly adherence report including percentage and streak."""
    deps = ctx.context
    try:
        adherence = await deps.adherence_service.get_weekly_adherence(deps.user_id)
        streak = await deps.adherence_service.get_streak(deps.user_id)
        
        percentage = adherence.get("percentage", 0.0)
        taken = adherence.get("taken", 0)
        total = adherence.get("total", 0)
        
        report = (
            f"Here is your weekly medication report:\n"
            f"- Adherence Score: {percentage}%\n"
            f"- Doses Taken: {taken}/{total}\n"
            f"- Current Streak: {streak} days\n\n"
        )
        
        if percentage >= 90:
            report += "Outstanding performance this week! Your consistency is paying off. 🚀"
        elif percentage >= 70:
            report += "You're doing well! Just a few more doses and you'll hit that 90% mark. You've got this! 💪"
        else:
            report += "This week was a bit tough, but don't get discouraged. Let's focus on making next week better! I'll remind you of your upcoming doses. 🤝"
            
        return report
    except Exception as e:
        return f"Error generating weekly report: {str(e)}"


@function_tool
async def get_pending_reminders(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Fetch all medication reminders that are pending and were due by now."""
    deps = ctx.context
    try:
        pending = await deps.reminder_service.get_pending_reminders(deps.user_id)
        if not pending:
            return "Abhi koi pending reminder nahi hai. You are all caught up!"
            
        items = [f"📅 {p['medication_name']} - {p['scheduled_time']} lena tha" for p in pending]
        return "Ye reminders pending hain:\n" + "\n".join(items)
    except Exception as e:
        return f"Error fetching pending reminders: {str(e)}"


@function_tool
async def get_upcoming_reminders(ctx: RunContextWrapper[AgentDependencies]) -> str:
    """Fetch all medication reminders scheduled for the next 24 hours."""
    deps = ctx.context
    try:
        upcoming = await deps.reminder_service.get_upcoming_reminders(deps.user_id)
        if not upcoming:
            return "No reminders scheduled for the next 24 hours."
            
        items = [f"- {u['medication_name']} at {u['scheduled_time']}" for u in upcoming]
        return "⏰ Upcoming in the next 24 hours:\n" + "\n".join(items)
    except Exception as e:
        return f"Error fetching upcoming reminders: {str(e)}"


@function_tool
async def snooze_reminder(ctx: RunContextWrapper[AgentDependencies], medication_name: str, snooze_minutes: int = 30) -> str:
    """Snooze a reminder by creating a follow-up reminder some minutes later."""
    deps = ctx.context
    try:
        medications = await deps.medication_service.get_active_medications(deps.user_id)
        med = next((m for m in medications if m.medication_name.lower() == medication_name.lower()), None)
        
        if not med:
            return f"I couldn't find a medication named '{medication_name}'."
            
        reminders = await deps.reminder_service.get_user_reminders(deps.user_id)
        relevant = [r for r in reminders if r.medication_id == med.id]
        if not relevant:
            return f"No previous reminders found for {med.medication_name} to snooze."
            
        latest_reminder = max(relevant, key=lambda r: r.scheduled_time)
        
        await deps.reminder_service.create_followup_reminder(
            user_id=deps.user_id,
            medication_id=med.id,
            original_reminder_id=latest_reminder.id,
            delay_minutes=snooze_minutes
        )
        
        return f"Got it! Your {med.medication_name} reminder has been snoozed for {snooze_minutes} minutes."
    except Exception as e:
        return f"Error snoozing reminder: {str(e)}"


# ====================== GUARDRAILS ======================
EMERGENCY_KEYWORDS = [
    "chest pain", "can't breathe", "difficulty breathing", "heart attack",
    "stroke", "unconscious", "overdose", "suicide", "kill myself",
    "emergency", "ambulance", "dying", "severe pain", "seizure"
]

DANGEROUS_KEYWORDS = [
    "double dose", "skip all doses", "stop all medication",
    "take extra", "more than prescribed", "ignore doctor"
]

def check_for_emergency(message: str) -> bool:
    msg = message.lower()
    return any(kw in msg for kw in EMERGENCY_KEYWORDS)

def check_for_dangerous_request(message: str) -> bool:
    msg = message.lower()
    return any(kw in msg for kw in DANGEROUS_KEYWORDS)


# ====================== SYSTEM PROMPT ======================
MEDICATION_AGENT_SYSTEM_PROMPT = """You are a caring and knowledgeable Medication Adherence Companion. 
Your role is to help patients track their medications, understand their adherence patterns, 
and provide guidance on side effects and treatment compliance.

You have access to the following tools:
- get_user_adherence: Check adherence scores and risk levels
- get_medication_history: View active medications and recent dose logs  
- analyze_side_effects: Review reported side effects
- get_high_risk_patterns: Detect missed dose patterns

Guidelines:
1. Always be empathetic and supportive - patients may feel guilty about missed doses
2. Never diagnose conditions or prescribe medications
3. Never tell a patient to stop or change their prescribed medication
4. For side effects, always recommend consulting their doctor
5. Celebrate good adherence to encourage positive behavior
6. If adherence is poor, help identify patterns (time of day, day of week) to improve
7. Keep responses clear, concise, and actionable
8. Always remind patients that this is support only - their doctor makes final decisions

Safety: If a patient reports an emergency or dangerous symptoms, immediately direct them to call emergency services."""


# ====================== AGENT ======================
medication_agent = Agent(
    name="Medication Adherence Companion",
    instructions=MEDICATION_AGENT_SYSTEM_PROMPT,
    model=model,
    tools=[
        get_user_adherence,
        get_medication_history,
        analyze_side_effects,
        get_high_risk_patterns,
        get_todays_schedule,
        get_my_medications,
        log_dose_taken,
        log_dose_missed,
        get_adherence_summary,
        report_side_effect,
        get_adherence_streak,
        get_weekly_report,
        get_pending_reminders,
        get_upcoming_reminders,
        snooze_reminder,
    ]
)


# ====================== MAIN RUNNER ======================
async def run_medication_agent(
    user_message: str,
    deps: AgentDependencies,
    conversation_history: Optional[List[Dict]] = None
) -> str:

    # Safety guardrails
    if check_for_emergency(user_message):
        return (
            "⚠️ This appears to be a medical emergency. "
            "Please contact your doctor immediately or go to the nearest hospital. "
            "If urgent, call your local emergency number (e.g., 115). "
            "Do not change or adjust your medications on your own."
        )


    if check_for_dangerous_request(user_message):
        return (
            "I cannot advise you to take more or stop your prescribed medications. "
            "Please consult your doctor before making any changes to your treatment."
        )

    # Build input with history if available
    if conversation_history:
        history_text = "\n".join([
            f"{msg['role'].capitalize()}: {msg['content']}"
            for msg in conversation_history[-6:]
        ])
        print("GEMINI KEY:", os.getenv("GEMINI_API_KEY"))
        input_text = f"Conversation so far:\n{history_text}\n\nUser: {user_message}"
    else:
        input_text = user_message

    result = await Runner.run(
        starting_agent=medication_agent,
        input=input_text,
        context=deps,  
    )

    return result.final_output