# Story 2.2: User Login & JWT Authentication

Status: done

## Story

As a registered developer,
I want to log in and receive a JWT token,
so that I can make authenticated requests to dashboard endpoints.

## Acceptance Criteria

1. **Given** POST /api/v1/auth/login with valid `{"email": "...", "password": "..."}`, **When** called, **Then** HTTP 200 is returned with `{"access_token": "<jwt>", "token_type": "bearer"}`.

2. **Given** POST /api/v1/auth/login with a wrong password, **When** called, **Then** HTTP 401 is returned with error code `INVALID_CREDENTIALS` (same message for wrong password and unknown email to prevent enumeration).

3. **Given** a valid JWT, **When** decoded, **Then** it contains `user_id` (UUID) and `exp` claims; token expires in 24 hours.

4. **Given** a protected dashboard endpoint (e.g. GET /api/v1/keys) called without a JWT, **When** called, **Then** HTTP 401 is returned with error code `MISSING_AUTH_TOKEN`.

5. **Given** a protected dashboard endpoint called with an expired JWT, **When** called, **Then** HTTP 401 is returned with error code `TOKEN_EXPIRED`.

## Tasks / Subtasks

- [x] Implement login endpoint (AC: 1, 2)
  - [x] `app/auth/service.py`: `login_user(db, email, password)` → verify bcrypt hash, return JWT
  - [x] `app/api/v1/auth.py`: `POST /api/v1/auth/login`
  - [x] Same error message for wrong email and wrong password (prevent enumeration)

- [x] Implement JWT creation/validation (AC: 3)
  - [x] `app/core/security.py`: `create_access_token(user_id)`, `decode_access_token(token)`
  - [x] Token: contains `user_id` (str UUID) + `exp` claim, expires 24h
  - [x] Use `python-jose[cryptography]` with HS256 algorithm
  - [x] Sign with `settings.SECRET_KEY`

- [x] Implement auth dependency (AC: 4, 5)
  - [x] `app/auth/dependencies.py`: `get_current_user()` dependency
  - [x] Parse `Authorization: Bearer <token>` header
  - [x] Raise `MissingAuthTokenError` if no header
  - [x] Raise `TokenExpiredError` if token expired
  - [x] Raise `InvalidTokenError` if token invalid

- [x] Viết tests (AC: 1, 2, 3, 4, 5)

## Dev Notes

### `app/core/security.py`

```python
from datetime import datetime, timedelta, timezone
from jose import jwt, JWTError, ExpiredSignatureError
from app.core.config import settings
import uuid


ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_HOURS = 24


def create_access_token(user_id: uuid.UUID) -> str:
    expire = datetime.now(timezone.utc) + timedelta(hours=ACCESS_TOKEN_EXPIRE_HOURS)
    payload = {
        "user_id": str(user_id),
        "exp": expire,
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def decode_access_token(token: str) -> dict:
    """Returns payload dict. Raises JWTError or ExpiredSignatureError."""
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
```

### `app/auth/service.py` — Add login function

```python
import bcrypt
from jose import JWTError, ExpiredSignatureError
from sqlalchemy import select
from app.auth.models import User
from app.core.security import create_access_token
from app.core.errors import InvalidCredentialsError


async def login_user(db: AsyncSession, email: str, password: str) -> str:
    """Returns JWT access token. Raises InvalidCredentialsError for any auth failure."""
    result = await db.execute(select(User).where(User.email == email.lower()))
    user = result.scalar_one_or_none()

    # Same error for unknown email OR wrong password (prevent enumeration — AC: 2)
    if not user or not bcrypt.checkpw(password.encode(), user.password_hash.encode()):
        raise InvalidCredentialsError()

    return create_access_token(user.id)
```

### `app/auth/dependencies.py`

```python
from fastapi import Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from jose import JWTError, ExpiredSignatureError
from app.db.session import get_db
from app.auth.models import User
from app.core.security import decode_access_token
from app.core.errors import (
    MissingAuthTokenError, TokenExpiredError, InvalidTokenError, UnauthorizedError
)
import uuid

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

    result = await db.execute(select(User).where(User.id == uuid.UUID(user_id_str)))
    user = result.scalar_one_or_none()
    if not user:
        raise UnauthorizedError()

    return user
```

### `app/api/v1/auth.py` — Add login endpoint

