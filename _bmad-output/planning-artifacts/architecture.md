---
stepsCompleted: [1, 2, 3, 4, 5, 6, 7, 8]
lastStep: 8
status: 'complete'
completedAt: '2026-05-11'
inputDocuments: ['docs/report.md']
workflowType: 'architecture'
project_name: 'resili'
user_name: 'Viet An'
date: '2026-05-10'
---

# Architecture Decision Document

_This document builds collaboratively through step-by-step discovery. Sections are appended as we work through each architectural decision together._

## Project Context Analysis

### Requirements Overview

**Functional Requirements (16 tổng):**

*Auth & Access (FR-01–03):* API key CRUD từ dashboard, xác thực mỗi request qua Authorization header, credit usage real-time theo Fetcher/Dynamic breakdown. Kiến trúc: middleware auth stateless với key lookup nhanh (cache/hashed store).

*Core Scraping API (FR-04–07):* Hai endpoint độc lập — Fetcher (HTTP, trang tĩnh) và DynamicFetcher (Playwright, JS-heavy). Output format Markdown/JSON configurable. Error response có human-readable message + troubleshooting link. Kiến trúc: hai service/worker riêng biệt với shared output formatting layer.

*MCP Integration (FR-08–10):* MCP stdio transport expose 2 tools (`fetch_page`, `fetch_dynamic_page`) với description đủ rõ cho LLM tool selection. Kiến trúc: MCP server là adapter layer gọi vào cùng core scraping logic của REST API.

*Rate Limiting & Pricing (FR-11–15):* Free tier (1,000 Fetcher credits/tháng, no Dynamic), credit multiplier (1 Dynamic = 5 Fetcher), HTTP 429 với Retry-After, email alert 80% quota, 1-click upgrade. Kiến trúc: credit deduction phải atomic và pre-request (check-then-deduct hoặc reserve-then-confirm).

*Dashboard (FR-16):* Usage visualization Fetcher/Dynamic theo ngày/tuần/tháng. Kiến trúc: read model tách từ write path để không ảnh hưởng API latency.

**Non-Functional Requirements (12 tổng):**

- **Availability:** 99.5% uptime, external monitoring, planned maintenance 24h notice
- **Performance:** Fetcher ≤ 3s p95 / DynamicFetcher ≤ 15s p95 dưới tải bình thường
- **Isolation:** Mỗi DynamicFetcher request chạy isolated process, timeout 30s, memory cap
- **Scalability:** Horizontal scaling, 10x spike không downtime
- **Security:** HTTPS/TLS 1.2+, API key hashed, SSRF protection tại gateway, input sanitization
- **Data retention:** Không lưu content; metadata (timestamp, URL hash, credit) 90 ngày
- **Async migration path (NFR-12):** API contract MVP không được block growth-phase async job queue

**Scale & Complexity:**

- Primary domain: API Service + Background Processing (Playwright)
- Complexity level: **Medium-High**
- Estimated architectural components: API Gateway, Auth/Key Service, Fetcher Worker, DynamicFetcher Worker (Playwright pool), Credit/Billing Service, Dashboard Service, MCP Server Adapter, Notification Service (email), Observability Stack

### Technical Constraints & Dependencies

- **Scrapling v0.4.7 fork (BSD):** Core parsing/fetching engine; phải maintain BSD attribution
- **Playwright:** Browser runtime cho DynamicFetcher; cần browser-capable Docker images, isolated processes
- **Stripe:** Metered billing; credit events phải sync với Stripe usage records
- **MCP stdio transport:** Protocol constraint cho AI Agent integration
- **Docker/container orchestration:** Required cho horizontal scaling và DynamicFetcher isolation

### Cross-Cutting Concerns Identified

1. **Authentication:** API key validation trên mọi request (REST + MCP)
2. **Credit accounting:** Atomic deduction trước khi scrape; không được over-charge hoặc miss-charge
3. **Error handling:** Human-readable messages với suggested action — cần error taxonomy nhất quán
4. **SSRF protection:** URL validation tại gateway trước khi đến scraping layer
5. **Observability:** APM latency tracking, uptime monitoring, credit usage events — cần instrumentation đồng nhất
6. **Async migration readiness:** DynamicFetcher API design phải support future job-ID + callback model

## Starter Template Evaluation

### Primary Technology Domain

**Hybrid Stack:** Python API Backend + TypeScript/React Frontend — monorepo với hai sub-project riêng biệt.

### Starter Options Đã Xem Xét

| Option | Mô tả | Quyết định |
|--------|--------|------------|
| `vintasoftware/nextjs-fastapi-template` | Type-safe full-stack, Zod↔Pydantic sync, pre-configured auth | Loại — thiếu async worker pattern, cần thêm nhiều cho Playwright/billing |
| `next-fast-turbo` (Turborepo) | Next.js + FastAPI + Docs trong Turborepo | Loại — docs layer thừa, opinionated về Vercel |
| **Custom Monorepo** | `create-next-app` + FastAPI official template | **Chọn** — kiểm soát hoàn toàn, phù hợp requirements đặc thù |

**Lý do chọn Custom Monorepo:** Resili có requirements đủ đặc thù (MCP protocol, Playwright worker isolation, credit accounting, async migration path) khiến bất kỳ opinionated starter nào cũng cần stripped down đáng kể. Custom setup cho foundation sạch hơn.

