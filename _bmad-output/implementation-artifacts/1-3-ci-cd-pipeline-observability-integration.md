# Story 1.3: CI/CD Pipeline & Observability Integration

Status: done

## Story

As a development team,
I want automated testing, linting, and deployment pipelines with error monitoring,
so that code quality is enforced automatically and production errors are visible.

## Acceptance Criteria

1. **Given** a PR opened against `main`, **When** the CI pipeline (`.github/workflows/ci.yml`) runs, **Then** it executes in sequence: `pytest tests/` (backend), `ruff check .` (backend lint), `mypy .` (backend types), `npm test` (frontend Jest).

2. **Given** a push to `main`, **When** the deploy pipeline (`.github/workflows/deploy.yml`) runs, **Then** it deploys the backend to Railway/Render and (optionally) the frontend to Vercel.

3. **Given** `SENTRY_DSN` is set in environment, **When** FastAPI starts, **Then** `sentry_sdk.init()` is called in `app/main.py` and unhandled exceptions are captured.

4. **Given** `NEXT_PUBLIC_SENTRY_DSN` is set, **When** the Next.js app starts, **Then** Sentry is initialized in `src/app/layout.tsx`.

5. **Given** any FastAPI HTTP response, **When** inspected, **Then** the response includes `X-Powered-By: Resili (built on Scrapling — BSD License)` header (NFR-11).

6. **Given** `pyproject.toml`, **When** reviewed, **Then** `ruff` and `mypy` are configured with appropriate rules for the `backend/` codebase.

## Tasks / Subtasks

- [x] Tạo GitHub Actions CI workflow (AC: 1)
  - [x] Tạo `.github/workflows/ci.yml`
  - [x] Backend job: `pytest tests/`, `ruff check .`, `mypy .`
  - [x] Frontend job: `npm test`
  - [x] Trigger: `on: pull_request: branches: [main]`

- [x] Tạo GitHub Actions Deploy workflow (AC: 2)
  - [x] Tạo `.github/workflows/deploy.yml`
  - [x] Trigger: `on: push: branches: [main]`
  - [x] Backend deploy step đến Railway/Render
  - [x] (Optional) Frontend deploy đến Vercel

- [x] Integrate Sentry vào FastAPI (AC: 3, 5)
  - [x] `app/main.py`: add `sentry_sdk.init()` conditional on `settings.SENTRY_DSN`
  - [x] Verify `X-Powered-By` header middleware từ Story 1.2 đang hoạt động

- [x] Integrate Sentry vào Next.js (AC: 4)
  - [x] Install `@sentry/nextjs`
  - [x] Tạo `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`
  - [x] Update `next.config.ts` với Sentry plugin
  - [x] Add Sentry init trong `src/app/layout.tsx` nếu `NEXT_PUBLIC_SENTRY_DSN` set

- [x] Verify pyproject.toml ruff + mypy config (AC: 6)
  - [x] Đảm bảo config từ Story 1.1 đầy đủ

## Dev Notes

### `.github/workflows/ci.yml`

```yaml
name: CI

on:
  pull_request:
    branches: [main]

jobs:
  backend-test:
    runs-on: ubuntu-latest
    services:
      postgres:
        image: postgres:16
        env:
          POSTGRES_USER: resili
          POSTGRES_PASSWORD: resili
          POSTGRES_DB: resili_test
        ports:
          - 5432:5432
        options: --health-cmd pg_isready --health-interval 10s --health-timeout 5s --health-retries 5
      redis:
        image: redis:7
        ports:
          - 6379:6379

    steps:
      - uses: actions/checkout@v4

      - name: Set up Python 3.13
        uses: actions/setup-python@v5
        with:
          python-version: "3.13"

      - name: Install dependencies
        working-directory: backend
        run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Install Playwright
        working-directory: backend
        run: playwright install chromium

      - name: Run tests
        working-directory: backend
        env:
          DATABASE_URL: postgresql+psycopg://resili:resili@localhost:5432/resili_test
          REDIS_URL: redis://localhost:6379
          SECRET_KEY: test-secret-key-for-ci
        run: pytest tests/ -v

      - name: Lint with ruff
        working-directory: backend
        run: ruff check .

      - name: Type check with mypy
        working-directory: backend
        run: mypy .

  frontend-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Node 20
        uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
          cache-dependency-path: frontend/package-lock.json

      - name: Install dependencies
        working-directory: frontend
        run: npm ci

      - name: Run tests
        working-directory: frontend
        run: npm test -- --passWithNoTests
```

### `.github/workflows/deploy.yml`

