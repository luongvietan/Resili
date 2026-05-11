# Story 2.5: API Request Authentication Middleware

Status: ready-for-dev

## Story

As the Resili API,
I want to authenticate every scraping request via API key in the Authorization header,
so that only authorized users can access scraping endpoints.

## Acceptance Criteria

1. **Given** POST /api/v1/scrape/fetch with `Authorization: Bearer rsl_<valid-active-key>`, **When** the key is valid, **Then** the request proceeds; the authenticated `User` object is available via `Depends(get_current_user)`.

2. **Given** a scraping endpoint called without an `Authorization` header, **When** called, **Then** HTTP 401 is returned with error code `MISSING_API_KEY` and hint to add the `Authorization: Bearer <key>` header.

3. **Given** a scraping endpoint called with a malformed key (not matching `rsl_` format), **When** called, **Then** HTTP 401 is returned with error code `INVALID_API_KEY`.

4. **Given** Redis is available and a valid API key is looked up, **When** the same key is used within 5 minutes, **Then** subsequent lookups are served from Redis cache (TTL 5 min) without hitting PostgreSQL.

5. **Given** all scraping route handlers (`scrape.py`), **When** reviewed, **Then** no handler manually verifies the API key — all authentication flows through `Depends(get_current_user)`.

## Tasks / Subtasks

- [ ] Implement API key authentication dependency (AC: 1, 2, 3)
  - [ ] `app/auth/dependencies.py`: add `get_current_user_from_api_key()` dependency
  - [ ] Parse `Authorization: Bearer rsl_*` header
  - [ ] Hash key with SHA-256, lookup in Redis then DB
  - [ ] Raise appropriate errors

- [ ] Implement Redis caching for API key lookup (AC: 4)
  - [ ] `app/core/redis.py`: Redis client factory
  - [ ] Cache API key → user_id mapping (TTL 5 min)
  - [ ] Invalidate cache on revoke

- [ ] Create placeholder scrape router (AC: 5)
  - [ ] `app/api/v1/scrape.py`: placeholder router with auth dependency
  - [ ] Include in `app/api/v1/router.py`

- [ ] Add error types (AC: 2, 3)
  - [ ] `app/core/errors.py`: `MissingApiKeyError`, `InvalidApiKeyError`

- [ ] Viết tests

## Dev Notes

### Two Auth Dependencies — CRITICAL DISTINCTION

Project có HAI loại authentication:
1. **JWT (Bearer token)** — `get_current_user()` từ Story 2.2 — dùng cho dashboard endpoints (`/keys`, `/usage`, `/billing`)
2. **API Key (Bearer rsl_key)** — `get_current_user_from_api_key()` từ story này — dùng cho scraping endpoints (`/scrape/fetch`, `/scrape/dynamic`)

Cả hai đều dùng `Authorization: Bearer` header, nhưng phân biệt qua prefix `rsl_`:

```python
async def get_current_user_from_api_key(
    credentials: HTTPAuthorizationCredentials | None = Depends(bearer_scheme),
    db: AsyncSession = Depends(get_db),
    redis: Redis = Depends(get_redis),
) -> User:
    if not credentials:
        raise MissingApiKeyError()

    token = credentials.credentials

    # API keys start with rsl_ — JWTs don't
    if not token.startswith("rsl_"):
        raise InvalidApiKeyError()

    key_hash = hash_api_key(token)  # SHA-256

    # 1. Check Redis cache (TTL 5 min)
    cache_key = f"api_key:{key_hash}"
    cached_user_id = await redis.get(cache_key)

    if cached_user_id:
        user_id = uuid.UUID(cached_user_id.decode())
        result = await db.execute(select(User).where(User.id == user_id))
        user = result.scalar_one_or_none()
        if user:
            return user

    # 2. DB lookup
    result = await db.execute(
        select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
    )
    api_key = result.scalar_one_or_none()

    if not api_key:
        raise InvalidApiKeyError()

    # 3. Cache the user_id (TTL 300s = 5 min)
    await redis.setex(cache_key, 300, str(api_key.user_id))

    result = await db.execute(select(User).where(User.id == api_key.user_id))
    return result.scalar_one()
```

### `app/core/redis.py`

```python
import redis.asyncio as aioredis
from app.core.config import settings

_redis_client = None

async def get_redis():
    global _redis_client
    if _redis_client is None:
        _redis_client = aioredis.from_url(settings.REDIS_URL, decode_responses=False)
    return _redis_client
```

### `app/core/errors.py` — Add API key errors

```python
class MissingApiKeyError(ResiliError):
    status_code = 401
    error_code = "MISSING_API_KEY"
    message = "API key is required for scraping endpoints"
    hint = "Add Authorization: Bearer rsl_<your_key> header"
    docs_url = "https://docs.resili.io/errors/missing-api-key"

class InvalidApiKeyError(ResiliError):
    status_code = 401
    error_code = "INVALID_API_KEY"
    message = "The provided API key is invalid or has been revoked"
    hint = "Check your API key in the dashboard or generate a new one"
    docs_url = "https://docs.resili.io/errors/invalid-api-key"
```

### Redis Cache Invalidation on Revoke

Trong `revoke_api_key()` service (Story 2.4), add cache invalidation:
```python
async def revoke_api_key(db, key_id, user_id):
    # ... existing code ...
    api_key.is_active = False
    await db.commit()

    # Invalidate Redis cache
    redis = await get_redis()
    cache_key = f"api_key:{api_key.key_hash}"
    await redis.delete(cache_key)
```

### Scrape Placeholder Router (AC: 5)

```python
# app/api/v1/scrape.py
from fastapi import APIRouter, Depends
from app.auth.dependencies import get_current_user_from_api_key
from app.auth.models import User

router = APIRouter(prefix="/scrape", tags=["scraping"])


@router.post("/fetch")
async def fetch_page(
    user: User = Depends(get_current_user_from_api_key),  # API key auth
    # body and credit check will be added in Epic 3
):
    return {"message": "Scraping endpoint — implementation in Epic 3"}


@router.post("/dynamic")
async def fetch_dynamic_page(
    user: User = Depends(get_current_user_from_api_key),  # API key auth
):
    return {"message": "Dynamic scraping endpoint — implementation in Epic 3"}
```

**CRITICAL:** Scraping routes dùng `get_current_user_from_api_key` (API key auth). Dashboard routes dùng `get_current_user` (JWT auth). Không trộn lẫn.

### Settings — Add REDIS_URL to config

`settings.REDIS_URL` đã có từ Story 1.1. Đảm bảo `app/core/config.py` có field này.

### References

- [Source: architecture.md#Dec-A-API-Key-Format-Storage] — SHA-256 lookup
- [Source: architecture.md#Dec-G-Credit-Accounting-Atomicity] — Redis cache pattern (TTL 5min for API keys)
- [Source: architecture.md#Communication-Patterns] — Depends() pattern mandatory
- [Source: epics.md#Story-2.5] — acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/auth/dependencies.py` — add get_current_user_from_api_key
- `backend/app/auth/service.py` — add Redis cache invalidation on revoke
- `backend/app/core/errors.py` — add MissingApiKeyError, InvalidApiKeyError
- `backend/app/api/v1/router.py` — include scrape router

**NEW:**
- `backend/app/core/redis.py`
- `backend/app/api/v1/scrape.py` (placeholder)
- `backend/tests/api/test_api_key_auth.py`
