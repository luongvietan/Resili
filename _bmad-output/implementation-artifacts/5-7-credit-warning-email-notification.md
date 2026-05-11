# Story 5.7: Credit Warning Email Notification

Status: ready-for-dev

## Story

As a developer on any tier,
I want to receive an email warning when my credit usage reaches 80% of my monthly limit,
so that I can upgrade or reduce usage before hitting the limit.

## Acceptance Criteria

1. **Given** a credit deduction that brings `credits_used / monthly_limit >= 0.80` for the first time in the billing period, **When** the deduction completes, **Then** an email is sent via Resend API with subject "You've used 80% of your Resili credits".

2. **Given** the email content, **When** reviewed, **Then** it includes: current `credits_used`, `monthly_limit`, reset date, and a CTA link to upgrade (for Free tier) or dashboard (for Pro tier).

3. **Given** subsequent deductions after the 80% threshold has already been reached, **When** processed, **Then** the warning email is NOT sent again (idempotent — one email per billing period).

4. **Given** `RESEND_API_KEY` is not set in environment, **When** a scraping request is made, **Then** the scraping request succeeds; the email notification is silently skipped (non-blocking).

5. **Given** the notification email is triggered, **When** it fails to send (network error, Resend API down), **Then** the scraping response is still returned to the user; the email failure is logged but does not cause the scraping request to fail.

## Tasks / Subtasks

- [ ] Implement email notification service (AC: 1, 2)
  - [ ] `app/notifications/service.py`: `send_credit_warning_email(user_email, used, limit, reset_date, tier)`
  - [ ] Use Resend Python SDK

- [ ] Implement 80% threshold check (AC: 1, 3)
  - [ ] `app/billing/service.py`: after deduction, check if ≥ 80% threshold crossed
  - [ ] Track `last_warning_sent_at` or `warning_sent` flag in `credit_balances`

- [ ] Make notification non-blocking (AC: 4, 5)
  - [ ] Wrap email send in try/except: log error, never raise
  - [ ] If `RESEND_API_KEY` is None, skip silently

- [ ] Add `warning_sent` flag to `credit_balances` (AC: 3)
  - [ ] Alembic migration `005_add_warning_sent_flag`
  - [ ] `credit_balances.warning_sent` = bool, default False
  - [ ] Reset to False when monthly credits reset

- [ ] Viết tests (AC: 1, 3, 4, 5)

## Dev Notes

### `credit_balances` Table — Add `warning_sent` Column (AC: 3)

```python
# Alembic migration 005
def upgrade() -> None:
    op.add_column("credit_balances", sa.Column(
        "warning_sent", sa.Boolean, nullable=False, server_default="false"
    ))
```

Update `CreditBalance` model:
```python
class CreditBalance(Base):
    # ... existing fields ...
    warning_sent: Mapped[bool] = mapped_column(default=False, nullable=False)
```

**Reset `warning_sent` when credits reset:** When a monthly credit reset job runs (or at start of new billing period), set `warning_sent = False` for all users.

### `app/notifications/service.py` — Resend Integration

```python
import resend
from app.core.config import settings
import logging

logger = logging.getLogger(__name__)


async def send_credit_warning_email(
    user_email: str,
    credits_used: int,
    monthly_limit: int,
    reset_date: str,
    tier: str,
) -> None:
    """
    Send 80% credit warning email via Resend.
    NON-BLOCKING: silently skips if Resend not configured (AC: 4).
    NEVER raises exception (AC: 5).
    """
    if not settings.RESEND_API_KEY:
        logger.debug("RESEND_API_KEY not set — skipping credit warning email")
        return

    resend.api_key = settings.RESEND_API_KEY

    upgrade_cta = (
        '<a href="https://resili.io/dashboard/billing">Upgrade to Pro</a>'
        if tier == "free"
        else '<a href="https://resili.io/dashboard">View Dashboard</a>'
    )

    html_content = f"""
    <h2>You've used 80% of your Resili credits</h2>
    <p>Current usage: <strong>{credits_used:,} / {monthly_limit:,} credits</strong></p>
    <p>Your credits reset on <strong>{reset_date}</strong>.</p>
    <p>{upgrade_cta}</p>
    <p>If you exceed your limit, API calls will return a 429 error.</p>
    """

    try:
        resend.Emails.send({
            "from": "Resili <noreply@resili.io>",
            "to": [user_email],
            "subject": "You've used 80% of your Resili credits",
            "html": html_content,
        })
        logger.info(f"Credit warning email sent to {user_email}")
    except Exception as e:
        # CRITICAL: NEVER propagate this exception (AC: 5)
        # Log and continue — scraping response must succeed
        logger.error(f"Failed to send credit warning email to {user_email}: {e}")
```

