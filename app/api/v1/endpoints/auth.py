from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.schemas.auth import RegisterRequest, LoginRequest, ChangePasswordRequest
from app.schemas.token import TokenResponse, RefreshTokenRequest
from app.schemas.user import UserResponse
from app.services.auth_service import AuthService
from app.repositories.auth_repository import AuthRepository
from app.api.dependencies.auth import get_current_user
from app.models.user import User

router = APIRouter(prefix="/auth", tags=["Authentication"])

@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
async def register(register_in: RegisterRequest, db: AsyncSession = Depends(get_db)):
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    user = await auth_service.register_user(register_in)
    return user

@router.post("/login", response_model=TokenResponse)
async def login(login_in: LoginRequest, db: AsyncSession = Depends(get_db)):
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    return await auth_service.authenticate_user(login_in)

@router.post("/refresh", response_model=TokenResponse)
async def refresh_token(refresh_in: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    return await auth_service.refresh_access_token(refresh_in.refresh_token)

@router.post("/logout", status_code=status.HTTP_204_NO_CONTENT)
async def logout(refresh_in: RefreshTokenRequest, db: AsyncSession = Depends(get_db)):
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    await auth_service.logout_user(refresh_in.refresh_token)

@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user

@router.post("/change-password", status_code=status.HTTP_204_NO_CONTENT)
async def change_password(
    change_in: ChangePasswordRequest, 
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db)
):
    auth_repo = AuthRepository(db)
    auth_service = AuthService(auth_repo)
    await auth_service.change_password(current_user, change_in)
