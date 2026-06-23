# AI Medication Adherence Companion Agent

A production-ready FastAPI backend designed to transform medication management through AI-driven insights, automated scheduling, and proactive adherence monitoring.

---

## 🚀 Key Features

### 🤖 Intelligent Health Agent
A sophisticated AI agent powered by **OpenAI Agents SDK** and **Gemini 2.5 Flash** that acts as a personal health companion.
- **Natural Language Processing**: Chat about your medications in plain English.
- **12+ Specialized Tools**:
    - **Real-time Schedule**: "What medications do I need to take today?"
    - **Dose Logging**: "I just took my Metformin."
    - **Adherence Reports**: "Give me my weekly report."
    - **Streak Tracking**: "What is my current streak?"
    - **Smart Snooze**: "I can't take it right now, remind me in 30 minutes."
    - **Side Effect Reporting**: Auto-detects severity and provides medical warnings.

### 📅 Smart Medication Management
- **Auto-Schedule Generation**: Automatically creates precise time slots (e.g., Twice Daily → 09:00, 21:00) when adding medications.
- **Complex Scheduling**: Supports varying dosages, frequencies, and start/end dates.
- **Automated Reminders**: Background tasks generate and track reminders.

### 📊 Advanced Adherence Analytics
- **Multi-Level Scoring**: Daily, weekly, monthly, and overall adherence percentages.
- **Streak Calculation**: Monitors consecutive days of 100% compliance.
- **Risk Assessment**: AI-driven detection of non-adherence patterns and high-risk behavior.

### 🔒 Enterprise-Grade Foundation
- **Secure Auth**: JWT-based authentication with refresh token rotation.
- **Async Architecture**: Fully asynchronous database operations with SQLAlchemy 2.0.
- **Database Migrations**: Managed via Alembic for reliable schema evolution.

---

## 🏗 Architecture & Tech Stack

- **Framework**: [FastAPI](https://fastapi.tiangolo.com/) (Asynchronous Python)
- **AI Engine**: [OpenAI Agents SDK](https://github.com/openai/openai-agents-python) + Gemini 2.5 Flash
- **Database**: [PostgreSQL](https://www.postgresql.org/) (Production) / SQLite (Dev) via [SQLAlchemy 2.0](https://www.sqlalchemy.org/)
- **Migrations**: [Alembic](https://alembic.sqlalchemy.org/)
- **Validation**: [Pydantic v2](https://docs.pydantic.dev/latest/)
- **Task Scheduling**: [APScheduler](https://apscheduler.readthedocs.io/) (for reminders and missed dose detection)

### Directory Structure
```text
app/
├── agents/         # AI Agent logic, tools, and guardrails
├── api/            # API v1 Endpoints (Auth, Meds, Doses, etc.)
├── core/           # Config, Security, and Database setup
├── models/         # SQLAlchemy 2.0 Database models
├── repositories/   # Data Access Layer (CRUD)
├── services/       # Business Logic (Adherence, Scheduling, Reminders)
└── schemas/        # Pydantic v2 data schemas
```

---

## 🛠 Setup & Installation

### Prerequisites
- Python 3.10+
- `pip` and `virtualenv`

### Installation Steps
1. **Clone & Setup Environment**:
   ```bash
   git clone <repo-url>
   cd ai-medication-adherence-companion-agent
   python -m venv venv
   source venv/bin/activate  # Windows: venv\Scripts\activate
   pip install -r requirements.txt
   ```

2. **Configuration**:
   Create a `.env` file in the root directory:
   ```env
   DATABASE_URL=sqlite+aiosqlite:///./sql_app.db
   SECRET_KEY=your_super_secret_key
   GEMINI_API_KEY=your_gemini_api_key
   ```

3. **Initialize Database**:
   ```bash
   # Run alembic migrations
   alembic upgrade head
   # OR use the setup script
   python scripts/setup_db.py
   ```

4. **Launch Application**:
   ```bash
   uvicorn app.main:app --reload
   ```

---

## 📡 API Endpoints Summary

### 🔐 Authentication
- `POST /api/v1/auth/register` - Register
- `POST /api/v1/auth/login` - Login
- `POST /api/v1/auth/refresh` - Refresh Token
- `POST /api/v1/auth/logout` - Logout
- `GET /api/v1/auth/me` - Get Me
- `POST /api/v1/auth/change-password` - Change Password

### 💊 Medications
- `GET /api/v1/medications/` - List Medications
- `POST /api/v1/medications/` - Create Medication
- `GET /api/v1/medications/{id}` - Get Medication
- `PATCH /api/v1/medications/{id}` - Update Medication
- `DELETE /api/v1/medications/{id}` - Delete Medication
- `GET /api/v1/medications/{medication_id}/schedule` - Get Medication Schedule
- `POST /api/v1/medications/{medication_id}/schedule` - Create Medication Schedule
- `PUT /api/v1/medications/{medication_id}/schedule/{schedule_id}` - Update Medication Schedule

### 📈 Dose Tracking
- `GET /api/v1/doses/` - List Dose Logs
- `POST /api/v1/doses/` - Log Dose
- `GET /api/v1/doses/medication/{medication_id}` - List Medication Logs

### 📊 Analytics
- `GET /api/v1/adherence/summary` - Get Adherence Summary
- `GET /api/v1/adherence/analytics` - Get Adherence Analytics

### 🤢 Side Effects
- `GET /api/v1/side-effects/` - List Side Effects
- `POST /api/v1/side-effects/` - Report Side Effect

### 💬 AI Agent
- `POST /api/v1/agent/chat` - Chat With Agent

### ⏰ Reminders
- `GET /api/v1/reminders/reminders/` - List User Reminders
- `POST /api/v1/reminders/reminders/` - Create Reminder
- `GET /api/v1/reminders/reminders/{reminder_id}` - Get Reminder
- `PATCH /api/v1/reminders/reminders/{reminder_id}` - Update Reminder
- `DELETE /api/v1/reminders/reminders/{reminder_id}` - Delete Reminder
- `GET /api/v1/reminders/reminders/stats` - Get Reminder Stats

### 📅 Schedules
- `GET /api/v1/schedules/` - Get User Schedules
- `POST /api/v1/schedules/` - Create Schedule
- `GET /api/v1/schedules/{schedule_id}` - Get Schedule
- `PATCH /api/v1/schedules/{schedule_id}` - Update Schedule
- `DELETE /api/v1/schedules/{schedule_id}` - Delete Schedule


---

## 🛡 Security & Guardrails

The agent includes strict safety protocols:
- **Emergency Detection**: Detects symptoms such as chest pain or difficulty breathing and redirects the user to emergency services.
- **Dangerous Request Blocking**: Prevents advice on overdosing or stopping prescribed treatments without doctor guidance.
- **Side Effect Severity**: High-severity reports trigger an immediate doctor consultation warning.

---

## 📄 License
This project is licensed under the MIT License - see the LICENSE file for details.