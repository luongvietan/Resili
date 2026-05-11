# Story 3.5: Scraping Error Handling & Rate Limit Responses

Status: ready-for-dev

## Story

As a developer using Resili,
I want clear, actionable error messages for every failure mode,
so that I can understand what went wrong and fix it within 2 minutes.

## Acceptance Criteria

1. **Given** any scraping failure, **When** an error response is returned, **Then** it follows Dec-D schema: `{"error": {"code": "SCREAMING_SNAKE_CASE", "message": "...", "hint": "...", "docs_url": "..."}}`.

2. **Given** POST /api/v1/scrape/fetch with `{"url": "not-a-url"}`, **When** called, **Then** HTTP 400 with error code `INVALID_URL` is returned.

3. **Given** a URL that returns HTTP 404 from the target, **When** Fetcher is called, **Then** error code `TARGET_NOT_FOUND` is returned.

4. **Given** a page with active anti-bot protection, **When** Fetcher is called, **Then** error code `ANTI_BOT_DETECTED` is returned with hint "Use /api/v1/scrape/dynamic for JS-heavy or bot-protected pages."

5. **Given** a user who has exhausted monthly quota, **When** they check the 429 error body, **Then** `message` names the specific credit type exhausted and `hint` includes the exact reset date.

## Tasks / Subtasks

- [ ] Add URL validation in FetchRequest schema (AC: 2)
  - [ ] `app/scraping/schemas.py`: validate URL format via pydantic validator
  - [ ] Raise `InvalidUrlError` (400) for malformed URLs

- [ ] Add target 404 and anti-bot error handling (AC: 3, 4)
  - [ ] `app/scraping/fetcher.py`: detect HTTP 404 from target → `TargetNotFoundError`
  - [ ] `app/scraping/fetcher.py`: detect anti-bot signals → `AntiBotDetectedError`

- [ ] Verify Dec-D schema for all error responses (AC: 1)
  - [ ] Review all existing error classes in `app/core/errors.py`
  - [ ] Verify `{"error": {...}}` wrapper for every HTTP error response

- [ ] Verify CreditsExhaustedError message specificity (AC: 5)
  - [ ] Error message must name specific credit type (fetcher vs dynamic)
  - [ ] Hint must include exact reset date

- [ ] Comprehensive integration tests (AC: 1-5)

## Dev Notes

### New Error Types in `app/core/errors.py`

```python
class InvalidUrlError(ResiliError):
    status_code = 400
    error_code = "INVALID_URL"
    message = "The provided URL is not valid"
    hint = "Ensure the URL starts with http:// or https:// and is properly formatted"
    docs_url = "https://docs.resili.io/errors/invalid-url"


class TargetNotFoundError(ResiliError):
    status_code = 200  # Return 200 with error in body per ScrapeResponse shape
    error_code = "TARGET_NOT_FOUND"
    message = "The target URL returned a 404 Not Found response"
    hint = "Verify the URL is accessible and try again"
    docs_url = "https://docs.resili.io/errors/target-not-found"
    # Note: For scraping errors, we return HTTP 200 with error body (FR-07)
    # This matches the Dec-F ScrapeResponse shape compatibility


class AntiBotDetectedError(ResiliError):
    status_code = 200
    error_code = "ANTI_BOT_DETECTED"
    message = "Anti-bot protection detected on the target page"
    hint = "Use /api/v1/scrape/dynamic for JS-heavy or bot-protected pages"
    docs_url = "https://docs.resili.io/errors/anti-bot-detected"
```

**Note on status codes:** FR-07 says "API trả về error JSON với field `message` human-readable". The error schema (Dec-D) is used with appropriate HTTP codes. For target-level errors (404, anti-bot), consider returning HTTP 200 with `status: "error"` in the ScrapeResponse body for consistency with Dec-F, or HTTP 4xx with Dec-D. This story uses HTTP 4xx for clarity.

### URL Validation in Schema (AC: 2)

```python
# app/scraping/schemas.py
from pydantic import BaseModel, field_validator
from urllib.parse import urlparse

class FetchRequest(BaseModel):
    url: str
    format: Literal["markdown", "json"] = "markdown"
    respect_robots_txt: bool = False

    @field_validator("url")
    @classmethod
    def validate_url_format(cls, v: str) -> str:
        parsed = urlparse(v)
        if not parsed.scheme or not parsed.netloc:
            raise ValueError("URL must include scheme (http/https) and hostname")
        if parsed.scheme not in ("http", "https"):
            raise ValueError("URL must use http or https scheme")
        return v
```