### Selected Starter: Custom Monorepo

**Initialization Commands:**

```bash
# Root monorepo
mkdir resili && cd resili && git init

# Frontend
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint \
  --app --src-dir --import-alias "@/*"

# Backend
mkdir backend && cd backend
python -m venv .venv
pip install "fastapi[standard]" sqlalchemy alembic pydantic-settings \
  psycopg[binary] scrapling playwright
playwright install chromium
```

**Architectural Decisions Provided by Starter:**

**Language & Runtime:**
- Backend: Python 3.13 + FastAPI (latest), async/await throughout
- Frontend: TypeScript, Next.js App Router, Turbopack (dev)
- ORM: SQLAlchemy 2.0 async + Alembic migrations

**Project Structure:**
```
resili/
├── backend/
│   ├── app/
│   │   ├── api/           # FastAPI routers
│   │   ├── auth/          # API key management
│   │   ├── scraping/      # Fetcher + DynamicFetcher logic
│   │   ├── billing/       # Credit accounting + Stripe
│   │   ├── mcp/           # MCP server adapter
│   │   ├── notifications/ # Email alerts
│   │   ├── db/            # SQLAlchemy models + session
│   │   └── core/          # Config, security, SSRF guard
│   ├── workers/           # Playwright pool (Celery-ready)
│   ├── Dockerfile
│   └── Dockerfile.worker  # Browser-capable image
├── frontend/
│   ├── src/app/           # Next.js App Router
│   ├── src/components/
│   └── Dockerfile
├── docker-compose.yml
└── .devcontainer/
```

**Styling Solution:** Tailwind CSS (via create-next-app)

**Build Tooling:** Turbopack (Next.js dev), Uvicorn (dev) / Gunicorn + Uvicorn workers (production)

**Testing Framework:** pytest + httpx (backend), Jest + Playwright E2E (frontend)

**Development Setup (Docker Compose):**
```yaml
services:
  api:      FastAPI + uvicorn --reload
  worker:   Playwright worker (sync MVP, Celery-ready structure)
  frontend: Next.js dev server
  db:       PostgreSQL 16
  redis:    Redis (API key cache, future job queue)
```

**Deployment:**
- **Dev/MVP:** Railway — GitHub repo → live trong vài phút, managed PostgreSQL
- **Production:** Render (predictable cost) hoặc Fly.io (global scale)
- **Frontend option:** Vercel (optimal cho Next.js) + Railway/Render cho backend riêng

**Note:** Project initialization, monorepo scaffold, và Docker Compose setup nên là implementation story đầu tiên.

## Core Architectural Decisions

### Decision Priority Analysis

**Critical Decisions (Block Implementation):**
- API key format, hashing, storage strategy
- Credit accounting atomicity model
- SSRF protection approach
- MCP server process model
- DynamicFetcher async-ready response shape

**Important Decisions (Shape Architecture):**
- Error response schema chuẩn hóa
- API versioning strategy
- Frontend state management
- Observability stack
- Email provider

**Deferred Decisions (Post-MVP):**
- Celery task queue (Growth phase — khi DynamicFetcher chuyển sang async)
- SDK chính thức (Python, TypeScript) — Vision phase
- Team/multi-key support — Growth phase

---

### Authentication & Security

**[Dec-A] API Key Format & Storage**
- Format: `rsl_` prefix + 32 random bytes (URL-safe base64) → `rsl_aB3xK9mP...`
- Hashing: SHA-256 (không dùng bcrypt — key là random string, không phải password user-chosen; SHA-256 nhanh hơn, đủ an toàn)
- Storage: chỉ lưu hash; plaintext trả về 1 lần duy nhất khi tạo (NFR-07)
- Lookup: hash incoming key → query DB → O(1) indexed lookup
- Rationale: Prefix dễ nhận dạng trong logs; SHA-256 đủ entropy cho random key

**[Dec-B] SSRF Protection**
- Implement: URL validation middleware Python thuần, chạy trước khi URL đến Scrapling
- Block: private IP ranges RFC 1918 (`10.x`, `172.16-31.x`, `192.168.x`), localhost (`127.x`, `::1`), link-local (`169.254.x` — AWS metadata), IPv6 private ranges
- Position: `app/core/ssrf_guard.py` — inject vào cả Fetcher và DynamicFetcher endpoints
- Rationale: SSRF block phải xảy ra tại API layer, trước bất kỳ network call nào (NFR-08)

---

### API & Communication Patterns

**[Dec-C] API Versioning**
- Strategy: `/api/v1/` prefix từ ngày đầu
- Rationale: Dù MVP, tránh breaking change sau này; cost thêm 0 khi implement ngay từ đầu

**[Dec-D] Error Response Schema**
- Chuẩn JSON thống nhất cho toàn bộ API và MCP:
```json
{
  "error": {
    "code": "ANTI_BOT_DETECTED",
    "message": "Anti-bot protection detected. Try DynamicFetcher.",
    "hint": "Use /api/v1/scrape/dynamic for JS-heavy pages",
    "docs_url": "https://docs.resili.io/errors/anti-bot"
  }
}
```
- Error codes: SCREAMING_SNAKE_CASE, defined trong `app/core/errors.py`
- Rationale: Nhất quán giữa REST và MCP; `hint` + `docs_url` thực hiện UJ-04 (error recovery ≤ 2 phút)

