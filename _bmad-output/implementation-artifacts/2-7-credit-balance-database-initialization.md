# Story 2.7: Credit Balance Database Initialization

Status: ready-for-dev

## Story

As the Resili billing system,
I want a `credit_balances` table created and wired to user registration,
so that every new user immediately has a trackable credit quota.

## Acceptance Criteria

1. **Given** Alembic migration `003_create_credit_balances`, **When** `alembic upgrade head` is run, **Then** the `credit_balances` table is created with: `id` (UUID PK), `user_id` (UUID FK unique → users), `credits_used` (int default 0), `monthly_limit` (int default 1000), `tier` (varchar default 'free'), `reset_date` (date), `updated_at` (timestamptz).

2. **Given** the `credit_balances` table exists, **When** a new user completes registration (Story 2.1), **Then** the service layer creates the `credit_balances` row atomically within the same registration transaction.

3. **Given** app startup with no `credit_balances` rows for existing users, **When** `alembic upgrade head` is run, **Then** a backfill step creates `credit_balances` rows for any users that don't have one yet (idempotent, safe to run multiple times).

## Tasks / Subtasks

- [ ] Tạo Alembic migration `003_create_credit_balances` (AC: 1, 3)
  - [ ] Schema: `id` UUID PK, `user_id` UUID FK unique, `credits_used` int default 0, `monthly_limit` int default 1000, `tier` varchar default 'free', `reset_date` date, `updated_at` timestamptz
  - [ ] Add backfill step cho existing users trong `upgrade()`

- [ ] Finalize `CreditBalance` SQLAlchemy model (AC: 1)
  - [ ] `app/billing/models.py`: complete `CreditBalance` model (partially created in Story 2.1)

- [ ] Verify registration creates credit_balances atomically (AC: 2)
  - [ ] `app/auth/service.py`: verify `register_user()` creates CreditBalance in same transaction

- [ ] Viết tests (AC: 1, 2, 3)

## Dev Notes

### `app/billing/models.py` — Complete CreditBalance Model

```python
import uuid
from datetime import datetime, date, timezone
from sqlalchemy import String, Integer, Date, DateTime, ForeignKey
from sqlalchemy.orm import Mapped, mapped_column
from app.db.base import Base


class CreditBalance(Base):
    __tablename__ = "credit_balances"

    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    user_id: Mapped[uuid.UUID] = mapped_column(
        ForeignKey("users.id", ondelete="CASCADE"),
        unique=True,  # One balance per user
        nullable=False
    )
    credits_used: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    monthly_limit: Mapped[int] = mapped_column(Integer, default=1000, nullable=False)
    tier: Mapped[str] = mapped_column(String, default="free", nullable=False)
    reset_date: Mapped[date] = mapped_column(Date, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False
    )
```

### Alembic Migration `003_create_credit_balances.py`

```python
from datetime import date
from dateutil.relativedelta import relativedelta

def upgrade() -> None:
    op.create_table(
        "credit_balances",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("user_id", postgresql.UUID(as_uuid=True),
                  sa.ForeignKey("users.id", ondelete="CASCADE"),
                  unique=True, nullable=False),
        sa.Column("credits_used", sa.Integer, nullable=False, server_default="0"),
        sa.Column("monthly_limit", sa.Integer, nullable=False, server_default="1000"),
        sa.Column("tier", sa.String, nullable=False, server_default="free"),
        sa.Column("reset_date", sa.Date, nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False,
                  server_default=sa.func.now()),
    )

    # Backfill: create credit_balances for existing users (AC: 3 — idempotent)
    # reset_date = first day of next month
    today = date.today()
    reset_date = (today.replace(day=1) + relativedelta(months=1)).isoformat()

    op.execute(f"""
        INSERT INTO credit_balances (id, user_id, credits_used, monthly_limit, tier, reset_date, updated_at)
        SELECT gen_random_uuid(), u.id, 0, 1000, 'free', '{reset_date}', NOW()
        FROM users u
        WHERE u.id NOT IN (SELECT user_id FROM credit_balances)
    """)
```

### Registration Transaction Verification (AC: 2)

`app/auth/service.py` từ Story 2.1 đã implement này. Cần verify:

```python
async def register_user(db: AsyncSession, email: str, password: str) -> User:
    ...
    async with db.begin():
        db.add(user)
        await db.flush()  # Get user.id

        # This MUST be in same transaction
        balance = CreditBalance(
            user_id=user.id,
            credits_used=0,
            monthly_limit=1000,
            tier="free",
            reset_date=first_day_of_next_month(),
        )
        db.add(balance)
        await db.commit()  # Atomic commit — both user AND balance created or neither
```

### Helper Function for reset_date

```python
from datetime import date
from dateutil.relativedelta import relativedelta

def first_day_of_next_month() -> date:
    today = date.today()
    return (today.replace(day=1) + relativedelta(months=1))
```

### UsageEvent Model (Placeholder for Story 3.1)

Tạo luôn `UsageEvent` model placeholder trong `app/billing/models.py` để `alembic/env.py` import không bị lỗi:

```python
class UsageEvent(Base):
    __tablename__ = "usage_events"
    id: Mapped[uuid.UUID] = mapped_column(primary_key=True, default=uuid.uuid4)
    # Migration 004 sẽ tạo full schema
```

### Test — Verify atomic creation

```python
async def test_registration_creates_credit_balance(client: AsyncClient, db: AsyncSession):
    response = await client.post("/api/v1/auth/register", json={
        "email": "billing@test.com",
        "password": "password123"
    })
    assert response.status_code == 201
    user_id = response.json()["id"]

    result = await db.execute(
        select(CreditBalance).where(CreditBalance.user_id == uuid.UUID(user_id))
    )
    balance = result.scalar_one()
    assert balance.credits_used == 0
    assert balance.monthly_limit == 1000
    assert balance.tier == "free"
    assert balance.reset_date > date.today()
```

### References

- [Source: epics.md#Story-2.7] — acceptance criteria
- [Source: architecture.md#Dec-G-Credit-Accounting-Atomicity] — atomic transactions
- [Source: architecture.md#Dec-H-Usage-Events-Schema] — billing models

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/billing/models.py` — finalize CreditBalance, add UsageEvent placeholder
- `backend/app/auth/service.py` — verify/fix atomic credit_balances creation

**NEW:**
- `backend/alembic/versions/003_create_credit_balances.py`
- `backend/tests/billing/__init__.py`
- `backend/tests/billing/test_credit_balance.py`
