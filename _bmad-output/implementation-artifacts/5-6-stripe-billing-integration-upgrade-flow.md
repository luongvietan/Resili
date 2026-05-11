# Story 5.6: Stripe Billing Integration & Upgrade Flow

Status: ready-for-dev

## Story

As a developer on the Free tier,
I want to upgrade to Pro via a seamless Stripe Checkout flow from the dashboard,
so that I gain DynamicFetcher access and higher credit limits.

## Acceptance Criteria

1. **Given** a Free tier dashboard, **When** clicking "Upgrade to Pro", **Then** the user is redirected to a Stripe Checkout session with Pro plan price.

2. **Given** a successful Stripe payment, **When** the `checkout.session.completed` webhook fires, **Then** the user's `tier` is updated to `"pro"` and `monthly_limit` in `credit_balances` is updated to 50000.

3. **Given** the Stripe webhook endpoint `POST /api/v1/billing/webhook`, **When** called with a valid Stripe signature, **Then** it processes the event and returns HTTP 200.

4. **Given** a webhook call with an invalid signature, **When** called, **Then** HTTP 400 is returned immediately without processing.

5. **Given** a Pro tier user, **When** they view the dashboard billing section, **Then** they see their plan, next billing date, and "Cancel subscription" option.

## Tasks / Subtasks

- [ ] Implement Stripe Checkout session creation (AC: 1)
  - [ ] `app/billing/service.py`: `create_checkout_session(user_id, email)` → Stripe session URL
  - [ ] `app/api/v1/billing.py`: `POST /api/v1/billing/checkout` → returns `{checkout_url: "..."}`

- [ ] Implement Stripe webhook handler (AC: 2, 3, 4)
  - [ ] `app/api/v1/billing.py`: `POST /api/v1/billing/webhook`
  - [ ] Verify signature with `stripe.webhook.construct_event()`
  - [ ] On `checkout.session.completed`: update user tier + credit limit atomically

- [ ] Implement billing info endpoint (AC: 5)
  - [ ] `app/api/v1/billing.py`: `GET /api/v1/billing/info` → plan, next_billing_date

- [ ] Create frontend billing section (AC: 1, 5)
  - [ ] Upgrade button in dashboard → calls POST /api/v1/billing/checkout → redirect to Stripe
  - [ ] Billing info display for Pro users

## Dev Notes

### Stripe Python SDK — Version

```
stripe>=11.3
```
(Already in requirements.txt from Story 1.1)

Stripe Python SDK v11 uses synchronous client by default. For async FastAPI, use `stripe.stripe_object.StripeObject` async methods or wrap in `asyncio.get_event_loop().run_in_executor()`.

### Stripe Keys in Settings

`app/core/config.py` (already has from Story 1.1):
```python
STRIPE_SECRET_KEY: str | None = None
STRIPE_WEBHOOK_SECRET: str | None = None
STRIPE_PRO_PRICE_ID: str | None = None  # Add this
```

### `app/billing/service.py` — Stripe Integration

```python
import stripe
from app.core.config import settings


def _get_stripe_client():
    if not settings.STRIPE_SECRET_KEY:
        raise ResiliError(message="Stripe not configured")
    return stripe.StripeClient(settings.STRIPE_SECRET_KEY)


async def create_checkout_session(user_id: uuid.UUID, user_email: str, return_url: str) -> str:
    """Create Stripe Checkout session. Returns checkout_url."""
    client = _get_stripe_client()

    def _create_sync():
        session = client.checkout.sessions.create(params={
            "payment_method_types": ["card"],
            "mode": "subscription",
            "line_items": [{"price": settings.STRIPE_PRO_PRICE_ID, "quantity": 1}],
            "customer_email": user_email,
            "metadata": {"user_id": str(user_id)},  # CRITICAL: pass user_id for webhook
            "success_url": f"{return_url}/dashboard?upgraded=true",
            "cancel_url": f"{return_url}/dashboard",
        })
        return session.url

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _create_sync)


async def upgrade_user_to_pro(db: AsyncSession, user_id: uuid.UUID) -> None:
    """Upgrade user to Pro tier atomically. Called from webhook handler."""
    async with db.begin():
        result = await db.execute(
            select(User).where(User.id == user_id).with_for_update()
        )
        user = result.scalar_one_or_none()
        if user:
            user.tier = "pro"

        result = await db.execute(
            select(CreditBalance).where(CreditBalance.user_id == user_id).with_for_update()
        )
        balance = result.scalar_one_or_none()
        if balance:
            balance.tier = "pro"
            balance.monthly_limit = 50000  # Pro tier limit

        await db.commit()
```

### `app/api/v1/billing.py` — Webhook Handler

```python
from fastapi import APIRouter, Request, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
import stripe

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/checkout")
async def create_checkout(
    user: User = Depends(get_current_user),  # JWT auth (dashboard)
    db: AsyncSession = Depends(get_db),
):
    """Create Stripe Checkout session for Pro upgrade."""
    return_url = settings.FRONTEND_URL or "http://localhost:3000"
    checkout_url = await billing_service.create_checkout_session(user.id, user.email, return_url)
    return {"checkout_url": checkout_url}


@router.post("/webhook")
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    """Stripe webhook — NO JWT auth (called by Stripe, not by user)."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature")

    if not settings.STRIPE_WEBHOOK_SECRET:
        raise HTTPException(status_code=500, detail="Stripe webhook not configured")

    try:
        # Verify signature (AC: 4)
        event = stripe.Webhook.construct_event(
            payload, sig_header, settings.STRIPE_WEBHOOK_SECRET
        )
    except stripe.SignatureVerificationError:
        # Invalid signature → 400 immediately (AC: 4)
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    # Process event
    if event["type"] == "checkout.session.completed":
        session = event["data"]["object"]
        user_id_str = session.get("metadata", {}).get("user_id")
        if user_id_str:
            user_id = uuid.UUID(user_id_str)
            await billing_service.upgrade_user_to_pro(db, user_id)

    return {"status": "ok"}
```

**CRITICAL:** `/api/v1/billing/webhook` MUST NOT use `Depends(get_current_user)` — it's called by Stripe, not by users. The only auth is signature verification.

### `app/core/config.py` — Add missing settings

```python
STRIPE_PRO_PRICE_ID: str | None = None
FRONTEND_URL: str = "http://localhost:3000"
```

### Frontend Upgrade Button

```typescript
// In dashboard billing section:
async function handleUpgrade() {
  const response = await apiRequest("/api/v1/billing/checkout", { method: "POST" });
  if (response.checkout_url) {
    window.location.href = response.checkout_url;  // Redirect to Stripe
  }
}
```

### Webhook Security (AC: 4)

```python
# Stripe signature verification is MANDATORY
# NEVER skip signature verification in any environment
# NEVER process webhook events without verified signature
```

### Testing Webhooks Locally

```bash
# Install Stripe CLI
stripe listen --forward-to http://localhost:8000/api/v1/billing/webhook
```

### References

- [Source: architecture.md#Dec-L-Payment-Integration] — Stripe Checkout, webhook verification
- [Source: epics.md#Story-5.6] — acceptance criteria
- [Source: architecture.md#Dec-G-Credit-Accounting-Atomicity] — atomic upgrade transaction

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/billing/service.py` — add Stripe functions
- `backend/app/core/config.py` — add STRIPE_PRO_PRICE_ID, FRONTEND_URL

**NEW:**
- `backend/app/api/v1/billing.py`
- `frontend/src/app/dashboard/billing/page.tsx` (optional for AC: 5)