**[Dec-E] MCP Server Process Model**
- Decision: **Separate process** — standalone Python script (`backend/mcp_server.py`)
- Gọi vào cùng core scraping functions (`app/scraping/`) qua direct import (không qua HTTP)
- Rationale: Tách biệt hoàn toàn khỏi FastAPI; MCP crash không ảnh hưởng API uptime; dễ deploy riêng nếu cần

**[Dec-F] DynamicFetcher Async-Ready Response Shape**
- MVP response (synchronous):
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
- Growth phase: `job_id: "uuid-v4"`, `status: "pending"` → client poll `/api/v1/jobs/{job_id}`
- Rationale: `job_id: null` convention cho phép client code tương thích cả hai mode (NFR-12)

---

### Data Architecture

**[Dec-G] Credit Accounting Atomicity**
- Pattern: PostgreSQL `SELECT FOR UPDATE` trong DB transaction — atomic check-and-deduct
- Redis cache: cache current balance (TTL 60s), invalidate ngay sau mỗi deduction thành công
- Rationale: Tránh over-charge race condition; Redis giảm hot-row pressure trên PostgreSQL ở 100 concurrent requests

**[Dec-H] Usage Events Schema**
- Table: `usage_events (id, user_id, endpoint_type, credits_used, url_hash, status, created_at)`
- Không lưu URL gốc — chỉ SHA-256 hash (privacy + NFR-09)
- Append-only: không update, không delete (audit trail)
- Retention: scheduled job prune records `created_at < NOW() - INTERVAL '90 days'` (NFR-09)
- Read model: materialized view hoặc aggregation query cho dashboard (tách khỏi write path)

---

### Frontend Architecture

**[Dec-I] Server State Management**
- Library: **TanStack Query v5** (React Query)
- Rationale: Perfect fit cho dashboard SaaS — API data fetching, cache, background refetch, loading states. Không cần Zustand/Redux vì dashboard không có complex shared client state

**[Dec-J] Dashboard Charts**
- Library: **Recharts**
- Rationale: React-native, composable, works tốt với Tailwind, nhẹ hơn Chart.js, sufficient cho usage graphs (line/bar)

**[Dec-K] API Client**
- Strategy: Auto-generate typed client từ FastAPI's OpenAPI spec dùng **openapi-typescript**
- Rationale: Type-safe, luôn sync với backend schema, không viết tay types

---

### Infrastructure & Deployment

**[Dec-L] Email Provider**
- Provider: **Resend**
- Rationale: Developer-friendly, 3,000 emails/tháng free tier, React Email templates, SDK đơn giản, dễ setup hơn SendGrid cho MVP

**[Dec-M] Error Monitoring**
- Provider: **Sentry** (free tier)
- Coverage: cả Python backend (FastAPI) và Next.js frontend
- Rationale: Error grouping, alerting, performance tracing; free tier đủ cho MVP

**[Dec-N] Uptime Monitoring**
- Provider: **BetterUptime** hoặc **UptimeRobot** (free tier)
- Mục đích: External monitoring để đo và track NFR-01 (99.5% uptime SLA)

**[Dec-O] CI/CD Pipeline**
- Platform: **GitHub Actions**
- Pipeline: test → lint → build → deploy to Railway/Render
- Rationale: Free, native với GitHub, zero additional tooling

---

### Decision Impact Analysis

**Implementation Sequence:**
1. Monorepo scaffold + Docker Compose (foundation cho mọi thứ)
2. DB schema + migrations (Alembic) — users, api_keys, usage_events, credit_balances
3. Auth middleware (Dec-A) + SSRF guard (Dec-B)
4. Fetcher endpoint với credit deduction (Dec-G) và error schema (Dec-D)
5. DynamicFetcher endpoint với async-ready shape (Dec-F)
6. MCP server process (Dec-E)
7. Dashboard frontend với TanStack Query (Dec-I) + Recharts (Dec-J)
8. Stripe billing integration + Resend email (Dec-L)
9. Sentry + uptime monitoring (Dec-M, Dec-N)
10. GitHub Actions CI/CD (Dec-O)

**Cross-Component Dependencies:**
- Dec-A (API key hashing) → ảnh hưởng Auth middleware + DB schema
- Dec-G (credit accounting) → phải implement trước bất kỳ scraping endpoint nào
- Dec-F (async-ready shape) → ảnh hưởng API contract, frontend client type, MCP tool response
- Dec-D (error schema) → phải define trước implementation để nhất quán; ảnh hưởng cả REST lẫn MCP
- Dec-K (openapi-typescript) → generate sau khi FastAPI routes ổn định

## Implementation Patterns & Consistency Rules

**Potential conflict points đã xác định:** 6 vùng xung đột nơi AI agents có thể đưa ra quyết định khác nhau.

---

### Naming Patterns

**Database Naming Conventions:**
- Tables: `snake_case`, **plural** → `users`, `api_keys`, `usage_events`, `credit_balances`
- Columns: `snake_case` → `user_id`, `created_at`, `credits_used`, `endpoint_type`
- Foreign keys: `{table_singular}_id` → `user_id` (không phải `fk_user_id`)
- Indexes: `ix_{table}_{column}` → `ix_api_keys_user_id`, `ix_usage_events_created_at`
- Primary key: luôn là `id` (UUID hoặc BIGSERIAL tùy table)