This Pydantic validation raises HTTP 422 by default. To return HTTP 400 with `INVALID_URL` code, override in exception handler or use a custom validator:

```python
# In scrape.py handler:
@router.post("/fetch")
async def fetch_page(body: FetchRequest, ...):
    try:
        parsed = urlparse(body.url)
        if not parsed.scheme or not parsed.netloc:
            raise InvalidUrlError()
    except Exception:
        raise InvalidUrlError()
    ...
```

### Anti-Bot Detection in Fetcher (AC: 4)

Scrapling returns specific status codes or raises exceptions for bot-blocked pages. Detect by:
```python
# app/scraping/fetcher.py
async def fetch_url(url: str, respect_robots_txt: bool = False) -> str:
    def _sync_fetch():
        fetcher = Fetcher(respect_robots_txt=respect_robots_txt)
        try:
            page = fetcher.get(url)
            
            # Check for anti-bot signals
            if page.status_code == 404:
                raise TargetNotFoundError()
            if page.status_code in (403, 429) or _has_antibot_signals(page.html_content):
                raise AntiBotDetectedError()
                
            return page.html_content
        except (TargetNotFoundError, AntiBotDetectedError):
            raise
        except Exception as e:
            raise ScrapingError(message=f"Fetcher failed: {str(e)[:200]}")

    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, _sync_fetch)


def _has_antibot_signals(html: str) -> bool:
    """Heuristic detection of anti-bot pages."""
    signals = ["cloudflare", "recaptcha", "captcha", "bot detection", "access denied"]
    html_lower = html.lower()
    return any(signal in html_lower for signal in signals)
```

### CreditsExhaustedError — Message Specificity (AC: 5)

Update `CreditsExhaustedError` to include endpoint_type context:
```python
class CreditsExhaustedError(ResiliError):
    status_code = 429
    error_code = "CREDITS_EXHAUSTED"

    def __init__(self, reset_date: str = "", retry_after: int = 0, endpoint_type: str = "fetcher"):
        self.reset_date = reset_date
        self.retry_after = retry_after
        credit_type = "fetcher credits" if endpoint_type == "fetcher" else "dynamic credits"
        self.message = f"Your {credit_type} for this month are exhausted. They reset on {reset_date}" if reset_date \
                       else "Your credits for this month are exhausted"
        self.hint = f"Upgrade to Pro or wait until {reset_date} for credit reset"
```

### Dec-D Schema Verification Checklist

Every error response MUST have:
```json
{
  "error": {
    "code": "SCREAMING_SNAKE_CASE",
    "message": "Human-readable description",
    "hint": "Suggested action",
    "docs_url": "https://docs.resili.io/errors/<code-lowercase>"
  }
}
```

Verify via test:
```python
async def test_all_errors_follow_dec_d_schema(client: AsyncClient, api_key_headers: dict):
    """Test various error scenarios return Dec-D schema."""
    test_cases = [
        ({"url": "not-a-url"}, 400, "INVALID_URL"),
        ({"url": "http://192.168.1.1/"}, 400, "SSRF_BLOCKED"),
    ]
    for body, expected_status, expected_code in test_cases:
        response = await client.post("/api/v1/scrape/fetch", headers=api_key_headers, json=body)
        assert response.status_code == expected_status
        data = response.json()
        assert "error" in data
        assert "code" in data["error"]
        assert "message" in data["error"]
        assert "hint" in data["error"]
        assert "docs_url" in data["error"]
        assert data["error"]["code"] == expected_code
```

### References

- [Source: architecture.md#Dec-D-Error-Response-Schema] — mandatory schema
- [Source: epics.md#Story-3.5] — acceptance criteria
- [Source: architecture.md#Enforcement-Guidelines] — error handling patterns

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/core/errors.py` — add InvalidUrlError, TargetNotFoundError, AntiBotDetectedError; update CreditsExhaustedError
- `backend/app/scraping/fetcher.py` — add anti-bot and 404 detection
- `backend/app/scraping/schemas.py` — add URL format validation

**NEW:**
- `backend/tests/api/test_scrape_errors.py`
