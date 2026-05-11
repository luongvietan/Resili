# Story 2.3: API Key Generation

Status: ready-for-dev

## Story

As an authenticated developer,
I want to generate a new API key for my account,
so that I can authenticate my scraping API requests.

## Acceptance Criteria

1. **Given** POST /api/v1/keys with a valid JWT, **When** called, **Then** HTTP 201 is returned with `{"id": "<uuid>", "key": "rsl_<url-safe-base64-32-bytes>", "created_at": "..."}` — this is the **only** time the plaintext key is returned.

2. **Given** the `api_keys` table after key creation, **When** reviewed, **Then** only the SHA-256 hash of the key is stored; the plaintext key does not exist in the database (NFR-07).

3. **Given** Alembic migration `002_create_api_keys`, **When** `alembic upgrade head` is run, **Then** the `api_keys` table is created with: `id` (UUID PK), `user_id` (UUID FK → users), `key_hash` (varchar, indexed), `name` (varchar nullable), `is_active` (bool default true), `created_at` (timestamptz). Index: `ix_api_keys_key_hash`, `ix_api_keys_user_id`.

4. **Given** the generated key format, **When** inspected, **Then** it starts with `rsl_` and the remainder is URL-safe base64 encoding of 32 cryptographically random bytes.

5. **Given** calling POST /api/v1/keys multiple times for the same user, **When** each call succeeds, **Then** each returns a unique key; a user may have multiple active keys.

## Tasks / Subtasks

- [ ] Tạo Alembic migration `002_create_api_keys` (AC: 3)
  - [ ] Schema: `id` UUID PK, `user_id` UUID FK, `key_hash` varchar indexed, `name` varchar nullable, `is_active` bool default true, `created_at` timestamptz
  - [ ] Indexes: `ix_api_keys_key_hash`, `ix_api_keys_user_id`

- [ ] Tạo `ApiKey` SQLAlchemy model (AC: 2, 3)
  - [ ] `app/auth/models.py`: add `ApiKey` model

- [ ] Implement key generation functions (AC: 1, 4)
  - [ ] `app/core/security.py`: `generate_api_key()` → `rsl_` + 32 random bytes URL-safe base64
  - [ ] `app/core/security.py`: `hash_api_key(key)` → SHA-256 hex digest

- [ ] Implement create_key service (AC: 1, 2, 5)
  - [ ] `app/auth/service.py`: `create_api_key(db, user_id, name=None)` → returns (ApiKey, plaintext_key)

- [ ] Tạo API schemas và router (AC: 1)
  - [ ] `app/auth/schemas.py`: `ApiKeyCreateRequest`, `ApiKeyCreateResponse`
  - [ ] `app/api/v1/keys.py`: `POST /api/v1/keys`

- [ ] Viết tests (AC: 1, 2, 4, 5)

## Dev Notes

### API Key Format (Dec-A) — CRITICAL

```
rsl_ + base64url(32 random bytes)
```

Example: `rsl_aB3xK9mPqR7sT2uV5wY8zA1bC4dE6fG` (48 chars total after rsl_)

Implementation:
```python
import secrets
import base64
import hashlib

def generate_api_key() -> str:
    """Generate rsl_ prefixed URL-safe base64 key from 32 random bytes."""
    random_bytes = secrets.token_bytes(32)
    encoded = base64.urlsafe_b64encode(random_bytes).decode().rstrip("=")
    return f"rsl_{encoded}"

def hash_api_key(key: str) -> str:
    """SHA-256 hash of API key for storage. NEVER store plaintext."""
    return hashlib.sha256(key.encode()).hexdigest()
```

**SHA-256 for API keys** (NOT bcrypt) — karena API keys are random 256-bit values, không phải user-chosen passwords. SHA-256 lookup đủ nhanh và ổn. bcrypt quá chậm cho per-request lookup (Dec-A rationale).

### `app/auth/models.py` — Add ApiKey

