---
stepsCompleted: [1, 2, 3, 4]
status: 'complete'
completedAt: '2026-05-11'
inputDocuments:
  - 'docs/report.md'
  - '_bmad-output/planning-artifacts/architecture.md'
  - 'docs/DESIGN.md'
---

# resili - Epic Breakdown

## Overview

This document provides the complete epic and story breakdown for resili, decomposing the requirements from the PRD, and Architecture requirements into implementable stories.

## Requirements Inventory

### Functional Requirements

FR-01: Users tạo được API key từ dashboard, với tùy chọn revoke và regenerate bất kỳ lúc nào.

FR-02: Mỗi API request được xác thực qua API key trong `Authorization` header; request không có key hợp lệ nhận HTTP 401 với message giải thích rõ.

FR-03: Users xem được credit usage breakdown theo Fetcher/Dynamic trong dashboard, cập nhật theo thời gian thực.

FR-04: Users gọi Fetcher endpoint với URL để nhận nội dung trang tĩnh dạng Markdown hoặc JSON, không cần JS rendering.

FR-05: Users gọi DynamicFetcher endpoint với URL để nhận nội dung trang JS-heavy sau khi render hoàn toàn, dạng Markdown hoặc JSON.

FR-06: Users chỉ định output format (`markdown` hoặc `json`) qua request parameter; default là `markdown`.

FR-07: Khi scrape thất bại, API trả về error JSON với field `message` human-readable mô tả nguyên nhân cụ thể và action được gợi ý, kèm link troubleshooting doc.

FR-08: AI Agents kết nối được Resili qua MCP stdio transport bằng cách thêm 1 JSON config entry, không cần viết code wrapper.

FR-09: MCP server expose tối thiểu 2 tools: `fetch_page` (Fetcher) và `fetch_dynamic_page` (DynamicFetcher), với description đủ rõ để LLM chọn đúng tool theo context.

FR-10: Resili document MCP spec version được support; incompatibility trả về error message có ghi rõ spec version đang dùng và version Resili support.

FR-11: Free tier giới hạn 1,000 Fetcher credits/tháng; DynamicFetcher không khả dụng ở Free tier.

FR-12: Pro tier áp dụng credit multiplier: 1 DynamicFetcher call tiêu thụ 5 Fetcher credits.

FR-13: Request vượt quota nhận HTTP 429 với header `Retry-After` và body ghi rõ credit loại nào đã hết và khi nào reset.

FR-14: Users nhận email cảnh báo khi đạt 80% quota tháng, với link trực tiếp đến usage dashboard.

FR-15: Users nâng cấp tier từ dashboard với 1 click, không cần contact sales.

FR-16: Users xem được credit usage theo ngày/tuần/tháng, phân tách Fetcher credits và Dynamic credits.

### NonFunctional Requirements

NFR-01 — Availability: API đạt 99.5% uptime đo bằng external uptime monitoring; planned maintenance announced ≥ 24h trước qua email và status page.

NFR-02 — Fetcher Latency: Fetcher API response time ≤ 3s ở 95th percentile dưới tải bình thường (≤ 100 concurrent requests), đo bằng APM monitoring.

NFR-03 — DynamicFetcher Latency: DynamicFetcher API response time ≤ 15s ở 95th percentile dưới tải bình thường (≤ 20 concurrent Playwright sessions), đo bằng APM monitoring.

NFR-04 — DynamicFetcher Isolation: Mỗi DynamicFetcher request chạy trong isolated process với timeout 30s và memory cap; một request lỗi không affect request khác.

NFR-05 — Scalability: System scale horizontal để xử lý 10x load spike mà không có downtime, thông qua container orchestration.

NFR-06 — Transport Security: Toàn bộ API traffic qua HTTPS/TLS 1.2+; HTTP requests bị redirect tự động sang HTTPS.

NFR-07 — API Key Security: API keys được store dưới dạng hashed; plaintext key chỉ hiển thị một lần duy nhất tại thời điểm tạo.

NFR-08 — Input Validation: System validate và sanitize tất cả URL inputs tại API gateway; SSRF attack vectors bị block trước khi đến scraping layer.

NFR-09 — Data Retention: Resili không lưu nội dung trang đã scrape; chỉ lưu metadata request (timestamp, URL hash, credit usage) trong 90 ngày.

NFR-10 — Robots.txt Compliance: Resili expose tùy chọn `respect_robots_txt` per request; default off; behavior documented rõ trong ToS.

NFR-11 — License Compliance: BSD license của Scrapling upstream được giữ nguyên trong fork; attribution hiển thị trong About page và response headers.

NFR-12 — DynamicFetcher Async Architecture: MVP synchronous với timeout 30s; thiết kế MVP không được block migration lên async job queue (Growth phase).

### Additional Requirements

- **[Arch-01] Monorepo Scaffold (Epic 1, Story 1):** Custom monorepo — `create-next-app` (TypeScript, Tailwind, App Router) + FastAPI backend + Docker Compose với services: api, worker, frontend, db (PostgreSQL 16), redis.
- **[Arch-02] DB Schema:** 4 tables via Alembic migrations — `users`, `api_keys`, `credit_balances`, `usage_events`. Naming convention: snake_case plural.
- **[Arch-03] API Key Format (Dec-A):** `rsl_` prefix + 32 random bytes (URL-safe base64); stored as SHA-256 hash; plaintext returned once only.
- **[Arch-04] SSRF Guard (Dec-B):** `app/core/ssrf_guard.py` blocks RFC 1918 private IPs, localhost, link-local ranges; inject vào cả Fetcher và DynamicFetcher.
- **[Arch-05] API Versioning (Dec-C):** `/api/v1/` prefix từ ngày đầu.
- **[Arch-06] Error Response Schema (Dec-D):** Standardized JSON: `{ "error": { "code", "message", "hint", "docs_url" } }`; codes SCREAMING_SNAKE_CASE.
- **[Arch-07] MCP Separate Process (Dec-E):** `backend/mcp_server.py` standalone script; direct import of `app.scraping.*`; không qua HTTP.
- **[Arch-08] DynamicFetcher Async-Ready Shape (Dec-F):** Response includes `job_id: null` và `status: "completed"` để tương thích Growth phase async migration.
- **[Arch-09] Credit Accounting Atomicity (Dec-G):** PostgreSQL `SELECT FOR UPDATE` trong transaction; Redis cache balance (TTL 60s), invalidate on deduction.
- **[Arch-10] Usage Events Schema (Dec-H):** Append-only; store URL hash only (not raw URL); APScheduler prune job mỗi 90 ngày.
- **[Arch-11] Frontend State (Dec-I):** TanStack Query v5 cho tất cả server state trong dashboard.
- **[Arch-12] Dashboard Charts (Dec-J):** Recharts library (line/bar) cho usage visualization.
- **[Arch-13] API Client Generation (Dec-K):** `openapi-typescript` auto-generates typed client từ FastAPI OpenAPI spec.
- **[Arch-14] Email Provider (Dec-L):** Resend SDK cho quota warning emails.
- **[Arch-15] Error Monitoring (Dec-M):** Sentry (free tier) cho cả Python backend và Next.js frontend.
- **[Arch-16] Uptime Monitoring (Dec-N):** BetterUptime hoặc UptimeRobot external monitoring.
- **[Arch-17] CI/CD Pipeline (Dec-O):** GitHub Actions — test → lint → build → deploy.
- **[Arch-18] Health & Root Endpoints:** `GET /health` (Railway/Render probe) và `GET /api/v1/` (version + links).