### `app/billing/service.py` — 80% Check After Deduction

```python
async def deduct_credits(
    db: AsyncSession,
    user_id: uuid.UUID,
    cost: int,
    url_hash: str,
    endpoint_type: str,
) -> None:
    async with db.begin():
        result = await db.execute(
            select(CreditBalance).where(CreditBalance.user_id == user_id).with_for_update()
        )
        balance = result.scalar_one_or_none()
        # ... existing checks and deduction ...

        # Check 80% threshold AFTER deduction (AC: 1)
        threshold = balance.monthly_limit * 0.80
        should_send_warning = (
            balance.credits_used >= threshold
            and not balance.warning_sent  # Idempotent: one email per period (AC: 3)
        )

        if should_send_warning:
            balance.warning_sent = True  # Mark before commit to prevent duplicates

        await db.commit()

    # AFTER transaction — send email asynchronously (non-blocking)
    if should_send_warning:
        # Fetch user email
        async with db.begin():
            result = await db.execute(select(User).where(User.id == user_id))
            user = result.scalar_one_or_none()

        if user:
            # Fire-and-forget — don't await (non-blocking)
            asyncio.create_task(
                notifications_service.send_credit_warning_email(
                    user_email=user.email,
                    credits_used=balance.credits_used,
                    monthly_limit=balance.monthly_limit,
                    reset_date=str(balance.reset_date),
                    tier=balance.tier,
                )
            )
```

**CRITICAL:** 
1. Set `warning_sent = True` BEFORE committing (in same transaction) to prevent race conditions
2. Email send is `asyncio.create_task()` — fire-and-forget, does NOT block deduction response

### Credit Reset — Also Reset `warning_sent`

When monthly credit reset runs (e.g., at `reset_date`), reset `warning_sent = False`:

```python
# In monthly reset job (future enhancement or in prune_usage_events):
async def reset_monthly_credits():
    today = date.today()
    async with AsyncSessionLocal() as db:
        await db.execute(
            text("""
                UPDATE credit_balances
                SET credits_used = 0, warning_sent = false,
                    reset_date = reset_date + INTERVAL '1 month'
                WHERE reset_date <= :today
            """),
            {"today": today}
        )
        await db.commit()
```

### Non-Blocking Pattern (AC: 4, 5)

The three layers of protection:
1. `if not settings.RESEND_API_KEY: return` — skip if not configured
2. `try/except Exception: logger.error()` — catch all errors, never raise
3. `asyncio.create_task()` — fire-and-forget, deduction already complete before email attempt

### Test — Warning Email Idempotency (AC: 3)

```python
async def test_warning_email_sent_only_once(db: AsyncSession, user: User):
    """Multiple deductions past 80% should only send one warning email."""
    # Set balance to 79%
    balance = await get_balance(db, user.id)
    balance.credits_used = int(balance.monthly_limit * 0.79)
    await db.commit()

    with patch("app.notifications.service.send_credit_warning_email") as mock_send:
        # First deduction crosses 80%
        await deduct_credits(db, user.id, cost=10, url_hash="h1", endpoint_type="fetcher")
        # Second deduction (already past 80%)
        await deduct_credits(db, user.id, cost=1, url_hash="h2", endpoint_type="fetcher")

        # Email sent exactly once
        assert mock_send.call_count == 1
```

### References

- [Source: epics.md#Story-5.7] — acceptance criteria
- [Source: architecture.md#Dec-G-Credit-Accounting-Atomicity] — deduction pattern
- [Source: architecture.md#Gap-Analysis-Results] — Resend integration

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/billing/service.py` — add 80% threshold check + fire-and-forget email
- `backend/app/billing/models.py` — add warning_sent field
- `backend/requirements.txt` — verify resend>=2.5

**NEW:**
- `backend/app/notifications/service.py` (complete implementation)
- `backend/alembic/versions/005_add_warning_sent_flag.py`
- `backend/tests/notifications/test_credit_warning.py`
