import uuid
from datetime import datetime
from pydantic import EmailStr, Field
from app.schemas.base import BaseSchema

class UserBase(BaseSchema):
    email: EmailStr
    full_name: str | None = Field(None, max_length=255)

class UserCreate(UserBase):
    pass

class UserUpdate(BaseSchema):
    email: EmailStr | None = None
    full_name: str | None = Field(None, max_length=255)

class UserResponse(UserBase):
    id: uuid.UUID
    created_at: datetime
    updated_at: datetime
