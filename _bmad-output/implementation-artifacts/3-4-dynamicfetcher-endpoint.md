# Story 3.4: DynamicFetcher Endpoint

Status: ready-for-dev

## Story

As a developer using Resili,
I want to call a DynamicFetcher endpoint that fully renders JavaScript before returning content,
so that I can scrape JS-heavy pages that Fetcher cannot handle.

## Acceptance Criteria

1. **Given** POST /api/v1/scrape/dynamic with `{"url": "https://spa-example.com"}` and a valid Pro API key, **When** the page renders successfully, **Then** HTTP 200 is returned with `{"job_id": null, "status": "completed", "result": {"content": "<rendered-markdown>", "format": "markdown", "credits_used": 5}}`.

2. **Given** each DynamicFetcher request, **When** processed, **Then** it creates a new isolated Playwright browser context; the context is closed in a `finally` block regardless of success or error.

3. **Given** a DynamicFetcher request on a page that takes > 30 seconds to render, **When** the timeout fires, **Then** Playwright context is closed, error response returned with code `DYNAMIC_TIMEOUT`.

4. **Given** the async-ready response shape, **When** reviewed, **Then** response always includes `job_id: null` and `status: "completed"` at MVP.

5. **Given** `Dockerfile.worker`, **When** built and run, **Then** `playwright install chromium` has been executed.

6. **Given** DynamicFetcher p95 under ≤ 20 concurrent Playwright sessions, **When** measured, **Then** p95 ≤ 15 seconds.

## Tasks / Subtasks

- [ ] Implement Playwright DynamicFetcher wrapper (AC: 1, 2, 3)
  - [ ] `app/scraping/dynamic.py`: async Playwright scraper with isolated context per request
  - [ ] 30s timeout via `asyncio.timeout(30)` or `page.goto(timeout=30000)`
  - [ ] Context closed in `finally` block (NFR-04)

- [ ] Integrate DynamicFetcher into scraping service (AC: 1, 4)
  - [ ] `app/scraping/service.py`: add `scrape_dynamic()` function
  - [ ] Dec-F shape: `job_id: null, status: "completed"`

- [ ] Complete dynamic endpoint in scrape.py (AC: 1, 2, 3)
  - [ ] Replace Story 2.5 placeholder
  - [ ] `require_credits(cost=5)` already wired from Story 3.2

- [ ] Add error types (AC: 3)
  - [ ] `app/core/errors.py`: `DynamicTimeoutError`

- [ ] Viết tests (AC: 1, 2, 3, 4)

## Dev Notes

### `app/scraping/dynamic.py` — Playwright with Isolation (NFR-04)

```python
import asyncio
from playwright.async_api import async_playwright, Error as PlaywrightError
from app.core.errors import DynamicTimeoutError, ScrapingError

DYNAMIC_TIMEOUT_SECONDS = 30  # NFR-04


async def fetch_dynamic_url(url: str, format: str = "markdown") -> str:
    """
    Fetch a JS-heavy page using Playwright.
    Each request gets its own isolated browser context (NFR-04).
    Context is ALWAYS closed in finally block.
    Returns HTML string.
    """
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=True)
        context = None
        try:
            # Isolated context per request (NFR-04)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (compatible; Resili/1.0; +https://resili.io/bot)"
            )
            page = await context.new_page()

            try:
                async with asyncio.timeout(DYNAMIC_TIMEOUT_SECONDS):
                    await page.goto(url, wait_until="networkidle")
                    html = await page.content()
                    return html
            except asyncio.TimeoutError:
                raise DynamicTimeoutError()
            except PlaywrightError as e:
                raise ScrapingError(message=f"Playwright error: {str(e)[:200]}")

        finally:
            # ALWAYS close context — even if error (NFR-04)
            if context:
                await context.close()
            await browser.close()
```

**CRITICAL RULES:**
1. Each request = NEW browser context (not shared)
2. `finally` ALWAYS closes context — prevents browser resource leaks
3. 30s timeout = hard limit (NFR-04)

### `app/core/errors.py` — Add DynamicTimeoutError