**API Endpoint Naming:**
- Plural resource nouns: `/api/v1/keys`, `/api/v1/usage`
- Actions trên resource: `/api/v1/scrape/fetch`, `/api/v1/scrape/dynamic`
- HTTP verbs mapping: `GET` list/retrieve, `POST` create/action, `DELETE` remove
- Path params: `{key_id}`, `{job_id}` (snake_case, không camelCase)
- Query params: `snake_case` → `?page_size=20&endpoint_type=dynamic`

**JSON API Field Naming:**
- **snake_case xuyên suốt** cả request lẫn response → `credits_used`, `created_at`, `api_key`, `job_id`
- Rationale: đồng nhất với Python/DB convention; openapi-typescript handle types phía frontend
- Không dùng camelCase trong JSON dù frontend là TypeScript

**Python Code Naming:**
- Modules/files: `snake_case` → `ssrf_guard.py`, `credit_service.py`
- Functions/variables: `snake_case` → `get_current_user()`, `credits_used`
- Classes: `PascalCase` → `CreditService`, `APIKeyCreate`
- Constants: `UPPER_SNAKE_CASE` → `MAX_CONCURRENT_PLAYWRIGHT`, `CREDIT_MULTIPLIER`

**TypeScript/React Naming:**
- Component files: `kebab-case` → `dashboard-chart.tsx`, `api-key-card.tsx`
- Component exports: `PascalCase` → `DashboardChart`, `ApiKeyCard`
- Variables/functions: `camelCase` → `creditsUsed`, `fetchPageData`
- Custom hooks: `use` prefix → `useApiKeys()`, `useUsageData()`
- Types/interfaces: `PascalCase` → `ApiKey`, `UsageEvent`, `ScrapeResponse`

---

### Structure Patterns

**Backend File Organization:**
```
backend/app/
├── api/v1/              # Routers ONLY — no business logic in route handlers
│   ├── scrape.py        # POST /scrape/fetch, POST /scrape/dynamic
│   ├── keys.py          # GET/POST/DELETE /keys
│   └── usage.py         # GET /usage
├── scraping/
│   ├── service.py       # business logic (gọi từ router qua Depends)
│   ├── schemas.py       # Pydantic request/response models
│   ├── fetcher.py       # Scrapling Fetcher wrapper
│   └── dynamic.py       # Playwright DynamicFetcher wrapper
├── auth/
│   ├── service.py
│   ├── schemas.py
│   └── models.py        # SQLAlchemy models
├── billing/
│   ├── service.py       # credit deduction, Stripe events
│   ├── schemas.py
│   └── models.py
├── core/
│   ├── config.py        # pydantic-settings Settings class
│   ├── security.py      # SHA-256 key hashing, key generation
│   ├── ssrf_guard.py    # URL validation middleware
│   └── errors.py        # Custom exceptions + FastAPI exception handlers
└── db/
    ├── session.py       # AsyncSession factory
    └── base.py          # DeclarativeBase
backend/tests/           # Mirror app/ structure
    ├── api/
    ├── scraping/
    └── billing/
```

**Frontend File Organization:**
```
frontend/src/
├── app/                 # Next.js App Router — pages only, no business logic
│   ├── (auth)/          # route groups
│   └── dashboard/
├── components/
│   ├── ui/              # generic shadcn/tailwind components
│   └── dashboard/       # domain-specific (UsageChart, ApiKeyList, ...)
├── lib/
│   ├── api/             # openapi-typescript generated types + fetch wrappers
│   └── utils.ts         # shared utilities
└── hooks/               # custom React hooks (useApiKeys, useUsage, ...)
```

Test files: co-located với component → `dashboard-chart.test.tsx` bên cạnh `dashboard-chart.tsx`

---

### Format Patterns

**Success Response — không wrap:**
```json
// ✅ Direct object
{ "total_credits": 850, "fetcher_calls": 820, "dynamic_calls": 6 }

// ❌ Không wrap
{ "data": { "total_credits": 850 }, "success": true }
```

**List Response:**
```json
{ "items": [...], "total": 42, "page": 1, "page_size": 20 }
```

**Error Response (Dec-D):**
```json
{ "error": { "code": "CREDITS_EXHAUSTED", "message": "...", "hint": "...", "docs_url": "..." } }
```

**HTTP Status Codes:**
- `200` success, `201` created, `400` bad input, `401` missing/invalid key
- `403` forbidden (e.g. Free tier gọi Dynamic), `422` validation, `429` quota exceeded, `500` server error

**Data Type Conventions:**
- Dates: ISO 8601 string → `"2026-05-11T07:30:00Z"` (không Unix timestamp integer)
- Credits: integer → `5` (không `5.0`)
- Booleans: `true`/`false` (không `1`/`0`)
- IDs: UUID string → `"550e8400-e29b-41d4-a716-446655440000"`

---

### Communication Patterns

**FastAPI Dependency Injection — bắt buộc dùng `Depends()`:**
```python
# ✅ Đúng — auth và credit check qua Depends
@router.post("/scrape/fetch")
async def fetch_page(
    body: FetchRequest,
    user: User = Depends(get_current_user),
    _: None = Depends(require_credits(cost=1)),
    db: AsyncSession = Depends(get_db),
): ...

# ❌ Sai — manual check trong handler
async def fetch_page(body: FetchRequest, authorization: str = Header(...)):
    user = await verify_key(authorization)  # không làm thế này
```

