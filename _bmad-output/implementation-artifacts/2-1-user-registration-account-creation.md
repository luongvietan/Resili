# Story 2.1: User Registration & Account Creation

Status: ready-for-dev

## Story

As a developer building with Resili,
I want to register a new account with email and password,
so that I can access the dashboard and create API keys.

## Acceptance Criteria

1. **Given** POST /api/v1/auth/register with `{"email": "user@example.com", "password": "securepass"}`, **When** the email is not already registered, **Then** HTTP 201 is returned with `{"id": "<uuid>", "email": "user@example.com", "tier": "free", "created_at": "..."}` and the user is saved in the `users` table.

2. **Given** POST /api/v1/auth/register with a duplicate email, **When** called, **Then** HTTP 400 is returned with error code `EMAIL_ALREADY_EXISTS`.

3. **Given** POST /api/v1/auth/register with a missing or empty password, **When** called, **Then** HTTP 422 is returned with Pydantic validation error.

4. **Given** the `users` table after registration, **When** reviewed, **Then** passwords are stored as bcrypt hash; no plaintext password exists anywhere in the DB.

5. **Given** a new user record is created, **When** the registration transaction commits, **Then** a corresponding `credit_balances` row is created automatically with `credits_used=0`, `monthly_limit=1000`, `tier='free'`, `reset_date` = first day of next month.

6. **Given** Alembic migration `001_create_users`, **When** `alembic upgrade head` is run, **Then** the `users` table is created with columns: `id` (UUID PK), `email` (unique, not null), `password_hash` (varchar), `tier` (varchar default 'free'), `created_at` (timestamptz).

## Tasks / Subtasks

- [ ] Tạo Alembic migration `001_create_users` (AC: 6)
  - [ ] `alembic revision --autogenerate -m "001_create_users"`
  - [ ] Verify schema: `id` UUID PK, `email` unique not null, `password_hash` varchar, `tier` varchar default 'free', `created_at` timestamptz

- [ ] Tạo SQLAlchemy model `User` (AC: 4, 6)
  - [ ] `backend/app/auth/models.py`: User model
  - [ ] Import model vào `alembic/env.py` để autogenerate detect

- [ ] Tạo Pydantic schemas (AC: 1, 3)
  - [ ] `backend/app/auth/schemas.py`: `UserRegisterRequest`, `UserResponse`
  - [ ] Validation: email format, password min length 8

- [ ] Implement auth service (AC: 1, 2, 4, 5)
  - [ ] `backend/app/auth/service.py`: `register_user(db, email, password)` function
  - [ ] Bcrypt hash password trước khi lưu
  - [ ] Raise `EmailAlreadyExistsError` nếu email trùng
  - [ ] Tạo `credit_balances` row trong cùng transaction

- [ ] Tạo API router (AC: 1, 2, 3)
  - [ ] `backend/app/api/v1/auth.py`: `POST /api/v1/auth/register`
  - [ ] Register router trong `app/api/v1/router.py`
  - [ ] Register v1 router trong `app/main.py`

- [ ] Tạo CreditBalance model (chuẩn bị cho Story 2.7)
  - [ ] `backend/app/billing/models.py`: `CreditBalance` model (placeholder, migration sẽ tạo ở Story 2.7)

- [ ] Viết tests (AC: 1, 2, 3, 4, 5)
  - [ ] `backend/tests/api/test_auth.py`

## Dev Notes

### `app/auth/models.py`

```python
import uuid
from datetime import datetime, timezone
from sqlalchemy import String, DateTime
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class User(Base):
    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False, index=True)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    tier: Mapped[str] = mapped_column(String, default="free", nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

### `app/auth/schemas.py`

```python
from pydantic import BaseModel, EmailStr, field_validator
import uuid
from datetime import datetime


