# Story 3.2: Credit Accounting Service & Tier Enforcement

Status: ready-for-dev

## Story

As the Resili billing system,
I want atomic credit deduction and tier enforcement before any scrape executes,
so that users cannot exceed their quota and credits are never double-charged.

## Acceptance Criteria

1. **Given** `billing/service.py.deduct_credits(db, user_id, cost)` called within a transaction, **When** the user has sufficient credits, **Then** it executes `SELECT FOR UPDATE` on `credit_balances`, deducts atomically, logs to `usage_events`, and Redis balance cache is invalidated.

2. **Given** `deduct_credits()` called when the user has 0 remaining credits, **When** called, **Then** `CreditsExhaustedError` is raised; no `usage_events` row is written for the failed attempt.

3. **Given** `Depends(require_credits(cost=1))` on a Fetcher endpoint, with a Free tier user at 0 remaining credits, **When** called, **Then** HTTP 429 is returned with error code `CREDITS_EXHAUSTED`, `Retry-After` header set to seconds until `reset_date`.

4. **Given** `Depends(require_credits(cost=5))` on DynamicFetcher, with a Free tier user, **When** called, **Then** HTTP 403 is returned with error code `DYNAMIC_NOT_AVAILABLE_FREE_TIER`.

5. **Given** 100 concurrent `deduct_credits()` calls for same user with exactly 50 credits remaining, **When** all resolve, **Then** exactly 50 succeed and 50 raise `CreditsExhaustedError` — no over-deduction.

6. **Given** all scraping route handlers, **When** reviewed, **Then** `Depends(require_credits(cost=N))` is used — no manual credit check inside handler body.

## Tasks / Subtasks

- [ ] Implement `deduct_credits()` with SELECT FOR UPDATE (AC: 1, 2, 5)
  - [ ] `app/billing/service.py`: `deduct_credits(db, user_id, cost, url_hash, endpoint_type)`
  - [ ] PostgreSQL `SELECT FOR UPDATE` (with_for_update()) within async transaction
  - [ ] Check remaining credits → raise CreditsExhaustedError if insufficient
  - [ ] Deduct atomically → log UsageEvent → invalidate Redis cache

- [ ] Implement `require_credits()` dependency (AC: 3, 4, 6)
  - [ ] `app/billing/dependencies.py`: `require_credits(cost: int)` factory
  - [ ] Free tier + cost=5 (Dynamic) → 403 `DYNAMIC_NOT_AVAILABLE_FREE_TIER`
  - [ ] 0 remaining credits → 429 `CREDITS_EXHAUSTED` with Retry-After header
  - [ ] Wire into scrape.py placeholder endpoints

- [ ] Add new error types (AC: 3, 4)
  - [ ] `app/core/errors.py`: `DynamicNotAvailableFreeError` (403)
  - [ ] Update `CreditsExhaustedError` to include `Retry-After` header

- [ ] Viết concurrent deduction tests (AC: 5)

## Dev Notes

### `app/billing/service.py` — deduct_credits with SELECT FOR UPDATE (Dec-G)

```python
import hashlib
from datetime import datetime, timezone
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from app.billing.models import CreditBalance, UsageEvent
from app.core.errors import CreditsExhaustedError
from app.core.redis import get_redis
import uuid


async def deduct_credits(
    db: AsyncSession,
    user_id: uuid.UUID,
    cost: int,
    url_hash: str,
    endpoint_type: str,  # 'fetcher' | 'dynamic'
) -> None:
    """
    Atomically deduct credits. Raises CreditsExhaustedError if insufficient.
    Uses SELECT FOR UPDATE to prevent race conditions (Dec-G).
    """
    async with db.begin():
        # SELECT FOR UPDATE — locks the row until transaction commits
        result = await db.execute(
            select(CreditBalance)
            .where(CreditBalance.user_id == user_id)
            .with_for_update()  # CRITICAL: prevents concurrent over-deduction
        )
        balance = result.scalar_one_or_none()

        if not balance:
            raise CreditsExhaustedError()

        remaining = balance.monthly_limit - balance.credits_used
        if remaining < cost:
            # No usage_event written for failed attempt (AC: 2)
            raise CreditsExhaustedError(
                reset_date=balance.reset_date.isoformat()
            )

        # Deduct atomically
        balance.credits_used += cost
        balance.updated_at = datetime.now(timezone.utc)

        # Log usage event (append-only)
        event = UsageEvent(
            user_id=user_id,
            endpoint_type=endpoint_type,
            credits_used=cost,
            url_hash=url_hash,
            status="success",
        )
        db.add(event)

    # Invalidate Redis cache after transaction commits (Dec-G)
    redis = await get_redis()
    await redis.delete(f"credit_balance:{user_id}")
```

### `app/billing/dependencies.py` — require_credits factory