**Error Handling — exception-based (Python):**
```python
# ✅ Raise custom exception
raise CreditsExhaustedError(tier="free", reset_date="2026-06-01")

# ❌ Không return error dict từ service
return {"error": "credits exhausted"}
```
Custom exceptions defined trong `app/core/errors.py`; global handler format thành Dec-D schema.

**Frontend — TanStack Query error states (không manual loading state):**
```typescript
// ✅ Dùng TanStack Query states
const { data, error, isLoading } = useQuery({ queryKey: ['usage'], queryFn: fetchUsage })

// ❌ Không tự quản lý loading state
const [loading, setLoading] = useState(false)
```

---

### Process Patterns

**Database Transactions — context manager bắt buộc:**
```python
# ✅ Mọi credit deduction trong transaction
async with db.begin():
    balance = await get_balance_for_update(db, user_id)  # SELECT FOR UPDATE
    await deduct_credits(db, user_id, cost)
    await log_usage_event(db, ...)
```

**DynamicFetcher Playwright — isolated context, always cleanup:**
```python
# ✅ Mỗi request = context riêng, cleanup trong finally
async with playwright_pool.get_browser() as browser:
    context = await browser.new_context()
    try:
        page = await context.new_page()
        # ... scrape
    finally:
        await context.close()  # luôn close dù lỗi
```

**Environment Config — pydantic-settings only:**
```python
# ✅ Tất cả config từ Settings class
from app.core.config import settings
db_url = settings.DATABASE_URL

# ❌ Không dùng os.environ rải rác
import os; db_url = os.environ.get("DATABASE_URL")
```

---

### Enforcement Guidelines

**Tất cả AI Agents PHẢI:**
- Dùng `snake_case` cho JSON API fields — không exceptions
- Route handlers không chứa business logic — chỉ gọi service functions
- Credit deduction luôn trong PostgreSQL transaction với `SELECT FOR UPDATE`
- Mọi custom exception định nghĩa và handle tập trung tại `app/core/errors.py`
- Test files đặt đúng vị trí: `backend/tests/` (mirror structure), `frontend` co-located
- Không dùng `os.environ.get()` trực tiếp — luôn qua `settings.*`
- Playwright context phải close trong `finally` block

**Anti-Patterns cần tránh:**
- Wrap success response trong `{"data": ..., "success": true}` envelope
- Check API key thủ công trong route handler thay vì `Depends(get_current_user)`
- Share Playwright browser context giữa nhiều requests
- Lưu URL gốc vào database (chỉ lưu URL hash)
- Return error dicts từ service functions thay vì raise exceptions
- camelCase trong JSON fields (kể cả khi viết TypeScript code phía frontend)

## Project Structure & Boundaries

### Complete Project Directory Structure

