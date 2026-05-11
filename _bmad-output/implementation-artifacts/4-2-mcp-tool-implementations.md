# Story 4.2: MCP Tool Implementations

Status: ready-for-dev

## Story

As an AI agent,
I want clearly-described MCP tools for fetching static and dynamic web pages,
so that I can autonomously select the right tool based on the task context without human guidance.

## Acceptance Criteria

1. **Given** the MCP server is running, **When** tools are listed, **Then** both `fetch_page` and `fetch_dynamic_page` tools are present.

2. **Given** the `fetch_page` tool description, **When** read by an LLM, **Then** it clearly conveys: "Use for static pages, documentation, news articles — no JavaScript rendering required. Fast (1–3s). Costs 1 credit."

3. **Given** the `fetch_dynamic_page` tool description, **When** read by an LLM, **Then** it clearly conveys: "Use for JavaScript-heavy pages, SPAs, dashboards that require browser rendering. Slower (5–15s). Costs 5 credits. Requires Pro tier."

4. **Given** `fetch_page(url="https://example.com", format="markdown")` MCP tool call with a valid key, **When** executed, **Then** the response matches the REST API ScrapeResponse schema: `{"job_id": null, "status": "completed", "result": {...}}`.

5. **Given** `fetch_dynamic_page` MCP tool call with a Free tier key, **When** executed, **Then** the MCP error response contains a message equivalent to HTTP 403 `DYNAMIC_NOT_AVAILABLE_FREE_TIER`.

## Tasks / Subtasks

- [ ] Verify tool descriptions are LLM-optimized (AC: 2, 3)
  - [ ] `fetch_page`: explicitly state "no JavaScript", "Fast (1-3s)", "Costs 1 credit"
  - [ ] `fetch_dynamic_page`: explicitly state "requires browser rendering", "Slower (5-15s)", "Costs 5 credits", "Requires Pro tier"

- [ ] Implement credit checking in MCP tool handler (AC: 5)
  - [ ] `mcp_server.py`: check user tier/credits before calling Dynamic
  - [ ] Return proper MCP error for Free tier attempting Dynamic

- [ ] Ensure ScrapeResponse shape in MCP response (AC: 4)
  - [ ] Tool response must include `job_id`, `status`, `result` fields

- [ ] Viết tests (AC: 1, 2, 3, 4, 5)

## Dev Notes

### Tool Description Optimization (AC: 2, 3)

LLM tool selection depends on description clarity. These descriptions are CRITICAL:

```python
Tool(
    name="fetch_page",
    description="""Fetch and convert a web page to clean Markdown or JSON.

USE THIS FOR:
- Static HTML pages (documentation, blogs, news articles, product pages)
- Pages that don't require JavaScript to display content
- Fast fetches where speed matters (1-3 seconds)

DO NOT USE FOR:
- Single Page Applications (SPAs) built with React/Vue/Angular
- Pages requiring login with dynamic content
- Dashboards with real-time data

Cost: 1 credit per call.
Speed: 1-3 seconds.""",
    ...
),

Tool(
    name="fetch_dynamic_page",
    description="""Fetch and render a JavaScript-heavy web page using a full browser (Playwright).

USE THIS FOR:
- Single Page Applications (SPAs) built with React/Vue/Angular
- Pages that load content via JavaScript/AJAX after initial render
- Dashboards, user portals, dynamic content sites
- Pages with infinite scroll or lazy loading

DO NOT USE FOR:
- Simple static pages (use fetch_page instead — it's faster and cheaper)

Cost: 5 credits per call (5x fetch_page).
Speed: 5-15 seconds.
Requirement: Pro tier account only. Free tier will receive an error.""",
    ...
),
```

### Credit/Tier Check in MCP Handler (AC: 5)

MCP server không có direct DB access via SQLAlchemy async session. Options:

**Option A (Simple — call billing service directly with async):**
```python
# In call_tool handler for fetch_dynamic_page:
from app.billing.models import CreditBalance
from app.auth.models import User, ApiKey
# Set up DB session for MCP context
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from app.core.config import settings

async def _check_dynamic_tier(api_key: str) -> None:
    """Check if user has Pro tier for Dynamic access."""
    from app.core.security import hash_api_key
    from sqlalchemy import select

    engine = create_async_engine(settings.DATABASE_URL)
    async with AsyncSession(engine) as db:
        key_hash = hash_api_key(api_key)
        result = await db.execute(
            select(ApiKey).where(ApiKey.key_hash == key_hash, ApiKey.is_active == True)
        )
        api_key_obj = result.scalar_one_or_none()
        if not api_key_obj:
            raise McpError(ErrorCode.InvalidParams, "INVALID_API_KEY: API key not found or inactive")

        result = await db.execute(
            select(User).where(User.id == api_key_obj.user_id)
        )
        user = result.scalar_one_or_none()
        if user and user.tier == "free":
            raise McpError(
                ErrorCode.InvalidParams,
                "DYNAMIC_NOT_AVAILABLE_FREE_TIER: DynamicFetcher requires Pro tier. Upgrade at https://resili.io/dashboard"
            )
```

**Option B (Simple — read tier from environment):**
If the MCP server is configured per-user (with `RESILI_API_KEY` per user), validate the key against the REST API as a pre-check. This is simpler but makes an HTTP call.

**Recommendation:** Option A (direct DB) for consistency with Dec-E (no HTTP calls). The MCP server IS allowed to share DB access with the app.

### ScrapeResponse Shape in MCP (AC: 4)

MCP tool responses are `list[TextContent]`. To maintain Dec-F shape:

```python
import json

result_data = {
    "job_id": None,
    "status": "completed",
    "result": {
        "content": content,
        "format": fmt,
        "credits_used": 1,
    }
}
return [TextContent(type="text", text=json.dumps(result_data, ensure_ascii=False))]
```

The client (Claude/Cursor) receives the JSON string as text. This is standard MCP pattern — tools return text, structured data is in the text.

### RESILI_API_KEY Environment Variable

MCP server reads the API key from environment:
```python
import os
RESILI_API_KEY = os.environ.get("RESILI_API_KEY")
if not RESILI_API_KEY:
    print("ERROR: RESILI_API_KEY environment variable not set", file=sys.stderr)
    sys.exit(1)
```

### References

- [Source: epics.md#Story-4.2] — acceptance criteria
- [Source: architecture.md#Dec-E-MCP-Server-Process-Model] — no HTTP calls
- [Source: epics.md#FR-09] — tool descriptions must enable LLM tool selection

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/mcp_server.py` — improve tool descriptions, add tier check, fix response shape
