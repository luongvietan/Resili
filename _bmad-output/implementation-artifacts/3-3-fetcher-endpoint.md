# Story 3.3: Fetcher Endpoint

Status: ready-for-dev

## Story

As a developer using Resili,
I want to call a Fetcher endpoint with a URL and receive clean Markdown or JSON,
so that I can integrate static web page content into my AI pipeline without managing scraping infrastructure.

## Acceptance Criteria

1. **Given** POST /api/v1/scrape/fetch with `{"url": "https://example.com", "format": "markdown"}` and a valid API key with credits, **When** the page loads successfully, **Then** HTTP 200 is returned with `{"job_id": null, "status": "completed", "result": {"content": "<markdown>", "format": "markdown", "credits_used": 1}}`.

2. **Given** POST /api/v1/scrape/fetch with `{"url": "https://example.com", "format": "json"}`, **When** called, **Then** `result.content` is a JSON string of structured data extracted from the page.

3. **Given** POST /api/v1/scrape/fetch without a `format` field, **When** called, **Then** `format` defaults to `"markdown"`.

4. **Given** POST /api/v1/scrape/fetch with `{"respect_robots_txt": true}` and a URL disallowed by robots.txt, **When** called, **Then** HTTP 400 with error code `ROBOTS_TXT_DISALLOWED` is returned.

5. **Given** a successful Fetcher call, **When** the `usage_events` table is checked, **Then** a new append-only row exists with `endpoint_type='fetcher'`, `credits_used=1`, `url_hash=SHA256(url)`, `status='success'`.

6. **Given** Fetcher p95 response time under ≤ 100 concurrent requests, **When** measured via Sentry APM, **Then** p95 ≤ 3 seconds.

## Tasks / Subtasks

- [ ] Implement Scrapling Fetcher wrapper (AC: 1, 2, 3, 4)
  - [ ] `app/scraping/fetcher.py`: async wrapper around Scrapling Fetcher
  - [ ] Support `format`: 'markdown' | 'json'
  - [ ] Default format = 'markdown' (AC: 3)
  - [ ] `respect_robots_txt` parameter (AC: 4)

- [ ] Implement HTML formatter (AC: 1, 2)
  - [ ] `app/scraping/formatter.py`: `html_to_markdown()`, `html_to_json()`

- [ ] Implement scraping service (AC: 1, 5)
  - [ ] `app/scraping/service.py`: orchestrate ssrf_guard → credit_check → fetch → format → log_event
  - [ ] Log UsageEvent with url_hash after successful scrape

- [ ] Implement Pydantic schemas (AC: 1, 2, 3)
  - [ ] `app/scraping/schemas.py`: `FetchRequest`, `ScrapeResult`, `ScrapeResponse`
  - [ ] `ScrapeResponse` shape: `{"job_id": null, "status": "completed", "result": {...}}`

- [ ] Complete fetch endpoint in scrape.py (AC: 1, 2, 3, 4)
  - [ ] Full implementation replacing the Story 2.5 placeholder

- [ ] Viết tests (AC: 1, 2, 3, 4, 5)

## Dev Notes

### `app/scraping/schemas.py` — Dec-F async-ready shape

```python
from pydantic import BaseModel
from typing import Literal

class FetchRequest(BaseModel):
    url: str
    format: Literal["markdown", "json"] = "markdown"  # Default = markdown (AC: 3)
    respect_robots_txt: bool = False  # Default = False per NFR-10

class ScrapeResult(BaseModel):
    content: str
    format: str
    credits_used: int

class ScrapeResponse(BaseModel):
    job_id: None = None        # Always null in MVP (Dec-F async-ready shape)
    status: str = "completed"  # Always "completed" in MVP
    result: ScrapeResult
```

**CRITICAL Dec-F shape:** `job_id: null` and `status: "completed"` must ALWAYS be in response. This shape ensures Growth phase async migration won't break existing clients.

### `app/scraping/fetcher.py` — Scrapling Wrapper

```python
import asyncio
from scrapling import Fetcher
from scrapling.engines import PlayWrightEngine
from app.core.errors import RobotsTxtDisallowedError, ScrapingError


async def fetch_url(url: str, respect_robots_txt: bool = False) -> str:
    """
    Async wrapper for Scrapling Fetcher.
    Returns raw HTML string.
    Raises: RobotsTxtDisallowedError, ScrapingError
    """
    def _sync_fetch():
        fetcher = Fetcher(respect_robots_txt=respect_robots_txt)
        try:
            page = fetcher.get(url)
            return page.html_content
        except Exception as e:
            error_msg = str(e).lower()
            if "robots" in error_msg or "disallowed" in error_msg:
                raise RobotsTxtDisallowedError()
            raise ScrapingError(message=f"Fetcher failed: {str(e)[:200]}")

    # Run in thread pool (Scrapling Fetcher is sync)
    loop = asyncio.get_event_loop()
    html = await loop.run_in_executor(None, _sync_fetch)
    return html
```

