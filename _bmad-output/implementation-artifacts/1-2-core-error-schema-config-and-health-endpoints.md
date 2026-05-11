# Story 1.2: Core Error Schema, Config, and Health Endpoints

Status: ready-for-dev

## Story

As a developer,
I want a standardized error schema and health check endpoints in place from day one,
so that all API consumers have a consistent error format and deployment platforms can verify liveness.

## Acceptance Criteria

1. **Given** any API error at any endpoint, **When** the error response is returned, **Then** it follows Dec-D schema exactly: `{"error": {"code": "SCREAMING_SNAKE_CASE", "message": "...", "hint": "...", "docs_url": "https://docs.resili.io/errors/..."}}`.

2. **Given** `app/core/config.py`, **When** reviewed, **Then** all configuration is read via a `pydantic-settings` `Settings` class; no `os.environ.get()` calls exist outside this file.

3. **Given** `app/core/errors.py`, **When** reviewed, **Then** it contains: a custom exception base class, at minimum `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `SSRFBlockedError`, `CreditsExhaustedError`; global FastAPI exception handlers that format all custom exceptions using the Dec-D schema.

4. **Given** GET /health, **When** called, **Then** HTTP 200 is returned with `{"status": "ok"}`.

5. **Given** GET /api/v1/, **When** called, **Then** HTTP 200 is returned with `{"version": "v1", "docs": "/docs"}`.

6. **Given** the Alembic configuration (`alembic.ini`, `alembic/env.py`), **When** `alembic upgrade head` is run with no migrations yet, **Then** it succeeds without error (infrastructure ready for future migrations).

## Tasks / Subtasks

- [ ] Implement `app/core/errors.py` — custom exceptions + global handlers (AC: 1, 3)
  - [ ] Tạo `ResiliError` base exception class
  - [ ] Tạo `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `SSRFBlockedError`, `CreditsExhaustedError`
  - [ ] Tạo FastAPI exception handlers → format thành Dec-D schema
  - [ ] Register handlers trong `app/main.py`

- [ ] Verify `app/core/config.py` (AC: 2)
  - [ ] Đảm bảo `Settings` class đầy đủ theo Story 1.1
  - [ ] Kiểm tra không có `os.environ.get()` nào ngoài file này

- [ ] Implement health và root endpoints trong `app/main.py` (AC: 4, 5)
  - [ ] `GET /health` → `{"status": "ok"}`
  - [ ] `GET /api/v1/` → `{"version": "v1", "docs": "/docs"}`
  - [ ] Add `X-Powered-By: Resili (built on Scrapling — BSD License)` response header middleware (NFR-11)

- [ ] Cấu hình Alembic hoạt động (AC: 6)
  - [ ] Verify `alembic/env.py` đọc DATABASE_URL từ `settings`
  - [ ] Chạy `alembic upgrade head` thành công (không có migration → OK)
  - [ ] Tạo `backend/app/db/base.py` với `DeclarativeBase`

- [ ] Viết tests cho error schema và endpoints (AC: 1, 4, 5)
  - [ ] `backend/tests/api/test_health.py`: test `/health` và `/api/v1/`
  - [ ] `backend/tests/test_errors.py`: test Dec-D schema với custom exceptions

## Dev Notes

### `app/core/errors.py` — Implementation chi tiết

```python
from fastapi import Request, FastAPI
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException
from typing import Optional
import httpx


class ResiliError(Exception):
    """Base exception for all Resili custom errors."""
    status_code: int = 500
    error_code: str = "INTERNAL_SERVER_ERROR"
    message: str = "An unexpected error occurred"
    hint: str = "Please try again or contact support"
    docs_url: str = "https://docs.resili.io/errors/internal-server-error"

    def __init__(self, message: Optional[str] = None, hint: Optional[str] = None):
        self.message = message or self.__class__.message
        self.hint = hint or self.__class__.hint

    def to_dict(self) -> dict:
        return {
            "error": {
                "code": self.error_code,
                "message": self.message,
                "hint": self.hint,
                "docs_url": self.docs_url,
            }
        }


class NotFoundError(ResiliError):
    status_code = 404
    error_code = "NOT_FOUND"
    message = "The requested resource was not found"
    hint = "Check the resource ID or URL"
    docs_url = "https://docs.resili.io/errors/not-found"


class UnauthorizedError(ResiliError):
    status_code = 401
    error_code = "UNAUTHORIZED"
    message = "Authentication required"
    hint = "Add Authorization: Bearer <key> header"
    docs_url = "https://docs.resili.io/errors/unauthorized"


class ForbiddenError(ResiliError):
    status_code = 403
    error_code = "FORBIDDEN"
    message = "You do not have permission to perform this action"
    hint = "Check your account permissions or upgrade tier"
    docs_url = "https://docs.resili.io/errors/forbidden"


class SSRFBlockedError(ResiliError):
    status_code = 400
    error_code = "SSRF_BLOCKED"
    message = "The target URL is blocked for security reasons"
    hint = "Only public URLs are allowed. Private IPs and localhost are blocked"
    docs_url = "https://docs.resili.io/errors/ssrf-blocked"


class CreditsExhaustedError(ResiliError):
    status_code = 429
    error_code = "CREDITS_EXHAUSTED"
    message = "Your credits for this month are exhausted"
    hint = "Upgrade to Pro or wait for your credits to reset"
    docs_url = "https://docs.resili.io/errors/credits-exhausted"


# — Exception Handlers —

def _error_response(exc: ResiliError) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content=exc.to_dict(),
    )


async def resili_error_handler(request: Request, exc: ResiliError) -> JSONResponse:
    return _error_response(exc)


async def validation_error_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    return JSONResponse(
        status_code=422,
        content={
            "error": {
                "code": "VALIDATION_ERROR",
                "message": "Request validation failed",
                "hint": str(exc.errors()),
                "docs_url": "https://docs.resili.io/errors/validation-error",
            }
        },
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": "HTTP_ERROR",
                "message": exc.detail,
                "hint": "See HTTP status code for context",
                "docs_url": "https://docs.resili.io/errors",
            }
        },
    )


def register_exception_handlers(app: FastAPI) -> None:
    """Register all exception handlers — call in app factory."""
    app.add_exception_handler(ResiliError, resili_error_handler)
    app.add_exception_handler(RequestValidationError, validation_error_handler)
    app.add_exception_handler(StarletteHTTPException, http_exception_handler)
```

