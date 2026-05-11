# Story 2.6: SSRF Protection Guard

Status: ready-for-dev

## Story

As the Resili API,
I want to block requests targeting private or internal IP addresses,
so that the scraping endpoints cannot be abused to probe internal network resources.

## Acceptance Criteria

1. **Given** `validate_url("http://192.168.1.1/data")`, **When** called, **Then** `SSRFBlockedError` is raised (RFC 1918 block).

2. **Given** `validate_url("http://10.0.0.1/internal")`, **When** called, **Then** `SSRFBlockedError` is raised (10.x/8 RFC 1918 range).

3. **Given** `validate_url("http://127.0.0.1/local")`, **When** called, **Then** `SSRFBlockedError` is raised (localhost).

4. **Given** `validate_url("http://169.254.169.254/latest/meta-data/")`, **When** called, **Then** `SSRFBlockedError` is raised (AWS metadata link-local).

5. **Given** `validate_url("http://[::1]/")`, **When** called, **Then** `SSRFBlockedError` is raised (IPv6 localhost).

6. **Given** `validate_url("https://example.com/page")`, **When** called, **Then** no exception is raised (valid public URL passes through).

7. **Given** both `POST /api/v1/scrape/fetch` and `POST /api/v1/scrape/dynamic`, **When** reviewed, **Then** `validate_url()` is invoked **before** any network connection is attempted.

## Tasks / Subtasks

- [ ] Implement `app/core/ssrf_guard.py` (AC: 1-6)
  - [ ] `validate_url(url: str) -> str` — parse URL, resolve hostname, check IP ranges
  - [ ] Block: RFC 1918, localhost/loopback, link-local (169.254.x.x), IPv6 private
  - [ ] Valid public URL returns the url string unchanged

- [ ] Wire validate_url into scrape endpoints (AC: 7)
  - [ ] `app/api/v1/scrape.py`: call `validate_url(body.url)` before any scraping
  - [ ] Or wire into `scraping/service.py` as first step in pipeline

- [ ] Viết comprehensive tests (AC: 1-7)
  - [ ] `backend/tests/scraping/test_ssrf_guard.py`

## Dev Notes

### `app/core/ssrf_guard.py` — Complete Implementation

```python
import ipaddress
import socket
from urllib.parse import urlparse
from app.core.errors import SSRFBlockedError

# RFC 1918 private ranges + special ranges to block
_BLOCKED_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),       # RFC 1918
    ipaddress.ip_network("172.16.0.0/12"),     # RFC 1918
    ipaddress.ip_network("192.168.0.0/16"),    # RFC 1918
    ipaddress.ip_network("127.0.0.0/8"),       # Loopback
    ipaddress.ip_network("169.254.0.0/16"),    # Link-local (AWS metadata)
    ipaddress.ip_network("0.0.0.0/8"),         # This network
    ipaddress.ip_network("100.64.0.0/10"),     # Shared address space
    ipaddress.ip_network("::1/128"),            # IPv6 loopback
    ipaddress.ip_network("fc00::/7"),           # IPv6 private
    ipaddress.ip_network("fe80::/10"),          # IPv6 link-local
]


def _is_private_ip(ip_str: str) -> bool:
    """Returns True if the IP address is in a blocked range."""
    try:
        ip = ipaddress.ip_address(ip_str)
        return any(ip in network for network in _BLOCKED_NETWORKS)
    except ValueError:
        return True  # Invalid IP = block


def validate_url(url: str) -> str:
    """
    Validates URL is safe to scrape (not SSRF target).
    Returns url unchanged if valid. Raises SSRFBlockedError if blocked.
    """
    try:
        parsed = urlparse(url)
    except Exception:
        raise SSRFBlockedError(message="URL could not be parsed")

    if parsed.scheme not in ("http", "https"):
        raise SSRFBlockedError(message="Only http and https URLs are allowed")

    hostname = parsed.hostname
    if not hostname:
        raise SSRFBlockedError(message="URL must have a valid hostname")

    # Check raw hostname if it's an IP address directly
    try:
        # If hostname is an IP address (IPv4 or IPv6)
        ip = ipaddress.ip_address(hostname)
        if _is_private_ip(str(ip)):
            raise SSRFBlockedError(
                message=f"Requests to private IP addresses are not allowed: {hostname}"
            )
        return url
    except ValueError:
        pass  # Not a direct IP — resolve the hostname

    # DNS resolution — check resolved IP(s)
    try:
        # getaddrinfo returns list of (family, type, proto, canonname, sockaddr)
        addr_infos = socket.getaddrinfo(hostname, None)
        for addr_info in addr_infos:
            ip_str = addr_info[4][0]
            if _is_private_ip(ip_str):
                raise SSRFBlockedError(
                    message=f"URL resolves to a private IP address: {ip_str}"
                )
    except socket.gaierror:
        # DNS resolution failed — block it (fail safe)
        raise SSRFBlockedError(message=f"Could not resolve hostname: {hostname}")

    return url
```