```python
class ApiKey(Base):
    __tablename__ = "api_keys"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # ix_api_keys_user_id
    )
    key_hash: Mapped[str] = mapped_column(String, nullable=False, index=True)  # ix_api_keys_key_hash
    name: Mapped[str | None] = mapped_column(String, nullable=True)
    is_active: Mapped[bool] = mapped_column(default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

### `app/auth/schemas.py` — API Key schemas

```python
class ApiKeyCreateRequest(BaseModel):
    name: str | None = None  # Optional label

class ApiKeyCreateResponse(BaseModel):
    id: uuid.UUID
    key: str  # Plaintext — returned ONCE only
    created_at: datetime
    model_config = {"from_attributes": True}
```

### `app/auth/service.py` — create_api_key

```python
from app.core.security import generate_api_key, hash_api_key

async def create_api_key(
    db: AsyncSession,
    user_id: uuid.UUID,
    name: str | None = None
) -> tuple[ApiKey, str]:
    """Returns (ApiKey model, plaintext_key). Plaintext key shown ONCE."""
    plaintext_key = generate_api_key()
    key_hash = hash_api_key(plaintext_key)

    api_key = ApiKey(user_id=user_id, key_hash=key_hash, name=name)
    db.add(api_key)
    await db.commit()
    await db.refresh(api_key)

    return api_key, plaintext_key  # Caller uses plaintext_key for response, then discards
```

### `app/api/v1/keys.py`

```python
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.db.session import get_db
from app.auth.dependencies import get_current_user
from app.auth.models import User
from app.auth import service, schemas

router = APIRouter(prefix="/keys", tags=["keys"])


@router.post("", status_code=201)
async def create_key(
    body: schemas.ApiKeyCreateRequest,
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    api_key, plaintext_key = await service.create_api_key(db, user.id, body.name)
    return {
        "id": api_key.id,
        "key": plaintext_key,  # ONLY time plaintext is returned
        "created_at": api_key.created_at,
    }
```

### `app/api/v1/router.py` — Add keys router

```python
from app.api.v1 import auth, keys

router = APIRouter(prefix="/api/v1")
router.include_router(auth.router)
router.include_router(keys.router)
```

### Alembic Migration `002_create_api_keys.py`

```python
def upgrade() -> None:
    op.create_table(
        "api_keys",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("key_hash", sa.String, nullable=False),
        sa.Column("name", sa.String, nullable=True),
        sa.Column("is_active", sa.Boolean, nullable=False, server_default="true"),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_api_keys_key_hash", "api_keys", ["key_hash"])
    op.create_index("ix_api_keys_user_id", "api_keys", ["user_id"])
```

### Test — Verify plaintext not stored

```python
async def test_key_not_stored_plaintext(client, db):
    # Create key via API
    response = await client.post(
        "/api/v1/keys",
        headers={"Authorization": f"Bearer {jwt_token}"},
        json={}
    )
    assert response.status_code == 201
    plaintext_key = response.json()["key"]
    
    # Verify DB stores only hash
    result = await db.execute(select(ApiKey))
    api_key = result.scalar_one()
    assert api_key.key_hash != plaintext_key  # hash ≠ plaintext
    assert api_key.key_hash == hashlib.sha256(plaintext_key.encode()).hexdigest()
```

### References

- [Source: architecture.md#Dec-A-API-Key-Format-Storage] — format + SHA-256 hashing
- [Source: epics.md#Story-2.3] — acceptance criteria
- [Source: architecture.md#Enforcement-Guidelines] — NFR-07

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/auth/models.py` — add ApiKey model
- `backend/app/auth/schemas.py` — add ApiKey schemas
- `backend/app/auth/service.py` — add create_api_key
- `backend/app/core/security.py` — add generate_api_key, hash_api_key
- `backend/app/api/v1/router.py` — include keys router

**NEW:**
- `backend/app/api/v1/keys.py`
- `backend/alembic/versions/002_create_api_keys.py`
- `backend/tests/api/test_keys.py`