```yaml
name: Deploy

on:
  push:
    branches: [main]

jobs:
  deploy-backend:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      # Railway deployment — add RAILWAY_TOKEN secret in GitHub repo settings
      - name: Install Railway CLI
        run: npm install -g @railway/cli

      - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --service api
        # Alternative for Render: use Render deploy hook
        # curl -X POST ${{ secrets.RENDER_DEPLOY_HOOK }}

  deploy-frontend:
    runs-on: ubuntu-latest
    # Optional: Uncomment and add secrets (VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID) to enable
    if: ${{ vars.ENABLE_VERCEL_DEPLOY == 'true' }}
    steps:
      - uses: actions/checkout@v4
      # Vercel deployment — optional, can deploy manually
      # Add VERCEL_TOKEN, VERCEL_ORG_ID, VERCEL_PROJECT_ID secrets if needed
```

### Sentry trong FastAPI — `app/main.py` update

```python
import sentry_sdk
from app.core.config import settings

def create_app() -> FastAPI:
    # Sentry init TRƯỚC khi app được create (Dec-M)
    if settings.SENTRY_DSN:
        sentry_sdk.init(
            dsn=settings.SENTRY_DSN,
            traces_sample_rate=0.1,  # 10% performance monitoring
            environment="production",
        )

    app = FastAPI(...)
    # ... rest of factory
```

**QUAN TRỌNG:** `sentry_sdk.init()` phải được gọi **trước** khi `FastAPI()` được khởi tạo để capture initialization errors.

### Sentry trong Next.js

```bash
# Install
npm install @sentry/nextjs
npx @sentry/wizard@latest -i nextjs
```

**`sentry.client.config.ts`:**
```typescript
import * as Sentry from "@sentry/nextjs";

Sentry.init({
  dsn: process.env.NEXT_PUBLIC_SENTRY_DSN,
  tracesSampleRate: 0.1,
});
```

**`src/app/layout.tsx`** — Sentry init conditional:
```typescript
// Sentry is initialized via sentry.client.config.ts and sentry.server.config.ts
// No manual init needed in layout.tsx if using @sentry/nextjs with next.config.ts integration
```

Dùng `withSentryConfig()` trong `next.config.ts`:
```typescript
import { withSentryConfig } from "@sentry/nextjs";
export default withSentryConfig(nextConfig, { silent: true });
```

### X-Powered-By Header Verification (AC: 5)

Header này đã được implement trong Story 1.2 middleware. Trong story này chỉ cần verify test passes:

```python
async def test_attribution_header(client: AsyncClient):
    response = await client.get("/health")
    assert response.headers.get("X-Powered-By") == "Resili (built on Scrapling - BSD License)"
```

**Lưu ý:** HTTP header encoding giới hạn latin-1, nên dùng hyphen `-` thay vì em dash `—`.

### Pytest Configuration

Thêm vào `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py313"

[tool.ruff.lint]
select = ["E", "F", "I", "N", "UP"]

[tool.mypy]
python_version = "3.13"
strict = false
ignore_missing_imports = true
exclude = ["alembic/"]
```

### Project Structure Notes

- CI chạy backend và frontend tests song song (separate jobs)
- Deploy chỉ trigger khi push lên `main` (không phải PR)
- `RAILWAY_TOKEN`, `SENTRY_DSN`, `NEXT_PUBLIC_SENTRY_DSN` → GitHub repo secrets
- Playwright phải được install trong CI backend job (Dockerfile.worker approach)

### References