class UserRegisterRequest(BaseModel):
    email: EmailStr
    password: str

    @field_validator("password")
    @classmethod
    def password_min_length(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Password must be at least 8 characters")
        return v


class UserResponse(BaseModel):
    id: uuid.UUID
    email: str
    tier: str
    created_at: datetime

    model_config = {"from_attributes": True}
```

### `app/auth/service.py`

```python
import bcrypt
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from app.auth.models import User
from app.core.errors import EmailAlreadyExistsError  # Add to errors.py
import uuid
from datetime import date


async def register_user(db: AsyncSession, email: str, password: str) -> User:
    # Hash password với bcrypt (NOT SHA-256 — bcrypt for user passwords)
    password_hash = bcrypt.hashpw(password.encode(), bcrypt.gensalt()).decode()

    user = User(email=email.lower(), password_hash=password_hash)

    async with db.begin():
        try:
            db.add(user)
            await db.flush()  # Get user.id before credit_balances insert

            # Create credit_balances atomically in same transaction (AC: 5)
            # Import here to avoid circular — or use string annotation
            from app.billing.models import CreditBalance
            from dateutil.relativedelta import relativedelta
            reset_date = (date.today().replace(day=1) + relativedelta(months=1))

            balance = CreditBalance(
                user_id=user.id,
                credits_used=0,
                monthly_limit=1000,
                tier="free",
                reset_date=reset_date,
            )
            db.add(balance)
            await db.commit()
        except IntegrityError:
            await db.rollback()
            raise EmailAlreadyExistsError()

    return user
```

**CRITICAL:** `password_hash` dùng `bcrypt` — KHÔNG phải SHA-256. SHA-256 chỉ dùng cho API keys (random strings), bcrypt dùng cho user passwords (Dec-A).

### `app/core/errors.py` — Add new error types

Thêm vào `errors.py` (từ Story 1.2):
```python
class EmailAlreadyExistsError(ResiliError):
    status_code = 400
    error_code = "EMAIL_ALREADY_EXISTS"
    message = "An account with this email already exists"
    hint = "Try logging in instead, or use a different email address"
    docs_url = "https://docs.resili.io/errors/email-already-exists"

class InvalidCredentialsError(ResiliError):
    status_code = 401
    error_code = "INVALID_CREDENTIALS"
    message = "Invalid email or password"  # Same message to prevent enumeration
    hint = "Check your email and password and try again"
    docs_url = "https://docs.resili.io/errors/invalid-credentials"
```

### `app/api/v1/auth.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth import service, schemas

router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/register", response_model=schemas.UserResponse, status_code=201)
async def register(
    body: schemas.UserRegisterRequest,
    db: AsyncSession = Depends(get_db),
):
    # Service raises EmailAlreadyExistsError → handled by global handler → Dec-D schema
    user = await service.register_user(db, body.email, body.password)
    return user
```

### `app/api/v1/router.py`

```python
from fastapi import APIRouter
from app.api.v1 import auth

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
```

### `app/main.py` — Register v1 router

```python
from app.api.v1.router import router as v1_router
app.include_router(v1_router)
```

### `app/db/session.py`

```python
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from app.core.config import settings

engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(engine, expire_on_commit=False)


async def get_db():
    async with AsyncSessionLocal() as session:
        yield session
```

**NOTE:** `DATABASE_URL` với psycopg3 phải dùng `postgresql+psycopg://` (không phải `postgresql+asyncpg://`). psycopg3 hỗ trợ async native.

### `alembic/env.py` — Import models

```python
# CRITICAL: Import ALL models để autogenerate detect
from app.auth.models import User
from app.billing.models import CreditBalance  # Cần tạo placeholder model trước
from app.db.base import Base
target_metadata = Base.metadata
```

### `backend/tests/api/test_auth.py`

```python
import pytest
from httpx import AsyncClient


async def test_register_success(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "test@example.com",
        "password": "securepass123"
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "test@example.com"
    assert data["tier"] == "free"
    assert "id" in data
    assert "password_hash" not in data  # NEVER return password_hash


async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com", "password": "securepass123"
    })
    response = await client.post("/api/v1/auth/register", json={
        "email": "dup@example.com", "password": "differentpass123"
    })
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "EMAIL_ALREADY_EXISTS"


async def test_register_short_password(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "test2@example.com", "password": "short"
    })
    assert response.status_code == 422
```

### Alembic Migration `001_create_users.py`

```python
def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column("email", sa.String, unique=True, nullable=False),
        sa.Column("password_hash", sa.String, nullable=False),
        sa.Column("tier", sa.String, nullable=False, server_default="free"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_users_email", "users", ["email"])
```

### Project Structure Notes

- `app/billing/models.py` phải tồn tại với `CreditBalance` placeholder TRƯỚC khi migration chạy (alembic env.py import nó)
- Migration `001` chỉ tạo `users` table — `credit_balances` table sẽ được tạo ở Story 2.7
- Nhưng `register_user()` service cần tạo credit_balances row → cần import model
- **Giải pháp:** Tạo `CreditBalance` SQLAlchemy model ngay (không cần migration) → migration sẽ thêm ở Story 2.7

### References

- [Source: architecture.md#Dec-A-API-Key-Format-Storage] — bcrypt for passwords, SHA-256 for API keys
- [Source: architecture.md#Naming-Patterns] — snake_case JSON, UUID IDs
- [Source: architecture.md#Communication-Patterns] — Depends() pattern
- [Source: epics.md#Story-2.1] — acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**NEW:**
- `backend/app/auth/models.py`
- `backend/app/auth/schemas.py`
- `backend/app/auth/service.py`
- `backend/app/auth/dependencies.py` (placeholder for Story 2.2+)
- `backend/app/billing/models.py` (CreditBalance placeholder model)
- `backend/app/billing/schemas.py` (placeholder)
- `backend/app/billing/service.py` (placeholder)
- `backend/app/billing/dependencies.py` (placeholder)
- `backend/app/api/v1/auth.py`
- `backend/app/api/v1/router.py`
- `backend/alembic/versions/001_create_users.py`
- `backend/tests/api/test_auth.py`

**UPDATE:**
- `backend/app/core/errors.py` — add EmailAlreadyExistsError, InvalidCredentialsError
- `backend/app/main.py` — include v1 router
- `backend/alembic/env.py` — import models
