import uuid

from fastapi import Depends
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import ExpiredSignatureError, JWTError
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.auth.models import User
from app.core.errors import InvalidTokenError, MissingAuthTokenError, TokenExpiredError, UnauthorizedError
from app.core.security import decode_access_token
from app.db.session import get_db

bearer_scheme = HTTPBearer(auto_error=False)


async def get_current_user(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
) -> User:
    if not credentials:
        raise MissingAuthTokenError()

    try:
        payload = decode_access_token(credentials.credentials)
    except ExpiredSignatureError:
        raise TokenExpiredError()
    except JWTError:
        raise InvalidTokenError()

    user_id_str = payload.get("user_id")
    if not user_id_str:
        raise InvalidTokenError()

    try:
        user_uuid = uuid.UUID(user_id_str)
    except ValueError:
        raise InvalidTokenError()

    result = await db.execute(select(User).where(User.id == user_uuid))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError()

    return user