```python
class DynamicTimeoutError(ResiliError):
    status_code = 408  # Or 200 with status: "error" per FR-07
    error_code = "DYNAMIC_TIMEOUT"
    message = "Page took >30s to render"
    hint = "Try Fetcher for static content, or check if the page is accessible"
    docs_url = "https://docs.resili.io/errors/dynamic-timeout"
```

Note: The AC says "HTTP 200 with status: 'error' (or 408 equivalent)". Implementing as 408 for simplicity. Can be 200 with `status: "error"` in the Dec-F body if desired.

### `app/scraping/service.py` — Add scrape_dynamic

```python
from app.scraping.dynamic import fetch_dynamic_url

async def scrape_dynamic_page(
    url: str,
    format: str,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    # 1. SSRF guard (MUST be first)
    validate_url(url)

    # 2. Fetch with Playwright
    html = await fetch_dynamic_url(url, format=format)

    # 3. Format
    if format == "markdown":
        content = html_to_markdown(html)
    else:
        content = html_to_json(html)

    # 4. Deduct credits + log (cost=5 for Dynamic)
    url_hash = hash_url(url)
    await deduct_credits(db, user_id, cost=5, url_hash=url_hash, endpoint_type="dynamic")

    return {
        "job_id": None,        # Dec-F: always null in MVP
        "status": "completed", # Dec-F: always completed in MVP
        "result": {
            "content": content,
            "format": format,
            "credits_used": 5,  # 1 Dynamic = 5 Fetcher credits (FR-12)
        }
    }
```

### Complete Dynamic Endpoint

```python
# app/api/v1/scrape.py
class DynamicFetchRequest(BaseModel):
    url: str
    format: Literal["markdown", "json"] = "markdown"

@router.post("/dynamic")
async def fetch_dynamic_page(
    body: DynamicFetchRequest,
    user: User = Depends(get_current_user_from_api_key),
    _: None = Depends(require_credits(cost=5)),  # 5 credits + blocks Free tier
    db: AsyncSession = Depends(get_db),
):
    result = await scraping_service.scrape_dynamic_page(
        url=body.url,
        format=body.format,
        user_id=user.id,
        db=db,
    )
    return result
```

### Playwright in Docker (Dockerfile.worker)

`Dockerfile.worker` từ Story 1.1 đã có `playwright install chromium`. Verify:
```dockerfile
RUN playwright install chromium
# Verify by running: python -c "from playwright.sync_api import sync_playwright; print('OK')"
```

DynamicFetcher endpoints chạy trong **cùng FastAPI process** (MVP). Worker service là placeholder cho Growth phase Celery migration. `Dockerfile.worker` hiện chỉ cần cho isolation test.

### Memory & Resource Management

```python
# Playwright browser pool pattern (optional optimization for concurrent requests)
# MVP: create new browser per request (simpler, safer)
# Growth: implement browser pool with max 20 concurrent sessions (NFR-03)

# Per-request limits:
# - timeout: 30s (NFR-04)
# - 1 isolated context per request (NFR-04)
# - context closed in finally (NFR-04)
```

### Dec-F Shape Reminder

Response ALWAYS:
```json
{
  "job_id": null,
  "status": "completed",
  "result": {
    "content": "...",
    "format": "markdown",
    "credits_used": 5
  }
}
```

Growth phase will add `job_id: "uuid"` and `status: "pending"` without breaking this shape.

### References

- [Source: architecture.md#Dec-F-DynamicFetcher-Async-Ready-Response-Shape] — shape requirement
- [Source: architecture.md#Process-Patterns] — Playwright isolated context + finally
- [Source: epics.md#Story-3.4] — acceptance criteria
- [Source: architecture.md#Dec-B-SSRF-Protection] — validate_url first

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/api/v1/scrape.py` — complete dynamic endpoint
- `backend/app/scraping/service.py` — add scrape_dynamic_page
- `backend/app/core/errors.py` — add DynamicTimeoutError

**NEW:**
- `backend/app/scraping/dynamic.py`
- `backend/tests/scraping/test_dynamic.py`