**CRITICAL:** `validate_url()` phải được gọi TRƯỚC mọi network call trong scraping pipeline.

### Wire into Scraping Service (AC: 7)

```python
# app/scraping/service.py
from app.core.ssrf_guard import validate_url
from app.core.errors import SSRFBlockedError

async def scrape_page(url: str, format: str, user: User, db: AsyncSession) -> dict:
    # FIRST: validate URL (SSRF protection)
    validate_url(url)  # Raises SSRFBlockedError if blocked
    
    # Then: credit check, scraping, etc.
    ...
```

Hoặc trong route handler nếu chưa có service layer:
```python
@router.post("/fetch")
async def fetch_page(body: FetchRequest, user: User = Depends(...)):
    validate_url(body.url)  # Before any async scraping
    ...
```

### Test Cases — Comprehensive Coverage

```python
import pytest
from app.core.ssrf_guard import validate_url
from app.core.errors import SSRFBlockedError


@pytest.mark.parametrize("url,should_block", [
    # RFC 1918 — must block
    ("http://192.168.1.1/data", True),
    ("http://10.0.0.1/internal", True),
    ("http://172.16.0.1/", True),
    ("http://172.31.255.255/", True),
    # Localhost — must block
    ("http://127.0.0.1/local", True),
    ("http://localhost/", True),
    # Link-local (AWS metadata) — must block
    ("http://169.254.169.254/latest/meta-data/", True),
    # IPv6 loopback — must block
    ("http://[::1]/", True),
    # Public — must pass
    ("https://example.com/page", False),
    ("https://api.github.com/repos", False),
    # Invalid scheme — must block
    ("ftp://example.com/", True),
    ("file:///etc/passwd", True),
])
async def test_ssrf_validation(url: str, should_block: bool):
    if should_block:
        with pytest.raises(SSRFBlockedError):
            validate_url(url)
    else:
        result = validate_url(url)
        assert result == url
```

### Integration Test — Scrape Endpoint

```python
async def test_ssrf_blocked_via_api(client: AsyncClient, api_key_headers: dict):
    response = await client.post(
        "/api/v1/scrape/fetch",
        headers=api_key_headers,
        json={"url": "http://192.168.1.1/internal", "format": "markdown"}
    )
    assert response.status_code == 400
    assert response.json()["error"]["code"] == "SSRF_BLOCKED"
```

### DNS Rebinding Defense Note

DNS rebinding attacks (where DNS initially resolves to public IP, then rebinds to private) are a known SSRF vector. The current implementation resolves DNS at request time, which provides basic protection. For production-grade defense, consider using a pinned DNS resolver or checking IP at scrape time. This is noted in architecture as future enhancement.

### References

- [Source: architecture.md#Dec-B-SSRF-Protection] — block ranges and position
- [Source: architecture.md#Enforcement-Guidelines] — NFR-08
- [Source: epics.md#Story-2.6] — acceptance criteria
- [Source: architecture.md#Scrape-Request-Flow] — ssrf_guard.validate_url() is first step

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/api/v1/scrape.py` — add validate_url call

**NEW:**
- `backend/app/core/ssrf_guard.py`
- `backend/tests/scraping/__init__.py`
- `backend/tests/scraping/test_ssrf_guard.py`
