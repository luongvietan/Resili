# Story 3.1: Credit Balance & Usage Events DB Setup

Status: ready-for-dev

## Story

As the Resili billing system,
I want database tables for credit balances and usage events,
so that credit tracking and usage history can be stored with proper atomicity guarantees.

## Acceptance Criteria

1. **Given** Alembic migration `004_create_usage_events`, **When** `alembic upgrade head` is run, **Then** the `usage_events` table is created with: `id` (UUID PK), `user_id` (UUID FK), `endpoint_type` (varchar: 'fetcher' | 'dynamic'), `credits_used` (int), `url_hash` (varchar — SHA-256 of original URL), `status` (varchar: 'success' | 'error'), `created_at` (timestamptz). Indexes: `ix_usage_events_user_id`, `ix_usage_events_created_at`.

2. **Given** the `usage_events` table schema, **When** reviewed, **Then** there is NO column for raw URL — only `url_hash` (NFR-09 compliance).

3. **Given** an APScheduler job configured in `app/main.py` startup event, **When** the app is running, **Then** a daily scheduled job prunes `usage_events` rows where `created_at < NOW() - INTERVAL '90 days'` (NFR-09).

## Tasks / Subtasks

- [ ] Tạo Alembic migration `004_create_usage_events` (AC: 1, 2)
  - [ ] Schema: `id`, `user_id`, `endpoint_type`, `credits_used`, `url_hash`, `status`, `created_at`
  - [ ] NO `url` column — only `url_hash`
  - [ ] Indexes: `ix_usage_events_user_id`, `ix_usage_events_created_at`

- [ ] Finalize `UsageEvent` SQLAlchemy model (AC: 1, 2)
  - [ ] `app/billing/models.py`: complete `UsageEvent` model

- [ ] Implement APScheduler retention job (AC: 3)
  - [ ] Add `apscheduler` to `requirements.txt`
  - [ ] `app/main.py`: `@app.on_event("startup")` register daily prune job

- [ ] Viết tests (AC: 1, 2, 3)

## Dev Notes

### `app/billing/models.py` — Complete UsageEvent Model

```python
class UsageEvent(Base):
    __tablename__ = "usage_events"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True  # ix_usage_events_user_id
    )
    endpoint_type: Mapped[str] = mapped_column(String, nullable=False)  # 'fetcher' | 'dynamic'
    credits_used: Mapped[int] = mapped_column(Integer, nullable=False)
    url_hash: Mapped[str] = mapped_column(String, nullable=False)  # SHA-256 of URL — NOT raw URL
    status: Mapped[str] = mapped_column(String, nullable=False)  # 'success' | 'error'
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
        index=True  # ix_usage_events_created_at
    )
    # NOTE: NO url column — NFR-09 privacy compliance
```

**CRITICAL:** URL phải được SHA-256 hash trước khi lưu. NEVER lưu URL gốc.

### Alembic Migration `004_create_usage_events.py`

```python
def upgrade() -> None:
    op.create_table(
        "usage_events",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("endpoint_type", sa.String, nullable=False),
        sa.Column("credits_used", sa.Integer, nullable=False),
        sa.Column("url_hash", sa.String, nullable=False),
        sa.Column("status", sa.String, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )
    op.create_index("ix_usage_events_user_id", "usage_events", ["user_id"])
    op.create_index("ix_usage_events_created_at", "usage_events", ["created_at"])
```

### APScheduler Retention Job (AC: 3)

```python
# app/main.py — Add to create_app() or as startup event

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlalchemy import text

scheduler = AsyncIOScheduler()

async def prune_usage_events():
    """Delete usage_events older than 90 days — NFR-09."""
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("DELETE FROM usage_events WHERE created_at < NOW() - INTERVAL '90 days'")
        )
        await db.commit()

@app.on_event("startup")
async def startup_event():
    # Run daily at 2AM UTC
    scheduler.add_job(
        prune_usage_events,
        trigger=CronTrigger(hour=2, minute=0),
        id="prune_usage_events",
        replace_existing=True,
    )
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    scheduler.shutdown()
```

**Note:** `@app.on_event("startup")` là deprecated trong FastAPI — dùng `lifespan` context manager ở FastAPI 0.95+:

```python
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    scheduler.start()
    yield
    # Shutdown
    scheduler.shutdown()

app = FastAPI(..., lifespan=lifespan)
```

### URL Hashing Helper

```python
# app/core/security.py — add
import hashlib

def hash_url(url: str) -> str:
    """SHA-256 hash of URL for privacy-compliant storage (NFR-09)."""
    return hashlib.sha256(url.encode()).hexdigest()
```

Usage trong billing service:
```python
url_hash = hash_url(original_url)  # Store this, NOT the original URL
```

### Append-Only Design (Dec-H)

`usage_events` là append-only table:
- **KHÔNG** update existing rows
- **KHÔNG** delete individual rows (chỉ bulk prune theo age)
- Dùng cho audit trail và dashboard aggregation

### References

- [Source: architecture.md#Dec-H-Usage-Events-Schema] — append-only, url_hash, 90-day retention
- [Source: architecture.md#Gap-Analysis-Results] — APScheduler for retention prune
- [Source: epics.md#Story-3.1] — acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/billing/models.py` — complete UsageEvent model
- `backend/app/main.py` — add lifespan with APScheduler
- `backend/requirements.txt` — add apscheduler

**NEW:**
- `backend/alembic/versions/004_create_usage_events.py`
- `backend/tests/billing/test_usage_events.py`
