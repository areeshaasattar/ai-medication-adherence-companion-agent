from fastapi import FastAPI
from contextlib import asynccontextmanager
from app.core.config import settings
from app.api.v1.api import api_router
from app.core.database import init_db
from app.core.exceptions import AdherenceException, adherence_exception_handler
from app.services.scheduler_service import start_scheduler

@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    scheduler = start_scheduler()
    yield
    scheduler.shutdown()

app = FastAPI(
    title=settings.PROJECT_NAME,
    openapi_url=f"{settings.API_V1_STR}/openapi.json",
    lifespan=lifespan
)
app.add_exception_handler(AdherenceException, adherence_exception_handler)

app.include_router(api_router, prefix=settings.API_V1_STR)