**RULE:** Toàn bộ service layer phải `raise ResiliError subclass` — không bao giờ `return {"error": ...}`.

### `app/main.py` — Updated với middleware + error handlers

```python
from fastapi import FastAPI, Request, Response
from app.core.config import settings
from app.core.errors import register_exception_handlers

def create_app() -> FastAPI:
    app = FastAPI(title="Resili API", version="0.1.0", docs_url="/docs")

    # Register error handlers
    register_exception_handlers(app)

    # BSD Attribution header middleware (NFR-11)
    @app.middleware("http")
    async def add_attribution_header(request: Request, call_next):
        response = await call_next(request)
        response.headers["X-Powered-By"] = "Resili (built on Scrapling — BSD License)"
        return response

    return app

app = create_app()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/v1/")
async def root():
    return {"version": "v1", "docs": "/docs"}
```

### `backend/app/db/base.py`

```python
from sqlalchemy.orm import DeclarativeBase
import uuid
from sqlalchemy import String
from sqlalchemy.orm import mapped_column, Mapped

class Base(DeclarativeBase):
    pass
```

### `alembic/env.py` — Critical configuration

```python
from alembic import context
from sqlalchemy import engine_from_config, pool
from app.core.config import settings
from app.db.base import Base  # import all models here when they exist

# CRITICAL: Read from settings, NOT os.environ
config = context.config
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)

target_metadata = Base.metadata
```

### `backend/tests/conftest.py` cơ bản

```python
import pytest
from httpx import AsyncClient, ASGITransport
from app.main import app

@pytest.fixture
async def client():
    async with AsyncClient(
        transport=ASGITransport(app=app),
        base_url="http://test"
    ) as client:
        yield client
```

### Dec-D Schema — MANDATORY format cho mọi error

```json
{
  "error": {
    "code": "SCREAMING_SNAKE_CASE",
    "message": "Human-readable description of what happened",
    "hint": "Suggested next action for the developer",
    "docs_url": "https://docs.resili.io/errors/<code-lowercase>"
  }
}
```

**KHÔNG** dùng format khác. **KHÔNG** bọc trong `{"data": ..., "success": false}`.

### X-Powered-By Header (NFR-11)

Middleware phải add header này cho **MỌI** response: `X-Powered-By: Resili (built on Scrapling — BSD License)`. Implement là middleware, không phải per-route.

### Project Structure Notes

- File `app/core/errors.py` là centralized — tất cả custom exceptions đều định nghĩa ở đây
- `register_exception_handlers()` được gọi trong `create_app()`, không phải trực tiếp trong module scope
- Thứ tự handler quan trọng: `ResiliError` handler TRƯỚC generic HTTP handler

### References

- [Source: architecture.md#Dec-D-Error-Response-Schema] — Dec-D JSON format
- [Source: architecture.md#Error-Handling-exception-based] — exception pattern
- [Source: epics.md#Story-1.2] — acceptance criteria
- [Source: architecture.md#Enforcement-Guidelines] — anti-patterns to avoid
- [Source: architecture.md#Gap-Analysis-Results] — X-Powered-By header middleware

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/main.py` — add middleware + error handler registration
- `backend/app/db/base.py` — add DeclarativeBase
- `backend/alembic/env.py` — configure with settings.DATABASE_URL

**NEW:**
- `backend/app/core/errors.py`
- `backend/tests/api/__init__.py`
- `backend/tests/api/test_health.py`
- `backend/tests/test_errors.py`