**Note on Scrapling v0.4.7:** BSD license fork. Import as `from scrapling import Fetcher` for static pages. Scrapling's API may differ from Playwright wrapper. Check Scrapling docs for exact API.

### `app/scraping/formatter.py`

```python
import json
from html.parser import HTMLParser
import re


def html_to_markdown(html: str) -> str:
    """Convert HTML to clean Markdown using Scrapling's built-in or markdownify."""
    # Use markdownify library for robust conversion
    from markdownify import markdownify as md
    return md(html, heading_style="ATX", strip=["script", "style"])


def html_to_json(html: str) -> str:
    """Extract structured data from HTML and return as JSON string."""
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(html, "html.parser")

    # Remove scripts and styles
    for tag in soup(["script", "style"]):
        tag.decompose()

    data = {
        "title": soup.title.string if soup.title else "",
        "text": soup.get_text(separator="\n", strip=True),
        "links": [{"text": a.text.strip(), "href": a.get("href", "")}
                  for a in soup.find_all("a", href=True)[:50]],
        "headings": [{"level": int(h.name[1]), "text": h.text.strip()}
                     for h in soup.find_all(["h1", "h2", "h3", "h4"])],
    }
    return json.dumps(data, ensure_ascii=False)
```

Add `markdownify` and `beautifulsoup4` to `requirements.txt`.

### `app/scraping/service.py` — Orchestration Pipeline

```python
import hashlib
from app.core.ssrf_guard import validate_url
from app.core.security import hash_url
from app.scraping.fetcher import fetch_url
from app.scraping.formatter import html_to_markdown, html_to_json
from app.billing.service import deduct_credits


async def scrape_page(
    url: str,
    format: str,
    respect_robots_txt: bool,
    user_id: uuid.UUID,
    db: AsyncSession,
) -> dict:
    # 1. SSRF guard (MUST be first — Dec-B)
    validate_url(url)

    # 2. Fetch HTML
    html = await fetch_url(url, respect_robots_txt=respect_robots_txt)

    # 3. Format output
    if format == "markdown":
        content = html_to_markdown(html)
    else:
        content = html_to_json(html)

    # 4. Deduct credits + log event (atomic — Dec-G)
    url_hash = hash_url(url)  # SHA-256 hash of URL — NOT raw URL (NFR-09)
    await deduct_credits(db, user_id, cost=1, url_hash=url_hash, endpoint_type="fetcher")

    return {
        "job_id": None,        # Dec-F
        "status": "completed", # Dec-F
        "result": {
            "content": content,
            "format": format,
            "credits_used": 1,
        }
    }
```

### Complete Fetch Endpoint

```python
# app/api/v1/scrape.py
@router.post("/fetch")
async def fetch_page(
    body: FetchRequest,
    user: User = Depends(get_current_user_from_api_key),
    _: None = Depends(require_credits(cost=1)),
    db: AsyncSession = Depends(get_db),
):
    result = await scraping_service.scrape_page(
        url=body.url,
        format=body.format,
        respect_robots_txt=body.respect_robots_txt,
        user_id=user.id,
        db=db,
    )
    return result
```

### New Error Types

```python
# app/core/errors.py
class RobotsTxtDisallowedError(ResiliError):
    status_code = 400
    error_code = "ROBOTS_TXT_DISALLOWED"
    message = "The target URL is disallowed by robots.txt"
    hint = "Set respect_robots_txt=false or choose a different URL"
    docs_url = "https://docs.resili.io/errors/robots-txt-disallowed"

class ScrapingError(ResiliError):
    status_code = 500
    error_code = "SCRAPING_FAILED"
    message = "Failed to scrape the target URL"
    hint = "Try again, or use DynamicFetcher for JS-heavy pages"
    docs_url = "https://docs.resili.io/errors/scraping-failed"
```

### requirements.txt — Add new dependencies

```
markdownify>=0.13
beautifulsoup4>=4.12
lxml>=5.2
```

### Scrapling Version Note

Scrapling v0.4.7 — BSD fork. This is the pinned version per architecture. Do NOT upgrade without testing. Import pattern:
```python
from scrapling import Fetcher      # Static page fetcher
from scrapling.engines import ...  # For custom engine configs
```

### References

- [Source: architecture.md#Dec-F-DynamicFetcher-Async-Ready-Response-Shape] — job_id: null, status: completed
- [Source: architecture.md#Scrape-Request-Flow] — pipeline order
- [Source: epics.md#Story-3.3] — acceptance criteria
- [Source: architecture.md#Dec-H-Usage-Events-Schema] — url_hash storage

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/api/v1/scrape.py` — complete fetch_page endpoint
- `backend/requirements.txt` — add markdownify, beautifulsoup4, lxml
- `backend/app/core/errors.py` — add RobotsTxtDisallowedError, ScrapingError

**NEW:**
- `backend/app/scraping/schemas.py`
- `backend/app/scraping/fetcher.py`
- `backend/app/scraping/formatter.py`
- `backend/app/scraping/service.py`
- `backend/tests/api/test_scrape.py`
- `backend/tests/scraping/test_fetcher.py`