```
resili/
├── .github/
│   └── workflows/
│       ├── ci.yml                       # test + lint on PR
│       └── deploy.yml                   # deploy on push to main
├── .devcontainer/
│   └── devcontainer.json
├── docker-compose.yml                   # dev: api, worker, frontend, db, redis
├── .env.example
├── README.md
│
├── backend/
│   ├── Dockerfile                       # FastAPI — gunicorn + uvicorn workers
│   ├── Dockerfile.worker                # browser-capable: playwright install chromium
│   ├── requirements.txt
│   ├── requirements-dev.txt             # pytest, httpx, ruff, mypy
│   ├── alembic.ini
│   ├── pyproject.toml                   # ruff + mypy config
│   ├── mcp_server.py                    # standalone MCP stdio process (FR-08,09,10)
│   │
│   ├── alembic/
│   │   ├── env.py
│   │   └── versions/
│   │       ├── 001_create_users.py
│   │       ├── 002_create_api_keys.py
│   │       ├── 003_create_credit_balances.py
│   │       └── 004_create_usage_events.py
│   │
│   ├── app/
│   │   ├── main.py                      # FastAPI app factory, routers, Sentry init
│   │   │
│   │   ├── api/v1/
│   │   │   ├── router.py                # include all v1 routers
│   │   │   ├── scrape.py                # POST /scrape/fetch (FR-04), /scrape/dynamic (FR-05)
│   │   │   ├── keys.py                  # GET/POST/DELETE /keys (FR-01, FR-02)
│   │   │   ├── usage.py                 # GET /usage (FR-03, FR-16)
│   │   │   └── billing.py               # POST /billing/webhook — Stripe events
│   │   │
│   │   ├── auth/
│   │   │   ├── models.py                # User, ApiKey — SQLAlchemy models
│   │   │   ├── schemas.py               # ApiKeyCreate, ApiKeyResponse, UserResponse
│   │   │   ├── service.py               # create_key(), revoke_key(), verify_key()
│   │   │   └── dependencies.py          # Depends(get_current_user)
│   │   │
│   │   ├── scraping/
│   │   │   ├── schemas.py               # FetchRequest, DynamicFetchRequest, ScrapeResponse
│   │   │   ├── service.py               # orchestrate: ssrf → deduct → scrape → format
│   │   │   ├── fetcher.py               # Scrapling Fetcher wrapper (FR-04)
│   │   │   ├── dynamic.py               # Playwright DynamicFetcher wrapper (FR-05)
│   │   │   └── formatter.py             # HTML→Markdown, HTML→JSON (FR-06)
│   │   │
│   │   ├── billing/
│   │   │   ├── models.py                # CreditBalance, UsageEvent — SQLAlchemy models
│   │   │   ├── schemas.py               # UsageEventResponse, CreditBalanceResponse
│   │   │   ├── service.py               # deduct_credits(), get_balance(), check_tier()
│   │   │   ├── stripe_service.py        # handle Stripe webhook → update tier
│   │   │   └── dependencies.py          # Depends(require_credits(cost=N))
│   │   │
│   │   ├── notifications/
│   │   │   ├── schemas.py
│   │   │   └── service.py               # send_quota_warning_email() via Resend (FR-14)
│   │   │
│   │   ├── core/
│   │   │   ├── config.py                # pydantic-settings Settings class
│   │   │   ├── security.py              # generate_api_key(), hash_key() SHA-256
│   │   │   ├── ssrf_guard.py            # validate_url() — block private IPs (NFR-08)
│   │   │   └── errors.py                # custom exceptions + exception handlers
│   │   │
│   │   └── db/
│   │       ├── base.py                  # DeclarativeBase
│   │       └── session.py               # async_session_factory, get_db() Depends
│   │
│   └── tests/
│       ├── conftest.py                  # fixtures: test db, async client, mock user
│       ├── api/
│       │   ├── test_scrape.py           # FR-04, FR-05, FR-06, FR-07
│       │   ├── test_keys.py             # FR-01, FR-02
│       │   └── test_usage.py            # FR-03, FR-16
│       ├── scraping/
│       │   ├── test_fetcher.py
│       │   ├── test_dynamic.py
│       │   └── test_ssrf_guard.py       # NFR-08: private IP, localhost block
│       └── billing/
│           ├── test_credit_deduction.py # FR-11,12,13 — concurrent deduction tests
│           └── test_stripe_webhook.py
│
└── frontend/
    ├── Dockerfile
    ├── next.config.ts
    ├── tailwind.config.ts
    ├── tsconfig.json
    ├── package.json
    ├── .env.local.example
    │
    └── src/
        ├── app/
        │   ├── layout.tsx               # root layout, QueryClientProvider, Sentry
        │   ├── page.tsx                 # landing → redirect to dashboard
        │   ├── (auth)/
        │   │   ├── login/page.tsx
        │   │   └── register/page.tsx
        │   └── dashboard/
        │       ├── layout.tsx           # dashboard shell: sidebar + header
        │       ├── page.tsx             # overview + Quick Start guide (SC-04)
        │       ├── keys/page.tsx        # API key management (FR-01)
        │       └── usage/page.tsx       # usage charts breakdown (FR-03, FR-16)
        │
        ├── components/
        │   ├── ui/                      # generic: Button, Card, Badge, Input, Dialog
        │   └── dashboard/
        │       ├── usage-chart.tsx      # Recharts — Fetcher vs Dynamic (FR-16)
        │       ├── usage-chart.test.tsx
        │       ├── api-key-list.tsx     # list + revoke + regenerate (FR-01)
        │       ├── api-key-list.test.tsx
        │       ├── credit-badge.tsx     # balance + tier display (FR-03)
        │       └── quota-alert.tsx      # 80% usage warning banner (FR-14)
        │
        ├── lib/
        │   ├── api/
        │   │   ├── client.ts            # fetch wrapper: Authorization header, error parse
        │   │   ├── types.ts             # openapi-typescript generated from FastAPI spec
        │   │   └── endpoints.ts         # typed wrappers: getUsage(), getKeys(), revokeKey()
        │   └── utils.ts
        │
        └── hooks/
            ├── use-api-keys.ts          # TanStack Query: GET /api/v1/keys
            ├── use-usage.ts             # TanStack Query: GET /api/v1/usage
            └── use-credits.ts           # TanStack Query: balance + tier info
```

### Architectural Boundaries

**External API Boundaries:**
- REST API: `https://api.resili.io/api/v1/*` — AI Developers, RAG Engineers, Dashboard frontend
- MCP stdio: `mcp_server.py` process — AI Agent clients (Claude Desktop, Cursor, OpenAI)
- Stripe Webhook: `POST /api/v1/billing/webhook` — Stripe billing events inbound
- Resend: fire-and-forget email, no inbound webhook needed

**Internal Service Boundaries:**
- `api/v1/scrape.py` → gọi `scraping/service.py` (không trực tiếp gọi fetcher/dynamic)
- `scraping/service.py` → gọi `billing/dependencies.py` (credit check), rồi `fetcher.py` hoặc `dynamic.py`
- `billing/service.py` → sau deduction, gọi `notifications/service.py` nếu balance ≤ 20%
- `mcp_server.py` → import trực tiếp `app.scraping.fetcher` và `app.scraping.dynamic` (không qua HTTP)

**Data Boundaries:**
- PostgreSQL: source of truth — users, api_keys, credit_balances, usage_events
- Redis: read cache cho api_key lookup (TTL 5min) + credit balance (TTL 60s, invalidate on write)
- Scrapling/Playwright: stateless — không write database, trả data cho service layer
- Stripe: external billing source of truth — sync qua webhook events