### UX Design Requirements

*(Nguồn: `docs/DESIGN.md` — Design system cho toàn bộ public-facing frontend)*

**UX-DR1 — Design Token System:** Implement CSS design token system đầy đủ — color tokens (`{colors.canvas}`, `{colors.surface-card}`, `{colors.surface-elevated}`, `{colors.surface-deep}`, `{colors.hairline}`, `{colors.hairline-strong}`, `{colors.divider-soft}`, ink/body/charcoal/mute/ash/stone), spacing tokens (xxs=2px đến band=128px), border-radius scale (none/xs/sm/md/lg/xl/full), và elevation levels.

**UX-DR2 — Font Stack:** Load và configure 4-family font stack: Domaine Display (hero headlines, fallback: Söhne / Tiempos Headline), ABC Favorit (marketing body, fallback: Geist / Inter Tight), Inter (UI labels), Geist Mono (code). OpenType features: ABC Favorit dùng `ss01/ss03/ss04`; Domaine Display dùng `ss01/ss04/ss11`; Inter không dùng OpenType features; Geist Mono không dùng ligatures.

**UX-DR3 — Color Tokens Implementation:** Implement đầy đủ 5 accent colors với paired glow tokens: accent-orange (`#ff801f` + glow `rgba(255,89,0,0.22)`), accent-yellow (`#ffc53d`), accent-blue (`#3b9eff` + glow `rgba(0,117,255,0.34)`), accent-green (`#11ff99` + glow `rgba(34,255,153,0.18)`), accent-red (`#ff2047` + glow `rgba(255,32,71,0.34)`). Glow tokens chỉ dùng làm CSS radial gradient atmospheric wash — không bao giờ dùng làm solid surface.

**UX-DR4 — Typography Scale:** Implement 14-token typography hierarchy từ `display-xxl` (96px, weight 400, lineHeight 1.0, tracking -0.96px) đến `caption` (12px). Display sizes phải chạy lineHeight 1.0 với negative letter-spacing. Body weight cố định 400. Code dùng `typography.code-md` (13px, lineHeight 1.6).

