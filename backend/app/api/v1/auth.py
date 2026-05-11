from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth import schemas, service
from app.db.session import get_db

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(
    body: schemas.UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    user = await service.register_user(db, body.email, body.password)
    return user