### Requirements → Structure Mapping

| FR Group | Backend | Frontend |
|----------|---------|----------|
| Auth & Access (FR-01–03) | `app/auth/`, `api/v1/keys.py`, `api/v1/usage.py` | `dashboard/keys/`, `hooks/use-api-keys.ts` |
| Scraping API (FR-04–07) | `app/scraping/`, `api/v1/scrape.py` | (API-only, no dashboard UI) |
| MCP Integration (FR-08–10) | `mcp_server.py` | (config guide in docs only) |
| Rate Limiting (FR-11–13) | `app/billing/dependencies.py` | `components/dashboard/credit-badge.tsx` |
| Quota & Upgrade (FR-14–15) | `app/notifications/`, `app/billing/stripe_service.py` | `components/dashboard/quota-alert.tsx` |
| Dashboard (FR-16) | `api/v1/usage.py` | `dashboard/usage/`, `usage-chart.tsx` |

### Integration Points & Data Flow

**Scrape Request Flow (happy path):**
```
Client → HTTPS → FastAPI
  → ssrf_guard.validate_url()         [core/ssrf_guard.py]
  → get_current_user()                [auth/dependencies.py → Redis/DB]
  → require_credits(cost=N)           [billing/dependencies.py → DB SELECT FOR UPDATE]
  → scraping/service.py
      → fetcher.py OR dynamic.py      [Scrapling / Playwright]
      → formatter.py                  [→ Markdown or JSON]
  → log usage_event()                 [billing/service.py]
  → return ScrapeResponse             [job_id: null, status: completed, result: {...}]
```

**Quota Warning Flow:**
```
billing/service.py.deduct_credits()
  → balance ≤ 20% monthly limit?
      → notifications/service.py.send_quota_warning_email()
          → Resend API → user email (FR-14)
```

**Dashboard Data Flow:**
```
hooks/use-usage.ts → TanStack Query
  → GET /api/v1/usage
  → billing/service.py.get_usage_summary()
  → PostgreSQL aggregation on usage_events
  → UsageResponse → Recharts → usage-chart.tsx
```

**MCP Flow:**
```
AI Agent (Claude/Cursor/OpenAI)
  → MCP stdio → mcp_server.py
  → direct import: app.scraping.fetcher / app.scraping.dynamic
  → same scraping logic as REST API
  → MCP tool response (same ScrapeResponse schema)
```

### Development Workflow Commands

```bash
# Start all services (dev)
docker compose up

# Generate frontend types after backend route changes
cd frontend && npx openapi-typescript http://localhost:8000/openapi.json \
  -o src/lib/api/types.ts

# Create and run DB migration
cd backend
alembic revision --autogenerate -m "description"
alembic upgrade head

# Run backend tests
cd backend && pytest tests/ -v

# Run frontend tests
cd frontend && npm test
```

## Architecture Validation Results

### Coherence Validation ✅

**Decision Compatibility:**
- FastAPI + SQLAlchemy 2.0 async + PostgreSQL 16 + psycopg: fully compatible, production-proven stack
- Redis async (redis-py) + FastAPI async: ✅ non-blocking
- Playwright Python + Docker browser image: ✅ official support
- Next.js 16 + TanStack Query v5 + Recharts + Tailwind: ✅ all React ecosystem, no conflicts
- openapi-typescript ↔ FastAPI OpenAPI spec: ✅ auto-generated, always in sync
- Sentry: native SDK cho cả Python (FastAPI) và Next.js ✅

**Pattern Consistency:**
- Pydantic models dùng `snake_case` by default → khớp hoàn toàn với JSON naming pattern ✅
- `Depends()` pattern nhất quán với FastAPI paradigm ✅
- Exception → global handler → Dec-D error schema: coherent flow ✅
- `SELECT FOR UPDATE` supported trong SQLAlchemy 2.0 async via `with_for_update()` ✅

**Structure Alignment:**
- Domain-driven backend khớp với complexity level Medium-High ✅
- MCP as separate process: failure isolation, phù hợp Dec-E ✅
- Co-located frontend tests: khớp Next.js convention ✅

### Requirements Coverage Validation ✅

**Functional Requirements: 16/16 covered**

| FR | Covered By |
|----|-----------|
| FR-01 | `app/auth/service.py` + `api/v1/keys.py` |
| FR-02 | `auth/dependencies.py` → Depends(get_current_user) |
| FR-03 | `api/v1/usage.py` + `billing/service.py` |
| FR-04 | `scraping/fetcher.py` + `api/v1/scrape.py` |
| FR-05 | `scraping/dynamic.py` + `api/v1/scrape.py` |
| FR-06 | `scraping/formatter.py` (markdown/json param) |
| FR-07 | `core/errors.py` + Dec-D error schema |
| FR-08 | `mcp_server.py` standalone process |
| FR-09 | `mcp_server.py` tools: fetch_page, fetch_dynamic_page |
| FR-10 | `mcp_server.py` error với MCP spec version |
| FR-11 | `billing/dependencies.py` tier check (Free = no Dynamic) |
| FR-12 | `billing/service.py` cost=5 cho DynamicFetcher |
| FR-13 | `core/errors.py` HTTP 429 + Retry-After header |
| FR-14 | `billing/service.py` → `notifications/service.py` at 80% |
| FR-15 | `api/v1/billing.py` + Stripe + dashboard upgrade button |
| FR-16 | `api/v1/usage.py` + `dashboard/usage/page.tsx` + Recharts |