```python
from fastapi import Depends
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.db.session import get_db
from app.auth.models import User
from app.billing.models import CreditBalance
from app.core.errors import CreditsExhaustedError, DynamicNotAvailableFreeError
from datetime import datetime, timezone
import math


def require_credits(cost: int):
    """
    Dependency factory for credit checking. Use as:
    @router.post("/scrape/fetch")
    async def fetch_page(_: None = Depends(require_credits(cost=1)), ...):
    """
    async def _check_credits(
        user: User = Depends(get_current_user_from_api_key),
        db: AsyncSession = Depends(get_db),
    ) -> None:
        # Free tier cannot use DynamicFetcher (cost=5)
        if cost == 5 and user.tier == "free":
            raise DynamicNotAvailableFreeError()

        result = await db.execute(
            select(CreditBalance).where(CreditBalance.user_id == user.id)
        )
        balance = result.scalar_one_or_none()

        if not balance:
            raise CreditsExhaustedError()

        remaining = balance.monthly_limit - balance.credits_used
        if remaining < cost:
            # Retry-After = seconds until reset_date (midnight UTC)
            reset_dt = datetime.combine(balance.reset_date, datetime.min.time()).replace(tzinfo=timezone.utc)
            retry_after = max(0, math.ceil((reset_dt - datetime.now(timezone.utc)).total_seconds()))
            raise CreditsExhaustedError(retry_after=retry_after, reset_date=balance.reset_date.isoformat())

    return _check_credits
```

### `app/core/errors.py` — Update CreditsExhaustedError + add DynamicNotAvailable

```python
from fastapi import Request
from fastapi.responses import JSONResponse

class CreditsExhaustedError(ResiliError):
    status_code = 429
    error_code = "CREDITS_EXHAUSTED"
    message = "Your credits for this month are exhausted"
    hint = "Upgrade to Pro or wait for your credits to reset"
    docs_url = "https://docs.resili.io/errors/credits-exhausted"

    def __init__(self, reset_date: str = "", retry_after: int = 0):
        self.reset_date = reset_date
        self.retry_after = retry_after
        if reset_date:
            self.message = f"Your fetcher credits for this month are exhausted. They reset on {reset_date}"

    def to_response(self) -> JSONResponse:
        """Override to add Retry-After header."""
        response = JSONResponse(
            status_code=self.status_code,
            content=self.to_dict(),
        )
        if self.retry_after:
            response.headers["Retry-After"] = str(self.retry_after)
        return response


class DynamicNotAvailableFreeError(ResiliError):
    status_code = 403
    error_code = "DYNAMIC_NOT_AVAILABLE_FREE_TIER"
    message = "DynamicFetcher is not available on the Free tier"
    hint = "Upgrade to Pro to access DynamicFetcher"
    docs_url = "https://docs.resili.io/errors/dynamic-not-available-free-tier"
```

**Update exception handler to use `to_response()` if available:**
```python
async def resili_error_handler(request: Request, exc: ResiliError) -> JSONResponse:
    if hasattr(exc, "to_response"):
        return exc.to_response()
    return _error_response(exc)
```

### Wire require_credits into scrape.py

```python
# app/api/v1/scrape.py
from app.billing.dependencies import require_credits

@router.post("/fetch")
async def fetch_page(
    body: FetchRequest,
    user: User = Depends(get_current_user_from_api_key),
    _: None = Depends(require_credits(cost=1)),  # Check BEFORE scraping
    db: AsyncSession = Depends(get_db),
):
    ...

@router.post("/dynamic")
async def fetch_dynamic_page(
    body: DynamicFetchRequest,
    user: User = Depends(get_current_user_from_api_key),
    _: None = Depends(require_credits(cost=5)),  # 5x multiplier, blocks Free tier
    db: AsyncSession = Depends(get_db),
):
    ...
```

### Concurrent Deduction Test (AC: 5)

```python
import asyncio

async def test_concurrent_deductions_no_overdraft(db: AsyncSession, user: User):
    """50 credits remaining → exactly 50 deductions succeed."""
    # Set balance to exactly 50
    result = await db.execute(select(CreditBalance).where(CreditBalance.user_id == user.id))
    balance = result.scalar_one()
    balance.credits_used = balance.monthly_limit - 50
    await db.commit()

    # Fire 100 concurrent deductions
    url_hash = hashlib.sha256(b"test").hexdigest()
    tasks = [
        deduct_credits(AsyncSessionLocal(), user.id, 1, url_hash, "fetcher")
        for _ in range(100)
    ]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    successes = sum(1 for r in results if not isinstance(r, Exception))
    failures = sum(1 for r in results if isinstance(r, CreditsExhaustedError))
    assert successes == 50
    assert failures == 50
```

### Redis Balance Cache (Dec-G)

After deduction, invalidate `credit_balance:{user_id}` key. Optionally cache balance for read (TTL 60s):
```python
# Cache GET balance
await redis.setex(f"credit_balance:{user_id}", 60, str(balance.credits_used))
```

### References

- [Source: architecture.md#Dec-G-Credit-Accounting-Atomicity] — SELECT FOR UPDATE, Redis cache
- [Source: architecture.md#Communication-Patterns] — Depends() pattern mandatory
- [Source: epics.md#Story-3.2] — acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/core/errors.py` — update CreditsExhaustedError, add DynamicNotAvailableFreeError
- `backend/app/api/v1/scrape.py` — wire require_credits dependency

**NEW (or complete):**
- `backend/app/billing/service.py` — deduct_credits
- `backend/app/billing/dependencies.py` — require_credits factory
- `backend/tests/billing/test_credit_deduction.py`
