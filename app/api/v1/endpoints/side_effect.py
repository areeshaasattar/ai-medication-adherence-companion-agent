from typing import List
from fastapi import APIRouter, Depends, status, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.api.dependencies.auth import get_current_user
from app.schemas.side_effect_report import SideEffectReportCreate, SideEffectReportResponse
from app.repositories.side_effect_repository import SideEffectRepository
from app.models.user import User

router = APIRouter()

@router.post("/", response_model=SideEffectReportResponse, status_code=status.HTTP_201_CREATED)
async def report_side_effect(
    report_in: SideEffectReportCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    Submit a new side effect report.
    """
    if report_in.user_id != current_user.id and current_user.role != "admin":
        raise HTTPException(status_code=403, detail="Not enough permissions")
        
    repo = SideEffectRepository(db)
    return await repo.create(report_in.model_dump())

@router.get("/", response_model=List[SideEffectReportResponse])
async def list_side_effects(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """
    List all side effect reports for the current user.
    """
    repo = SideEffectRepository(db)
    return await repo.get_reports_by_user(current_user.id)