**UX-DR5 — Button Components:** Implement 3 button variants: `button-primary` (bg primary #fcfdff, text black, h=36px, rounded-md 8px — phải là bright pixel duy nhất trên canvas), `button-ghost` (bg surface-elevated, text ink, 1px hairline-strong), `button-outline` (bg canvas, text ink, 1px hairline-strong). Pressed state cho primary: bg surface-light (`#f1f7fe`). Mobile: scale lên 44px height.

**UX-DR6 — Card & Container Components:** Implement 5 container variants: `feature-card` (bg surface-card, rounded-lg, padding 32px), `feature-card-bordered` (+ 1px hairline-strong), `pricing-tier` (bg surface-card, 1px hairline-strong, price text ở display-lg 56px ABC Favorit), `pricing-tier-featured` (bg surface-elevated — elevation qua luminance, không qua màu), `hero-stripe` (full-bleed, rounded-none, padding 96px 32px, type display-xxl).

**UX-DR7 — Code Window Component:** Implement `code-window`: bg surface-deep (`#06060a`), 1px hairline-strong, rounded-lg, padding 24px, type code-md (Geist Mono). Bao gồm: hàng 3 traffic-light dots (red/yellow/green solid), tab strip (`code-tab`: bg surface-card, rounded-sm, active tab: ink text + hairline-strong underline).

**UX-DR8 — Navigation Components:** Implement `nav-bar` desktop (height 64px, bg canvas, hairline bottom, logo left — center links — sign-in + button-primary right) và mobile (collapse center nav thành hamburger tại < 1024px, logo và CTA vẫn hiện). Implement `sub-nav-pill` (pill chips horizontal row, height 36px desktop / 40px mobile).

**UX-DR9 — Atmospheric Glow System:** Implement section atmospheric glows bằng CSS radial gradient, anchored top of section, fade-off ~600px vertical. Không bao giờ dùng 2 glow màu khác nhau trong cùng section. Glow chỉ ở low-opacity, không solid surface.

**UX-DR10 — Signature & Utility Components:** Implement `badge-pill` (bg surface-elevated, rounded-full, padding 4px 10px, type caption), `status-dot` (bg accent-green, rounded-full, 8px square), `contributor-avatar` (bg surface-card placeholder, rounded-full, 32×32px), `email-mockup` (bg surface-card, rounded-lg), `footer` (bg canvas, multi-column, type body-sm, padding 64px 32px, divider-soft separator).

**UX-DR11 — Text Input Component:** Implement `text-input`: bg surface-card, 1px hairline-strong, rounded-md (8px), padding 10px 14px, height 40px (mobile 48px). Focus state: border thickens to ink — không dùng separate focus ring color.

**UX-DR12 — Responsive Layout System:** Implement 6-breakpoint responsive layout: mobile ≤425px (grid 1-up, hero clamp 44px, section padding 64px), mobile-large 426–767px (1-up, nav hamburger, hero clamp 56px), tablet 768–1023px (feature grid 2-up, code-story stacks, pricing stacks), tablet-large 1024–1279px (grid 3-up, code-story 2-up), desktop 1280–1439px, desktop-xl ≥1440px (max-width 1200px body). Hero display-xxl clamp: 96px→76px→56px→44px.

**UX-DR13 — No Drop Shadow Policy:** Toàn bộ frontend không được dùng drop-shadow/box-shadow. Elevation chỉ qua: surface color shift (surface-card → surface-elevated → surface-deep) + hairline white border (6%/14% opacity). Đây là thiết kế constraint bắt buộc.

### FR Coverage Map

| FR | Epic | Mô tả |
|----|------|--------|
| FR-01 | Epic 2 | API key CRUD từ dashboard |
| FR-02 | Epic 2 | Xác thực qua Authorization header |
| FR-03 | Epic 5 | Credit usage real-time trong dashboard |
| FR-04 | Epic 3 | Fetcher endpoint — trang tĩnh |
| FR-05 | Epic 3 | DynamicFetcher endpoint — JS-heavy |
| FR-06 | Epic 3 | Output format markdown/json configurable |
| FR-07 | Epic 3 | Error JSON human-readable + hint + docs_url |
| FR-08 | Epic 4 | MCP stdio connect với 1 JSON config |
| FR-09 | Epic 4 | MCP tools: fetch_page + fetch_dynamic_page |
| FR-10 | Epic 4 | MCP spec version documented + error |
| FR-11 | Epic 3 | Free tier limit 1,000 Fetcher credits |
| FR-12 | Epic 3 | Credit multiplier 1 Dynamic = 5 Fetcher |
| FR-13 | Epic 3 | HTTP 429 + Retry-After header |
| FR-14 | Epic 5 | Email alert tại 80% quota |
| FR-15 | Epic 5 | 1-click tier upgrade |
| FR-16 | Epic 5 | Usage visualization ngày/tuần/tháng |

## Epic List

### Epic 1: Foundation & Project Setup
Project chạy được ở development với đầy đủ monorepo structure, Docker Compose, database schema, CI/CD pipeline, observability stack, và public landing page. Đây là nền tảng architectural cho toàn bộ project.
**FRs covered:** *(Architectural foundation — không có FR trực tiếp)*
**Arch covered:** Arch-01, Arch-02, Arch-05, Arch-06, Arch-15, Arch-16, Arch-17, Arch-18
**NFRs covered:** NFR-05 (container scaling), NFR-06 (TLS termination)
**UX-DRs covered:** UX-DR1 (design tokens), UX-DR4–UX-DR9 (components for landing page)

### Epic 2: Authentication & API Key Management
Developers có thể đăng ký tài khoản, tạo/revoke/regenerate API keys, và xác thực mọi request qua Authorization header.
**FRs covered:** FR-01, FR-02
**Arch covered:** Arch-03 (API key format rsl_ + SHA-256), Arch-04 (SSRF guard wiring)
**NFRs covered:** NFR-07 (key hashing), NFR-08 (SSRF protection)

### Epic 3: Core Scraping API & Credit Enforcement
Developers có thể gọi Fetcher và DynamicFetcher endpoints để nhận Markdown/JSON sạch. Credits được deduct atomic và enforced — Free tier limit, multiplier, HTTP 429.
**FRs covered:** FR-04, FR-05, FR-06, FR-07, FR-11, FR-12, FR-13
**Arch covered:** Arch-07, Arch-08 (DynamicFetcher async-ready), Arch-09 (SELECT FOR UPDATE), Arch-10 (usage events)
**NFRs covered:** NFR-02, NFR-03, NFR-04, NFR-08, NFR-09, NFR-10, NFR-11, NFR-12

### Epic 4: MCP Server Integration
AI Agents (Claude Desktop, Cursor, OpenAI) có thể kết nối Resili qua MCP stdio với 1 dòng JSON config và gọi scraping tools trực tiếp, không cần code wrapper.
**FRs covered:** FR-08, FR-09, FR-10
**Arch covered:** Arch-07 (MCP separate process — standalone mcp_server.py)

### Epic 5: Dashboard, Billing & Notifications
Users có full dashboard experience — usage visualization (ngày/tuần/tháng), email cảnh báo 80% quota, 1-click upgrade qua Stripe. Toàn bộ frontend implement theo docs/DESIGN.md design system.
**FRs covered:** FR-03, FR-14, FR-15, FR-16
**Arch covered:** Arch-11 (TanStack Query), Arch-12 (Recharts), Arch-13 (openapi-typescript), Arch-14 (Resend), Arch-16 (Stripe)
**UX-DRs covered:** UX-DR2, UX-DR5–UX-DR8, UX-DR10–UX-DR13 (landing page UX-DRs moved to Epic 1)
**NFRs covered:** NFR-01 (uptime tracking)

---

## Epic 1: Foundation & Project Setup

Project chạy được ở development với đầy đủ monorepo structure, Docker Compose, database infrastructure, CI/CD pipeline, và observability stack.

### Story 1.1: Monorepo Scaffold & Docker Compose

As a developer,
I want a working monorepo structure with all services running via Docker Compose,
So that I can start development immediately without manual environment setup.

**Acceptance Criteria:**

**Given** the repo is cloned and `.env` is populated from `.env.example`,
**When** `docker compose up` is run,
**Then** all 5 services start without errors: `api` (FastAPI on :8000), `worker` (Playwright worker), `frontend` (Next.js on :3000), `db` (PostgreSQL 16 on :5432), `redis` (Redis on :6379).

**Given** the running environment,
**When** GET http://localhost:3000 is visited,
**Then** the Next.js default page loads without error.

**Given** the project root after scaffold,
**When** directory structure is inspected,
**Then** the following exist: `backend/`, `frontend/`, `docker-compose.yml`, `.env.example`, `README.md`, `.devcontainer/devcontainer.json`, `.github/workflows/`.

**Given** the frontend directory,
**When** package.json is reviewed,
**Then** it was created with `create-next-app` using: TypeScript, Tailwind CSS, App Router, `src/` dir, `@/*` import alias.

**Given** the `.env.example` file,
**When** reviewed,
**Then** it contains all required environment variables: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `SENTRY_DSN` (optional), `RESEND_API_KEY` (optional), `STRIPE_SECRET_KEY` (optional).

**Given** `backend/Dockerfile` and `backend/Dockerfile.worker`,
**When** built,
**Then** `Dockerfile` produces a FastAPI + uvicorn image; `Dockerfile.worker` includes `playwright install chromium`.

---

### Story 1.2: Core Error Schema, Config, and Health Endpoints

As a developer,
I want a standardized error schema and health check endpoints in place from day one,
So that all API consumers have a consistent error format and deployment platforms can verify liveness.

**Acceptance Criteria:**

**Given** any API error at any endpoint,
**When** the error response is returned,
**Then** it follows Dec-D schema exactly: `{"error": {"code": "SCREAMING_SNAKE_CASE", "message": "...", "hint": "...", "docs_url": "https://docs.resili.io/errors/..."}}`.

**Given** `app/core/config.py`,
**When** reviewed,
**Then** all configuration is read via a `pydantic-settings` `Settings` class; no `os.environ.get()` calls exist outside this file.

**Given** `app/core/errors.py`,
**When** reviewed,
**Then** it contains: a custom exception base class, at minimum `NotFoundError`, `UnauthorizedError`, `ForbiddenError`, `SSRFBlockedError`, `CreditsExhaustedError`; global FastAPI exception handlers that format all custom exceptions using the Dec-D schema.

**Given** GET /health,
**When** called,
**Then** HTTP 200 is returned with `{"status": "ok"}`.

**Given** GET /api/v1/,
**When** called,
**Then** HTTP 200 is returned with `{"version": "v1", "docs": "/docs"}`.

**Given** the Alembic configuration (`alembic.ini`, `alembic/env.py`),
**When** `alembic upgrade head` is run with no migrations yet,
**Then** it succeeds without error (infrastructure ready for future migrations).

---

### Story 1.3: CI/CD Pipeline & Observability Integration

As a development team,
I want automated testing, linting, and deployment pipelines with error monitoring,
So that code quality is enforced automatically and production errors are visible.

**Acceptance Criteria:**

**Given** a PR opened against `main`,
**When** the CI pipeline (`.github/workflows/ci.yml`) runs,
**Then** it executes in sequence: `pytest tests/` (backend), `ruff check .` (backend lint), `mypy .` (backend types), `npm test` (frontend Jest).

**Given** a push to `main`,
**When** the deploy pipeline (`.github/workflows/deploy.yml`) runs,
**Then** it deploys the backend to Railway/Render and (optionally) the frontend to Vercel.

**Given** `SENTRY_DSN` is set in environment,
**When** FastAPI starts,
**Then** `sentry_sdk.init()` is called in `app/main.py` and unhandled exceptions are captured.

**Given** `NEXT_PUBLIC_SENTRY_DSN` is set,
**When** the Next.js app starts,
**Then** Sentry is initialized in `src/app/layout.tsx`.

**Given** any FastAPI HTTP response,
**When** inspected,
**Then** the response includes `X-Powered-By: Resili (built on Scrapling — BSD License)` header (NFR-11).

**Given** `pyproject.toml`,
**When** reviewed,
**Then** `ruff` and `mypy` are configured with appropriate rules for the `backend/` codebase.

---

### Story 1.4: Public Landing Page & Design System Showcase

As a prospective Resili user,
I want a compelling public landing page that showcases Resili's value proposition,
So that I understand what Resili does and can start using it immediately.

**Acceptance Criteria:**

**Given** a logged-out user visiting `/`,
**When** the page loads,
**Then** the public landing page renders (no redirect) with: `hero-stripe` section (Domaine Display or configured fallback, `display-xxl` headline, `button-primary` "Get started", `button-ghost` "View docs" — UX-DR6), and at least two feature sections below.

**Given** the `hero-stripe` section,
**When** rendered,
**Then** the headline communicates Resili's scraping value proposition (e.g. "Web data for AI agents" or equivalent) — NOT email-related copy; all placeholder text referencing "Email for developers", "Email reimagined", or email-product messaging is replaced with scraping/AI-data messaging.

**Given** the DESIGN.md component system,
**When** applied to the landing page,
**Then** the `email-mockup` component is NOT used as a product feature showcase — it is either omitted or replaced with a `code-window` demonstrating actual scraping API output (Markdown from a real URL). The design system's visual language (colors, typography, elevation) is followed; only email-specific content references are adapted for Resili's scraping product.

**Given** the hero headline,
**When** rendered,
**Then** it uses `display-xxl` (96px) with `lineHeight: 1.0` and negative letter-spacing; clamps to 44px on mobile ≤ 425px (UX-DR4, UX-DR12).

**Given** at least one section below the hero,
**When** rendered,
**Then** an atmospheric glow (CSS radial gradient using one `accent-*-glow` token) is anchored at the top of the section and fades to canvas black within ~600px; no two adjacent sections share the same glow color (UX-DR9).

**Given** the pricing section,
**When** rendered,
**Then** 3 tier cards use `pricing-tier` component (bg `surface-card`, `rounded-lg`, `hairline-strong` border); the recommended Pro tier uses `pricing-tier-featured` (bg `surface-elevated`) — elevation from luminance only, no drop shadow (UX-DR6, UX-DR13).

**Given** at least one `code-window` component on the page,
**When** rendered,
**Then** it uses bg `surface-deep`, Geist Mono, traffic-light dots (solid red/yellow/green), code tabs, and displays a real working `curl` or Python example for the Fetcher API (UX-DR7).

**Given** the landing page on mobile (≤ 425px viewport),
**When** rendered,
**Then** feature grid is 1-up, hero font clamps to 44px, nav collapses to hamburger, section padding reduces to 64px (UX-DR12).

---

## Epic 2: Authentication & API Key Management

Developers có thể đăng ký tài khoản, tạo/revoke/regenerate API keys, và xác thực mọi scraping request qua Authorization header.

### Story 2.1: User Registration & Account Creation

As a developer building with Resili,
I want to register a new account with email and password,
So that I can access the dashboard and create API keys.

**Acceptance Criteria:**

**Given** POST /api/v1/auth/register with `{"email": "user@example.com", "password": "securepass"}`,
**When** the email is not already registered,
**Then** HTTP 201 is returned with `{"id": "<uuid>", "email": "user@example.com", "tier": "free", "created_at": "..."}` and the user is saved in the `users` table.

**Given** POST /api/v1/auth/register with a duplicate email,
**When** called,
**Then** HTTP 400 is returned with error code `EMAIL_ALREADY_EXISTS`.

**Given** POST /api/v1/auth/register with a missing or empty password,
**When** called,
**Then** HTTP 422 is returned with Pydantic validation error.

**Given** the `users` table after registration,
**When** reviewed,
**Then** passwords are stored as bcrypt hash; no plaintext password exists anywhere in the DB.

**Given** a new user record is created in the `users` table,
**When** the registration transaction commits,
**Then** a corresponding `credit_balances` row is created automatically with `credits_used=0`, `monthly_limit=1000`, `tier='free'`, `reset_date` = first day of next month.

**Given** Alembic migration `001_create_users`,
**When** `alembic upgrade head` is run,
**Then** the `users` table is created with columns: `id` (UUID PK), `email` (unique, not null), `password_hash` (varchar), `tier` (varchar default 'free'), `created_at` (timestamptz).

---

### Story 2.2: User Login & JWT Authentication

As a registered developer,
I want to log in and receive a JWT token,
So that I can make authenticated requests to dashboard endpoints.

**Acceptance Criteria:**

**Given** POST /api/v1/auth/login with valid `{"email": "...", "password": "..."}`,
**When** called,
**Then** HTTP 200 is returned with `{"access_token": "<jwt>", "token_type": "bearer"}`.

**Given** POST /api/v1/auth/login with a wrong password,
**When** called,
**Then** HTTP 401 is returned with error code `INVALID_CREDENTIALS` (same message for wrong password and unknown email to prevent enumeration).

**Given** a valid JWT,
**When** decoded,
**Then** it contains `user_id` (UUID) and `exp` claims; token expires in 24 hours.

**Given** a protected dashboard endpoint (e.g. GET /api/v1/keys) called without a JWT,
**When** called,
**Then** HTTP 401 is returned with error code `MISSING_AUTH_TOKEN`.

**Given** a protected dashboard endpoint called with an expired JWT,
**When** called,
**Then** HTTP 401 is returned with error code `TOKEN_EXPIRED`.

---

### Story 2.3: API Key Generation

As an authenticated developer,
I want to generate a new API key for my account,
So that I can authenticate my scraping API requests.

**Acceptance Criteria:**

**Given** POST /api/v1/keys with a valid JWT,
**When** called,
**Then** HTTP 201 is returned with `{"id": "<uuid>", "key": "rsl_<url-safe-base64-32-bytes>", "created_at": "..."}` — this is the **only** time the plaintext key is returned.

**Given** the `api_keys` table after key creation,
**When** reviewed,
**Then** only the SHA-256 hash of the key is stored; the plaintext key does not exist in the database (NFR-07).

**Given** Alembic migration `002_create_api_keys`,
**When** `alembic upgrade head` is run,
**Then** the `api_keys` table is created with: `id` (UUID PK), `user_id` (UUID FK → users), `key_hash` (varchar, indexed), `name` (varchar nullable), `is_active` (bool default true), `created_at` (timestamptz). Index: `ix_api_keys_key_hash`, `ix_api_keys_user_id`.

**Given** the generated key format,
**When** inspected,
**Then** it starts with `rsl_` and the remainder is URL-safe base64 encoding of 32 cryptographically random bytes.

**Given** calling POST /api/v1/keys multiple times for the same user,
**When** each call succeeds,
**Then** each returns a unique key; a user may have multiple active keys.

---

### Story 2.4: API Key Management (List, Revoke, Regenerate)

As an authenticated developer,
I want to list, revoke, and regenerate my API keys,
So that I can maintain security control over my account access.

**Acceptance Criteria:**

**Given** GET /api/v1/keys with a valid JWT,
**When** called,
**Then** HTTP 200 is returned with `{"items": [...], "total": N}` — each item includes `id`, `name`, `created_at`, `is_active`; `key_hash` is never returned.

**Given** DELETE /api/v1/keys/{key_id} with valid JWT and the key belonging to the authenticated user,
**When** called,
**Then** HTTP 200 is returned and `is_active` is set to `false` in the DB; the key no longer works for authentication.

**Given** DELETE /api/v1/keys/{key_id} with a key belonging to a different user,
**When** called,
**Then** HTTP 403 is returned with error code `FORBIDDEN`.

**Given** POST /api/v1/keys/{key_id}/regenerate with valid JWT,
**When** called,
**Then** the old key is deactivated, a new key is created, and the response returns the new plaintext key once (same format as Story 2.3 AC-1).

**Given** a revoked key used in the `Authorization` header for a scraping request,
**When** called,
**Then** HTTP 401 is returned with error code `INVALID_API_KEY`.

---

### Story 2.5: API Request Authentication Middleware

As the Resili API,
I want to authenticate every scraping request via API key in the Authorization header,
So that only authorized users can access scraping endpoints.

**Acceptance Criteria:**

**Given** POST /api/v1/scrape/fetch with `Authorization: Bearer rsl_<valid-active-key>`,
**When** the key is valid,
**Then** the request proceeds; the authenticated `User` object is available via `Depends(get_current_user)`.

**Given** a scraping endpoint called without an `Authorization` header,
**When** called,
**Then** HTTP 401 is returned with error code `MISSING_API_KEY` and hint to add the `Authorization: Bearer <key>` header.

**Given** a scraping endpoint called with a malformed key (not matching `rsl_` format),
**When** called,
**Then** HTTP 401 is returned with error code `INVALID_API_KEY`.

**Given** Redis is available and a valid API key is looked up,
**When** the same key is used within 5 minutes,
**Then** subsequent lookups are served from Redis cache (TTL 5 min) without hitting PostgreSQL.

**Given** all scraping route handlers (`scrape.py`),
**When** reviewed,
**Then** no handler manually verifies the API key — all authentication flows through `Depends(get_current_user)`.

---

### Story 2.6: SSRF Protection Guard

As the Resili API,
I want to block requests targeting private or internal IP addresses,
So that the scraping endpoints cannot be abused to probe internal network resources.

**Acceptance Criteria:**

**Given** `validate_url("http://192.168.1.1/data")`,
**When** called,
**Then** `SSRFBlockedError` is raised and the API returns HTTP 400 with error code `SSRF_BLOCKED` (RFC 1918 block).

**Given** `validate_url("http://10.0.0.1/internal")`,
**When** called,
**Then** `SSRFBlockedError` is raised (10.x/8 RFC 1918 range).

**Given** `validate_url("http://127.0.0.1/local")`,
**When** called,
**Then** `SSRFBlockedError` is raised (localhost).

**Given** `validate_url("http://169.254.169.254/latest/meta-data/")`,
**When** called,
**Then** `SSRFBlockedError` is raised (AWS metadata link-local).

**Given** `validate_url("http://[::1]/")`,
**When** called,
**Then** `SSRFBlockedError` is raised (IPv6 localhost).

**Given** `validate_url("https://example.com/page")`,
**When** called,
**Then** no exception is raised (valid public URL passes through).

**Given** both `POST /api/v1/scrape/fetch` and `POST /api/v1/scrape/dynamic`,
**When** reviewed,
**Then** `validate_url()` is invoked **before** any network connection is attempted.

---

### Story 2.7: Credit Balance Database Initialization

As the Resili billing system,
I want a `credit_balances` table created and wired to user registration,
So that every new user immediately has a trackable credit quota.

**Acceptance Criteria:**

**Given** Alembic migration `003_create_credit_balances`,
**When** `alembic upgrade head` is run,
**Then** the `credit_balances` table is created with: `id` (UUID PK), `user_id` (UUID FK unique → users), `credits_used` (int default 0), `monthly_limit` (int default 1000), `tier` (varchar default 'free'), `reset_date` (date), `updated_at` (timestamptz).

**Given** the `credit_balances` table exists,
**When** a new user completes registration (Story 2.1),
**Then** the service layer creates the `credit_balances` row atomically within the same registration transaction.

**Given** app startup with no `credit_balances` rows for existing users,
**When** `alembic upgrade head` is run,
**Then** a backfill step creates `credit_balances` rows for any users that don't have one yet (idempotent, safe to run multiple times).

---

## Epic 3: Core Scraping API & Credit Enforcement

Developers có thể gọi Fetcher và DynamicFetcher endpoints để nhận Markdown/JSON sạch. Credits được deduct atomic và tier limits được enforced ngay từ đầu.

### Story 3.1: Credit Balance & Usage Events DB Setup

As the Resili billing system,
I want database tables for credit balances and usage events,
So that credit tracking and usage history can be stored with proper atomicity guarantees.

**Acceptance Criteria:**

**Given** Alembic migration `004_create_usage_events`,
**When** `alembic upgrade head` is run,
**Then** the `usage_events` table is created with: `id` (UUID PK), `user_id` (UUID FK), `endpoint_type` (varchar: 'fetcher' | 'dynamic'), `credits_used` (int), `url_hash` (varchar — SHA-256 of original URL), `status` (varchar: 'success' | 'error'), `created_at` (timestamptz). Indexes: `ix_usage_events_user_id`, `ix_usage_events_created_at`.

**Given** the `usage_events` table schema,
**When** reviewed,
**Then** there is NO column for raw URL — only `url_hash` (NFR-09 compliance).

**Given** an APScheduler job configured in `app/main.py` startup event,
**When** the app is running,
**Then** a daily scheduled job prunes `usage_events` rows where `created_at < NOW() - INTERVAL '90 days'` (NFR-09).

---

### Story 3.2: Credit Accounting Service & Tier Enforcement

As the Resili billing system,
I want atomic credit deduction and tier enforcement before any scrape executes,
So that users cannot exceed their quota and credits are never double-charged.

**Acceptance Criteria:**

**Given** `billing/service.py.deduct_credits(db, user_id, cost)` called within a transaction,
**When** the user has sufficient credits,
**Then** it executes `SELECT FOR UPDATE` on `credit_balances`, deducts atomically, logs to `usage_events`, and Redis balance cache is invalidated (Dec-G).

**Given** `deduct_credits()` called when the user has 0 remaining credits,
**When** called,
**Then** `CreditsExhaustedError` is raised; no `usage_events` row is written for the failed attempt.

**Given** `Depends(require_credits(cost=1))` on a Fetcher endpoint, with a Free tier user at 0 remaining credits,
**When** called,
**Then** HTTP 429 is returned with error code `CREDITS_EXHAUSTED`, `Retry-After` header set to seconds until `reset_date`, and body message: "Your fetcher credits for this month are exhausted. They reset on <date>" (FR-13).

**Given** `Depends(require_credits(cost=5))` on DynamicFetcher, with a Free tier user (any credit level),
**When** called,
**Then** HTTP 403 is returned with error code `DYNAMIC_NOT_AVAILABLE_FREE_TIER` and hint "Upgrade to Pro to access DynamicFetcher" (FR-11).

**Given** 100 concurrent `deduct_credits()` calls for the same user with exactly 50 credits remaining,
**When** all resolve,
**Then** exactly 50 succeed (credits go to 0) and 50 raise `CreditsExhaustedError` — no over-deduction occurs due to `SELECT FOR UPDATE`.

**Given** all scraping route handlers,
**When** reviewed,
**Then** `Depends(require_credits(cost=N))` is used in the handler signature — no manual credit check inside handler body.

---

### Story 3.3: Fetcher Endpoint

As a developer using Resili,
I want to call a Fetcher endpoint with a URL and receive clean Markdown or JSON,
So that I can integrate static web page content into my AI pipeline without managing scraping infrastructure.

**Acceptance Criteria:**

**Given** POST /api/v1/scrape/fetch with `{"url": "https://example.com", "format": "markdown"}` and a valid API key with credits,
**When** the page loads successfully,
**Then** HTTP 200 is returned with `{"job_id": null, "status": "completed", "result": {"content": "<markdown>", "format": "markdown", "credits_used": 1}}`.

**Given** POST /api/v1/scrape/fetch with `{"url": "https://example.com", "format": "json"}`,
**When** called,
**Then** `result.content` is a JSON string of structured data extracted from the page.

**Given** POST /api/v1/scrape/fetch without a `format` field,
**When** called,
**Then** `format` defaults to `"markdown"` (FR-06).

**Given** POST /api/v1/scrape/fetch with `{"respect_robots_txt": true}` and a URL disallowed by robots.txt,
**When** called,
**Then** HTTP 400 with error code `ROBOTS_TXT_DISALLOWED` is returned (NFR-10).

**Given** a successful Fetcher call,
**When** the `usage_events` table is checked,
**Then** a new append-only row exists with `endpoint_type='fetcher'`, `credits_used=1`, `url_hash=SHA256(url)`, `status='success'`.

**Given** Fetcher p95 response time measured under ≤ 100 concurrent requests,
**When** measured via Sentry APM,
**Then** p95 ≤ 3 seconds (NFR-02).

---

### Story 3.4: DynamicFetcher Endpoint

As a developer using Resili,
I want to call a DynamicFetcher endpoint that fully renders JavaScript before returning content,
So that I can scrape JS-heavy pages that Fetcher cannot handle.

**Acceptance Criteria:**

**Given** POST /api/v1/scrape/dynamic with `{"url": "https://spa-example.com"}` and a valid Pro API key,
**When** the page renders successfully,
**Then** HTTP 200 is returned with `{"job_id": null, "status": "completed", "result": {"content": "<rendered-markdown>", "format": "markdown", "credits_used": 5}}` (Dec-F async-ready shape).

**Given** each DynamicFetcher request,
**When** processed,
**Then** it creates a new isolated Playwright browser context; the context is closed in a `finally` block regardless of success or error (NFR-04).

**Given** a DynamicFetcher request on a page that takes > 30 seconds to render,
**When** the timeout fires,
**Then** the Playwright context is closed, HTTP 200 with `status: "error"` (or 408 equivalent) is returned with error code `DYNAMIC_TIMEOUT` and hint "Page took >30s to render. Try Fetcher for static content" (FR-07).

**Given** the async-ready response shape,
**When** reviewed,
**Then** the response always includes `job_id: null` and `status: "completed"` at MVP — this structure is forward-compatible with Growth phase async job queue (NFR-12).

**Given** `Dockerfile.worker`,
**When** built and run,
**Then** `playwright install chromium` has been executed; the worker service handles Playwright requests from the FastAPI pool.

**Given** DynamicFetcher p95 under ≤ 20 concurrent Playwright sessions,
**When** measured,
**Then** p95 ≤ 15 seconds (NFR-03).

---

### Story 3.5: Scraping Error Handling & Rate Limit Responses

As a developer using Resili,
I want clear, actionable error messages for every failure mode,
So that I can understand what went wrong and fix it within 2 minutes (UJ-04).

**Acceptance Criteria:**

**Given** any scraping failure,
**When** an error response is returned,
**Then** it follows Dec-D schema: `{"error": {"code": "SCREAMING_SNAKE_CASE", "message": "Human-readable description", "hint": "Suggested next action", "docs_url": "https://docs.resili.io/errors/<code>"}}` (FR-07).

**Given** POST /api/v1/scrape/fetch with `{"url": "not-a-url"}`,
**When** called,
**Then** HTTP 400 with error code `INVALID_URL` is returned.

**Given** a URL that returns HTTP 404 from the target,
**When** Fetcher is called,
**Then** error code `TARGET_NOT_FOUND` is returned with message "The target URL returned a 404 Not Found response."

**Given** a page with active anti-bot protection that blocks the Fetcher,
**When** Fetcher is called,
**Then** error code `ANTI_BOT_DETECTED` is returned with hint "Use /api/v1/scrape/dynamic for JS-heavy or bot-protected pages." (UJ-03).

**Given** a user who has exhausted monthly quota,
**When** they check the 429 error body,
**Then** `message` names the specific credit type exhausted and `hint` includes the exact reset date (FR-13).

---

## Epic 4: MCP Server Integration

AI Agents (Claude Desktop, Cursor, OpenAI) có thể kết nối Resili qua MCP stdio với 1 dòng JSON config và gọi scraping tools trực tiếp.

### Story 4.1: MCP Server Process & stdio Transport

As an AI agent developer,
I want a standalone MCP server process that connects Resili to my agent client,
So that I can add Resili scraping capability with a single config entry and no wrapper code.

**Acceptance Criteria:**

**Given** `python backend/mcp_server.py` is run with `RESILI_API_KEY` set in environment,
**When** started,
**Then** the process accepts MCP stdio protocol messages without error.

**Given** `mcp_server.py`,
**When** reviewed,
**Then** it directly imports `app.scraping.fetcher` and `app.scraping.dynamic` — it makes **no** HTTP calls to the FastAPI server (Dec-E).

**Given** Claude Desktop `mcp_config.json` with entry: `{"resili": {"command": "python", "args": ["path/to/mcp_server.py"], "env": {"RESILI_API_KEY": "rsl_..."}}}`,
**When** added and Claude Desktop is restarted,
**Then** Resili tools appear in the tool list (FR-08).

**Given** the MCP server process crashes,
**When** it crashes,
**Then** the FastAPI API server continues running independently — confirmed by: API returns 200 after MCP process is killed (process isolation, Dec-E).

**Given** `mcp_server.py`,
**When** reviewed,
**Then** it declares a top-level constant `MCP_SPEC_VERSION` with the MCP protocol version it implements.

---

### Story 4.2: MCP Tool Implementations

As an AI agent,
I want clearly-described MCP tools for fetching static and dynamic web pages,
So that I can autonomously select the right tool based on the task context without human guidance.

**Acceptance Criteria:**

**Given** the MCP server is running and tools are listed,
**When** inspected,
**Then** both `fetch_page` and `fetch_dynamic_page` tools are present (FR-09).

**Given** the `fetch_page` tool description,
**When** read by an LLM,
**Then** it clearly conveys: "Use for static pages, documentation, news articles — no JavaScript rendering required. Fast (1–3s). Costs 1 credit."

**Given** the `fetch_dynamic_page` tool description,
**When** read by an LLM,
**Then** it clearly conveys: "Use for JavaScript-heavy pages, SPAs, dashboards that require browser rendering. Slower (5–15s). Costs 5 credits. Requires Pro tier."

**Given** `fetch_page(url="https://example.com", format="markdown")` MCP tool call with a valid key,
**When** executed,
**Then** the response matches the REST API ScrapeResponse schema: `{"job_id": null, "status": "completed", "result": {"content": "...", "format": "markdown", "credits_used": 1}}`.

**Given** `fetch_dynamic_page` MCP tool call with a Free tier key,
**When** executed,
**Then** the MCP error response contains a message equivalent to HTTP 403 `DYNAMIC_NOT_AVAILABLE_FREE_TIER` with upgrade hint.

---

### Story 4.3: MCP Spec Compatibility & Setup Documentation

As an AI agent developer,
I want clear MCP spec compatibility information and copy-paste setup instructions,
So that I can diagnose connection issues and integrate Resili into any MCP-compatible client.

**Acceptance Criteria:**

**Given** an MCP client using an incompatible protocol version,
**When** it connects to the MCP server,
**Then** the error response includes: the MCP spec version Resili supports (`MCP_SPEC_VERSION`), the version sent by the client, and a docs URL (FR-10).

**Given** `docs/mcp-setup.md` (or a README section),
**When** reviewed,
**Then** it contains: exact 1-line JSON config for Claude Desktop, Cursor, and OpenAI agent tools; `RESILI_API_KEY` environment variable setup instructions; and the supported `MCP_SPEC_VERSION`.

**Given** any MCP tool error (auth failure, credits exhausted, SSRF blocked),
**When** returned,
**Then** the error follows a consistent schema compatible with MCP protocol error message format.

---

## Epic 5: Dashboard, Billing & Notifications

Users có full dashboard experience — usage visualization, email alerts, 1-click upgrade. Toàn bộ frontend implement theo `docs/DESIGN.md`.

### Story 5.1: Frontend Design Token System & Core Components

As a frontend developer,
I want the DESIGN.md token system implemented as Tailwind config and CSS variables,
So that all UI components have a consistent dark-canvas visual identity from the start.

**Acceptance Criteria:**

**Given** `tailwind.config.ts`,
**When** reviewed,
**Then** it extends the default palette with all DESIGN.md color tokens: `canvas` (#000000), `surface-card` (#0a0a0c), `surface-elevated` (#101012), `surface-deep` (#06060a), `hairline` (rgba(255,255,255,0.06)), `hairline-strong` (rgba(255,255,255,0.14)), `ink` (#fcfdff), `body`, `charcoal`, `mute`, `ash`, and 5 accent colors with `-glow` variants (UX-DR1, UX-DR3).

**Given** the entire frontend codebase,
**When** searched for `box-shadow`, `drop-shadow`, or `shadow-` Tailwind utilities,
**Then** none are found — elevation is built exclusively from surface color shifts and hairline borders (UX-DR13).

**Given** the `Button` component variants,
**When** rendered,
**Then**: `button-primary` = `bg-primary text-primary-on h-9 rounded-md px-4`; `button-ghost` = `bg-surface-elevated text-ink border border-hairline-strong h-9 rounded-md`; `button-outline` = `bg-canvas text-ink border border-hairline-strong h-9 rounded-md` (UX-DR5).

**Given** `tailwind.config.ts` breakpoints,
**When** reviewed,
**Then** the 6 DESIGN.md breakpoints are configured: mobile (425px), tablet (768px), tablet-lg (1024px), desktop (1280px), desktop-xl (1440px) (UX-DR12).

**Given** Inter and Geist Mono fonts,
**When** configured via `next/font`,
**Then** Tailwind `fontFamily.sans` is set to Inter and `fontFamily.mono` to Geist Mono (UX-DR2).

**Given** the DESIGN.md proprietary font requirements (Domaine Display, ABC Favorit),
**When** implementing the font stack,
**Then** the developer makes an explicit decision documented in a code comment in `tailwind.config.ts` — either:
(a) **Licensed:** Domaine Display and ABC Favorit loaded via `@font-face` from `/public/fonts/`; `fontFamily.serif` = Domaine Display, `fontFamily.display` = ABC Favorit; OR
(b) **Fallback (default if no license):** `fontFamily.serif` uses `'Tiempos Headline', Georgia, serif` and `fontFamily.display` uses `'Inter Tight', Inter, sans-serif` — with comment `// Fallback for Domaine Display / ABC Favorit — replace with licensed fonts when available`.
Either path produces a visually coherent result per DESIGN.md Do's and Don'ts.

---

### Story 5.2: Dashboard Shell, Auth Pages & Navigation

As a developer,
I want to log in and access a structured dashboard with navigation,
So that I can manage my API keys and usage from a clean, branded interface.

**Acceptance Criteria:**

**Given** a logged-out user visiting `/dashboard`,
**When** redirected,
**Then** they are sent to `/login`.

**Given** the `/login` page,
**When** rendered,
**Then** it displays: email + password `text-input` fields (bg `surface-card`, `rounded-md`, height 40px, focus border `ink` — UX-DR11), a `button-primary` "Sign in" CTA, all on a `canvas` (#000) background.

**Given** a successful login,
**When** redirected to `/dashboard`,
**Then** the dashboard layout renders with: `nav-bar` (height 64px, `hairline` bottom border, logo left, user menu right — UX-DR8), sidebar navigation with links to "API Keys" and "Usage", and main content area.

**Given** `/dashboard/page.tsx`,
**When** rendered,
**Then** it shows a Quick Start guide with a `code-window` component displaying a real `curl` example pre-filled with the user's API key (SC-04, UX-DR7).

**Given** the `nav-bar` at viewport < 1024px,
**When** rendered,
**Then** center navigation links collapse to a hamburger icon; logo and `button-primary` remain visible (UX-DR8 mobile).

---

### Story 5.3: OpenAPI Type Generation & API Client

As a frontend developer,
I want auto-generated TypeScript types from the FastAPI OpenAPI spec,
So that all API calls are type-safe without manual type maintenance.

**Acceptance Criteria:**

**Given** `npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/types.ts` run with the backend live,
**When** executed,
**Then** `types.ts` is generated without errors and contains typed interfaces for all request/response schemas defined in Epics 2 and 3 (Arch-13).

**Given** `src/lib/api/client.ts`,
**When** reviewed,
**Then** it: attaches `Authorization: Bearer {api_key}` header to all requests; parses error responses extracting the Dec-D `error` object; throws a typed `ApiError` on non-2xx responses.

**Given** `src/lib/api/endpoints.ts`,
**When** reviewed,
**Then** it exports typed wrapper functions: `getKeys()`, `createKey()`, `revokeKey()`, `regenerateKey()`, `getUsage(period)`, `getCredits()` — each using types from `types.ts`.

**Given** passing an incorrect field type to an endpoint wrapper,
**When** TypeScript compiles,
**Then** it fails with a type error pointing to the mismatch (type safety enforced at compile time).

---

### Story 5.4: API Key Management UI

As a developer,
I want to create, view, copy, revoke, and regenerate API keys from the dashboard,
So that I can manage my Resili access without touching the raw API.

**Acceptance Criteria:**

**Given** `/dashboard/keys`,
**When** rendered,
**Then** it lists all active API keys via `api-key-list.tsx`: each row shows name/id, `created_at`, masked key (e.g. `rsl_****1234`), "Revoke" and "Regenerate" buttons.

**Given** clicking "Create new key",
**When** the API responds,
**Then** the full plaintext key is displayed once in a highlighted `code-window`-styled box with a "Copy to clipboard" button; after dismissing, the key is masked and cannot be retrieved again.

**Given** clicking "Copy to clipboard" on the creation dialog,
**When** clicked,
**Then** the key is copied to the clipboard and the button label changes to "Copied ✓" for 2 seconds.

**Given** clicking "Revoke" on a key,
**When** confirmed in a confirmation dialog,
**Then** DELETE `/api/v1/keys/{id}` is called, the key disappears from the list, and a toast notification confirms "Key revoked."

**Given** the `api-key-list.tsx` component data loading,
**When** loading,
**Then** a skeleton loader is shown using TanStack Query's `isLoading` state — no manual `useState(loading)` exists in the component (Arch-11).

---

### Story 5.5: Usage Dashboard & Real-Time Credit Display

As a developer,
I want to see my API usage charts and current credit balance in the dashboard,
So that I can monitor consumption and plan usage accordingly.

**Acceptance Criteria:**

**Given** GET /api/v1/usage with `?period=daily` (or `weekly` / `monthly`) and a valid JWT,
**When** called,
**Then** HTTP 200 is returned with aggregated data: `{"period": "daily", "items": [{"date": "2026-05-11", "fetcher_credits": 45, "dynamic_credits": 15}], "total_fetcher": N, "total_dynamic": M}` (FR-16).

**Given** `/dashboard/usage`,
**When** rendered,
**Then** a Recharts chart displays Fetcher credits and Dynamic credits as separate series; a period switcher toggles between daily / weekly / monthly views (FR-16).

**Given** the `credit-badge.tsx` component,
**When** rendered in the dashboard header,
**Then** it displays: current `credits_used`, `monthly_limit`, tier label ("Free" / "Pro"), and a progress bar showing percentage used (FR-03).

**Given** the `useCredits()` hook,
**When** the dashboard is open,
**Then** TanStack Query refetches credit data every 60 seconds for near-real-time updates; no manual polling loop exists in the component (FR-03).

**Given** Recharts chart colors,
**When** rendered,
**Then** Fetcher series uses `accent-blue` and Dynamic series uses `accent-orange` from the design token system — no default Recharts colors are used.

---

### Story 5.6: Stripe Billing & 1-Click Tier Upgrade

As a developer on the Free tier,
I want to upgrade to Pro with a single click from the dashboard,
So that I can access DynamicFetcher without contacting sales (FR-15).

**Acceptance Criteria:**

**Given** a Free tier user clicking "Upgrade to Pro" in the dashboard,
**When** clicked,
**Then** they are redirected to a Stripe Checkout session for the Pro plan.

**Given** a completed Stripe Checkout payment,
**When** the `customer.subscription.updated` webhook fires to POST /api/v1/billing/webhook,
**Then** `billing/stripe_service.py` updates `users.tier` to `'pro'` and `credit_balances.monthly_limit` to `10000`; the dashboard reflects the new tier on next refresh (FR-15).

**Given** POST /api/v1/billing/webhook called without a valid `Stripe-Signature` header,
**When** called,
**Then** HTTP 400 is returned (webhook security).

**Given** `billing/stripe_service.py`,
**When** reviewed,
**Then** Stripe webhook secret is read from `settings.STRIPE_WEBHOOK_SECRET` — not hardcoded.

---

### Story 5.7: Quota Email Notifications & Alert Banner

As a developer approaching their monthly quota,
I want an email notification and in-dashboard warning when I reach 80% usage,
So that I can decide to optimize or upgrade before exhausting my credits (FR-14).

**Acceptance Criteria:**

**Given** `billing/service.py.deduct_credits()` completing a deduction that brings the user to ≥ 80% of `monthly_limit`,
**When** deduction completes,
**Then** `notifications/service.py.send_quota_warning_email(user_id)` is called (FR-14).

**Given** `send_quota_warning_email()`,
**When** called,
**Then** it sends an email via Resend SDK with: subject "You've used 80% of your Resili credits this month", body with Fetcher/Dynamic breakdown, and a direct deep-link to `/dashboard/usage` — not the homepage (FR-14).

**Given** a user already past 80% making another API call (still within limit),
**When** `deduct_credits()` runs,
**Then** NO second quota-warning email is sent — at most one warning email per billing period per threshold crossing.

**Given** the `quota-alert.tsx` banner component,
**When** rendered in the dashboard and the user's balance is ≤ 20% remaining,
**Then** a non-dismissible banner appears: "You've used 80% of your credits this month." with an "Upgrade to Pro" `button-primary` button.

**Given** `settings.RESEND_API_KEY`,
**When** reviewed in `notifications/service.py`,
**Then** the Resend API key is read from `settings.RESEND_API_KEY` (not hardcoded).