- [Source: architecture.md#Dec-M-Error-Monitoring] — Sentry setup
- [Source: architecture.md#Dec-O-CI/CD-Pipeline] — GitHub Actions
- [Source: epics.md#Story-1.3] — acceptance criteria
- [Source: architecture.md#Gap-Analysis-Results] — BSD attribution header (NFR-11)

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

- **X-Powered-By header**: HTTP headers require latin-1 encoding. Em dash `—` (U+2014) là non-latin-1. Sử dụng hyphen `-` để đảm bảo compatibility. Đây là behavior đúng vì spec gốc có typo.
- **Sentry test approach**: Test `create_app()` trực tiếp với patched settings thay vì `importlib.reload()` để tránh re-import bypass patch.
- **ruff config deprecation**: `select` đã được di chuyển sang `[tool.ruff.lint]` section trong ruff >= 0.1.0.

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created
- CI workflow tạo với backend (pytest + ruff + mypy) và frontend jobs chạy parallel
- Deploy workflow tạo với Railway backend deploy và optional Vercel frontend
- `sentry_sdk.init()` được gọi trước `FastAPI()` trong `create_app()`, conditional trên `SENTRY_DSN`
- `@sentry/nextjs` installed, 3 config files tạo (client/server/edge), `next.config.ts` updated với `withSentryConfig`
- `pyproject.toml` updated: thêm `[tool.pytest.ini_options]`, fix ruff lint config sang `[tool.ruff.lint]`, thêm `exclude = ["alembic/"]` cho mypy
- 18 pre-existing ruff errors fixed (import sorting, unused imports, type annotation modernization)
- 63 tests pass, 0 regressions

### File List

**NEW:**
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `frontend/sentry.client.config.ts`
- `frontend/sentry.server.config.ts`
- `frontend/sentry.edge.config.ts`

**UPDATE:**
- `backend/app/main.py` — add Sentry init, remove unused `Response` import
- `backend/pyproject.toml` — add pytest config, fix ruff lint section, add mypy exclude
- `frontend/next.config.ts` — add withSentryConfig
- `frontend/src/app/layout.tsx` — add Sentry comment
- `frontend/package.json` — add @sentry/nextjs dependency
- `backend/tests/api/test_health.py` — add Sentry init tests, fix import sorting
- `backend/app/core/errors.py` — fix import sorting, modernize Optional annotations
- `backend/app/db/base.py` — fix import sorting, remove unused imports
- `backend/app/db/session.py` — fix import sorting
- `backend/tests/conftest.py` — fix import sorting, remove unused pytest import
- `backend/tests/test_errors.py` — fix import sorting, remove unused pytest import
- `backend/tests/test_story_1_1_scaffold.py` — fix import sorting

### Change Log

- 2026-05-11: Story 1.3 implemented — CI/CD pipelines created, Sentry integrated into FastAPI and Next.js, pyproject.toml updated with full tooling config. 18 pre-existing ruff lint issues resolved.
- 2026-05-11: Code review complete — 9 patches applied: removed playwright from backend CI, added Redis health check, added frontend build step, added BrowserTracing to Sentry client, fixed Sentry re-init risk with `_sentry_initialized` guard, added `ENVIRONMENT` field to Settings, fixed `silent`/`hideSourceMaps` in next.config.ts, added RAILWAY_TOKEN guard. 8 items deferred.

### Review Findings

<!-- Code review conducted 2026-05-11 — 3 layers: Blind Hunter, Edge Case Hunter, Acceptance Auditor -->

**Decision-Needed (2) — Resolved:**
- [x] [Review][Decision] `environment="production"` hardcoded — resolved: thêm `ENVIRONMENT: str = "production"` vào Settings, dùng `settings.ENVIRONMENT` trong `sentry_sdk.init()`, thêm re-init guard `_sentry_initialized` [`backend/app/main.py`, `backend/app/core/config.py`]
- [x] [Review][Decision] CI jobs parallel — resolved: giữ nguyên parallel (interpret "in sequence" = steps trong job đã sequential, parallel giữa jobs là acceptable) [dismissed]

**Patch (8) — All Fixed:**
- [x] [Review][Patch] `playwright install chromium` không cần thiết trong backend CI job [`.github/workflows/ci.yml`]
- [x] [Review][Patch] Redis service thiếu health check [`.github/workflows/ci.yml:services.redis`]
- [x] [Review][Patch] Frontend CI thiếu bước `npm run build` [`.github/workflows/ci.yml:frontend-test`]
- [x] [Review][Patch] `BrowserTracing` integration thiếu trong `sentry.client.config.ts` [`frontend/sentry.client.config.ts`]
- [x] [Review][Patch] `sentry_sdk.init()` re-initialization risk — fixed với `_sentry_initialized` guard [`backend/app/main.py`]
- [x] [Review][Patch] `silent: true` → đổi thành `silent: process.env.CI !== "true"` [`frontend/next.config.ts`]
- [x] [Review][Patch] Thiếu `hideSourceMaps: true` [`frontend/next.config.ts`]
- [x] [Review][Patch] Không guard `RAILWAY_TOKEN` trước bước deploy [`.github/workflows/deploy.yml`]

**Defer (8):**
- [x] [Review][Defer] Không có pip caching trong backend CI (`cache: pip`) [`.github/workflows/ci.yml`] — deferred, performance enhancement
- [x] [Review][Defer] Không có `release` field trong Sentry configs — cần để correlate errors với deployments [all sentry configs] — deferred, enhancement
- [x] [Review][Defer] Frontend CI thiếu `eslint` và `tsc --noEmit` steps [`.github/workflows/ci.yml:frontend-test`] — deferred, beyond story 1.3 scope
- [x] [Review][Defer] `deploy-backend` và `deploy-frontend` không có `needs:` — inconsistent deploy state nếu một job fail [`.github/workflows/deploy.yml`] — deferred, nice-to-have
- [x] [Review][Defer] GitHub Actions tags không được pin theo commit SHA — supply chain security risk [all workflows] — deferred, security hardening
- [x] [Review][Defer] `SENTRY_ORG`/`SENTRY_PROJECT` absent tại build time → source maps bị skip im lặng [`frontend/next.config.ts`] — deferred, configuration concern
- [x] [Review][Defer] `npm test -- --passWithNoTests` flag che giấu trường hợp frontend chưa có test coverage [`.github/workflows/ci.yml`] — deferred, pragmatic choice
- [x] [Review][Defer] Không validate VERCEL credentials khi `ENABLE_VERCEL_DEPLOY=true` [`.github/workflows/deploy.yml`] — deferred, conditional path