**Non-Functional Requirements: 12/12 covered**

| NFR | Coverage |
|-----|---------|
| NFR-01 (99.5% uptime) | BetterUptime external monitoring + Railway/Render SLA |
| NFR-02 (Fetcher ≤ 3s) | Scrapling HTTP-based, no JS overhead; measured via Sentry APM |
| NFR-03 (Dynamic ≤ 15s) | 30s timeout (NFR-04) gives headroom; measured via Sentry APM |
| NFR-04 (Isolation) | `Dockerfile.worker` isolated process + `asyncio.timeout(30)` + memory limits |
| NFR-05 (10x scaling) | Docker containers + Railway/Render horizontal auto-scale |
| NFR-06 (TLS) | Terminated at Railway/Render ingress |
| NFR-07 (Key hashed) | `core/security.py` SHA-256; plaintext shown once |
| NFR-08 (SSRF) | `core/ssrf_guard.py` validates trước mọi scrape call |
| NFR-09 (Data retention) | Append-only usage_events + APScheduler prune job (90 days) |
| NFR-10 (robots.txt) | `respect_robots_txt: bool = False` field trong FetchRequest schema |
| NFR-11 (BSD attribution) | `X-Powered-By` response header + README attribution |
| NFR-12 (Async migration) | Dec-F `job_id: null` response shape bảo vệ Growth phase |

### Gap Analysis Results

**Critical Gaps:** Không có.

**Minor Gaps (không block implementation):**
1. **APScheduler cho retention prune (NFR-09):** Thêm `apscheduler` vào `requirements.txt`; register job trong `app/main.py` startup event để prune `usage_events` sau 90 ngày
2. **`slowapi` dependency:** Thêm vào `requirements.txt` cho rate limiting middleware
3. **BSD attribution header (NFR-11):** Thêm 1 dòng middleware trong `app/main.py`: `response.headers["X-Powered-By"] = "Resili (built on Scrapling — BSD License)"`

**Nice-to-Have:**
- `GET /health` endpoint (cần cho Railway/Render health probe)
- `GET /api/v1/` root endpoint trả về API version + links

### Architecture Completeness Checklist

**Requirements Analysis**
- [x] Project context thoroughly analyzed
- [x] Scale and complexity assessed (Medium-High)
- [x] Technical constraints identified (Scrapling, Playwright, Stripe, MCP)
- [x] Cross-cutting concerns mapped (6 concerns)

**Architectural Decisions**
- [x] Critical decisions documented với rationale (Dec-A đến Dec-O)
- [x] Technology stack fully specified (Python 3.13, FastAPI, Next.js 16, PostgreSQL 16)
- [x] Integration patterns defined (REST + MCP + Stripe webhook)
- [x] Performance considerations addressed (latency budgets, Redis cache)

**Implementation Patterns**
- [x] Naming conventions established (DB, API, JSON, Python, TypeScript)
- [x] Structure patterns defined (domain-driven backend, co-located frontend tests)
- [x] Communication patterns specified (Depends(), exception-based errors)
- [x] Process patterns documented (transactions, Playwright isolation, config)

**Project Structure**
- [x] Complete directory structure defined (backend + frontend + CI)
- [x] Component boundaries established (6 backend domains)
- [x] Integration points mapped (scrape, quota, MCP, dashboard flows)
- [x] Requirements → structure mapping complete (FR-01 đến FR-16)

### Architecture Readiness Assessment

**Overall Status: READY FOR IMPLEMENTATION**

**Confidence Level: High** — 16/16 FRs và 12/12 NFRs covered; không có critical gaps; technology stack coherent; patterns comprehensive.

**Key Strengths:**
1. Async-ready DynamicFetcher response shape (Dec-F) bảo vệ Growth phase migration không breaking change
2. Separation of concerns rõ ràng: routers → service → fetcher (không có business logic trong route handlers)
3. MCP server as separate process: failure isolation + dễ scale độc lập
4. Credit accounting với `SELECT FOR UPDATE`: atomic, race-condition safe ngay từ MVP
5. openapi-typescript: type safety frontend↔backend không cần maintain thủ công

**Areas for Future Enhancement (post-MVP):**
- Celery task queue khi DynamicFetcher chuyển async (Growth phase)
- Team accounts: multi-key, usage reports, invoice PDF (Growth phase)
- SDK chính thức Python + TypeScript (Vision phase)
- Spider async: multi-page crawl với checkpoint (Vision phase)

### Implementation Handoff

**AI Agent Guidelines:**
- Follow all architectural decisions exactly as documented (Dec-A đến Dec-O)
- Use implementation patterns consistently — especially Depends(), snake_case JSON, exception-based errors
- Respect project structure: routers không chứa business logic; tests mirror app/ structure
- Refer to this document for all architectural questions before making assumptions

**First Implementation Priority:**
```bash
# Story 1: Monorepo scaffold + Docker Compose
mkdir resili && cd resili && git init
npx create-next-app@latest frontend \
  --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"
mkdir backend && cd backend && python -m venv .venv
# Sau đó: tạo docker-compose.yml với services: api, worker, frontend, db, redis
```
