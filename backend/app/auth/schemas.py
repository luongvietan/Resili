import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, field_validator


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        if len(v) > 72:
            raise ValueError("Password must be no more than 72 characters")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    tier: str
    created_at: datetime

    model_config = {"from_attributes": True}