```python
class LoginRequest(BaseModel):
    email: EmailStr
    password: str

class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


@router.post("/login", response_model=TokenResponse)
async def login(body: LoginRequest, db: AsyncSession = Depends(get_db)):
    token = await service.login_user(db, body.email, body.password)
    return TokenResponse(access_token=token)
```

### `app/core/errors.py` — Add JWT errors

```python
class MissingAuthTokenError(ResiliError):
    status_code = 401
    error_code = "MISSING_AUTH_TOKEN"
    message = "Authentication token is required"
    hint = "Add Authorization: Bearer <token> header"
    docs_url = "https://docs.resili.io/errors/missing-auth-token"

class TokenExpiredError(ResiliError):
    status_code = 401
    error_code = "TOKEN_EXPIRED"
    message = "Authentication token has expired"
    hint = "Log in again to get a new token"
    docs_url = "https://docs.resili.io/errors/token-expired"

class InvalidTokenError(ResiliError):
    status_code = 401
    error_code = "INVALID_TOKEN"
    message = "Authentication token is invalid"
    hint = "Ensure the token was issued by Resili and has not been tampered with"
    docs_url = "https://docs.resili.io/errors/invalid-token"
```

### Settings — Add SECRET_KEY validation

`app/core/config.py`: SECRET_KEY đã có từ Story 1.1. Nếu SECRET_KEY không đủ entropy trong production, jwt signing sẽ yếu — nhưng validation này nằm ngoài scope của story này.

### JWT JWT Claims Structure

Token payload:
```json
{
  "user_id": "550e8400-e29b-41d4-a716-446655440000",
  "exp": 1734567890
}
```

**KHÔNG** thêm `email`, `tier`, hay bất kỳ PII nào vào JWT — chỉ `user_id` và `exp`. User data được fetch từ DB trong `get_current_user()`.

### Dashboard Endpoints Pattern (AC: 4)

Bất kỳ dashboard endpoint nào cần auth phải dùng `Depends(get_current_user)`:
```python
@router.get("/keys")
async def list_keys(
    user: User = Depends(get_current_user),  # ← auth enforced
    db: AsyncSession = Depends(get_db),
):
    ...
```

**KHÔNG** verify token thủ công trong handler body.

### References

- [Source: architecture.md#Authentication-Security] — Dec-A, Dec-B
- [Source: architecture.md#Communication-Patterns] — Depends() pattern
- [Source: epics.md#Story-2.2] — acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- Implemented `app/core/security.py` với `create_access_token` và `decode_access_token` dùng python-jose HS256
- Thêm 3 JWT error classes: `MissingAuthTokenError`, `TokenExpiredError`, `InvalidTokenError` vào `errors.py`
- Thêm `login_user()` vào `app/auth/service.py` — verify bcrypt hash, prevent email enumeration
- Thêm `POST /api/v1/auth/login` và `GET /api/v1/auth/me` (protected) vào `app/api/v1/auth.py`
- Tạo `app/auth/dependencies.py` với `get_current_user` FastAPI dependency — xử lý đủ 3 lỗi auth
- Viết 9 tests bao phủ toàn bộ AC 1-5 (79/79 tests passed, zero regressions)

### File List

**UPDATE:**
- `backend/app/auth/service.py` — add login_user
- `backend/app/api/v1/auth.py` — add login endpoint + /me protected endpoint
- `backend/app/core/errors.py` — add MissingAuthTokenError, TokenExpiredError, InvalidTokenError

**NEW:**
- `backend/app/core/security.py` — JWT create/decode functions
- `backend/app/auth/dependencies.py` — get_current_user dependency
- `backend/tests/api/test_login.py` — 9 tests covering all ACs

### Change Log

- 2026-05-11: Story 2.2 implemented — User Login & JWT Authentication complete. Login endpoint, JWT security module, auth dependency, and full test coverage added.

### Review Findings

- [x] [Review][Patch] Timing attack vulnerability in `login_user` [`backend/app/auth/service.py`]
- [x] [Review][Patch] Potential 500 error on invalid UUID string in `get_current_user` [`backend/app/auth/dependencies.py`]
- [x] [Review][Defer] Database performance bottleneck in `get_current_user` [`backend/app/auth/dependencies.py`] — deferred, pre-existing
