from fastapi import APIRouter, Depends
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import schemas, service
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(
    body: schemas.UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await service.register_user(db, body.email, body.password)
    return user


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(
    body: LoginRequest,
    db: AsyncSession = Depends(get_db),
):
    token = await service.login_user(db, body.email, body.password)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=schemas.UserResponse)
async def me(user: User = Depends(get_current_user)):
    return user
