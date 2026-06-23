from datetime import datetime, timedelta, timezone
from fastapi import HTTPException, status
from app.repositories.auth_repository import AuthRepository
from app.schemas.auth import RegisterRequest, LoginRequest, ChangePasswordRequest
from app.schemas.token import TokenResponse
from app.utils.password import hash_password, verify_password
from app.utils.jwt import create_access_token, create_refresh_token, verify_token
from app.models.user import User

class AuthService:
    def __init__(self, auth_repo: AuthRepository):
        self.auth_repo = auth_repo

    async def register_user(self, register_in: RegisterRequest) -> User:
        existing_user = await self.auth_repo.get_user_by_email(register_in.email)
        if existing_user:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="User with this email already exists"
            )
        
        user_data = register_in.model_dump(exclude={"password"})
        user_data["hashed_password"] = hash_password(register_in.password)
        
        return await self.auth_repo.create_user(user_data)

    async def authenticate_user(self, login_in: LoginRequest) -> TokenResponse:
        user = await self.auth_repo.get_user_by_email(login_in.email)
        if not user or not verify_password(login_in.password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Incorrect email or password",
                headers={"WWW-Authenticate": "Bearer"},
            )
        
        if not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive"
            )

        access_token = create_access_token(user.id, user.role)
        refresh_token_str = create_refresh_token(user.id)
        
        # Save refresh token to DB
        expires_at = datetime.now(timezone.utc) + timedelta(days=7)
        await self.auth_repo.create_refresh_token({
            "user_id": user.id,
            "token": refresh_token_str,
            "expires_at": expires_at
        })

        return TokenResponse(
            access_token=access_token,
            refresh_token=refresh_token_str
        )

    async def refresh_access_token(self, refresh_token_str: str) -> TokenResponse:
        payload = verify_token(refresh_token_str)
        if not payload:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        db_token = await self.auth_repo.get_refresh_token(refresh_token_str)
        if not db_token or db_token.is_revoked or db_token.expires_at < datetime.now(timezone.utc):
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid or expired refresh token"
            )

        user = await self.auth_repo.get_user_by_id(db_token.user_id)

        if not user or not user.is_active:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="User is inactive or not found"
            )

        new_access_token = create_access_token(user.id, user.role)

        return TokenResponse(
            access_token=new_access_token,
            refresh_token=refresh_token_str
        )

    async def logout_user(self, refresh_token_str: str) -> None:
        db_token = await self.auth_repo.get_refresh_token(refresh_token_str)
        if db_token:
            await self.auth_repo.revoke_refresh_token(db_token.id)

    async def change_password(self, user: User, change_in: ChangePasswordRequest) -> None:
        if not verify_password(change_in.old_password, user.hashed_password):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Incorrect old password"
            )
        
        await self.auth_repo.update_user(user, {
            "hashed_password": hash_password(change_in.new_password)
        })
