# Story 1.3: CI/CD Pipeline & Observability Integration

Status: ready-for-dev

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

- [ ] Tạo GitHub Actions CI workflow (AC: 1)
  - [ ] Tạo `.github/workflows/ci.yml`
  - [ ] Backend job: `pytest tests/`, `ruff check .`, `mypy .`
  - [ ] Frontend job: `npm test`
  - [ ] Trigger: `on: pull_request: branches: [main]`

- [ ] Tạo GitHub Actions Deploy workflow (AC: 2)
  - [ ] Tạo `.github/workflows/deploy.yml`
  - [ ] Trigger: `on: push: branches: [main]`
  - [ ] Backend deploy step đến Railway/Render
  - [ ] (Optional) Frontend deploy đến Vercel

- [ ] Integrate Sentry vào FastAPI (AC: 3, 5)
  - [ ] `app/main.py`: add `sentry_sdk.init()` conditional on `settings.SENTRY_DSN`
  - [ ] Verify `X-Powered-By` header middleware từ Story 1.2 đang hoạt động

- [ ] Integrate Sentry vào Next.js (AC: 4)
  - [ ] Install `@sentry/nextjs`
  - [ ] Tạo `sentry.client.config.ts`, `sentry.server.config.ts`, `sentry.edge.config.ts`
  - [ ] Update `next.config.ts` với Sentry plugin
  - [ ] Add Sentry init trong `src/app/layout.tsx` nếu `NEXT_PUBLIC_SENTRY_DSN` set

- [ ] Verify pyproject.toml ruff + mypy config (AC: 6)
  - [ ] Đảm bảo config từ Story 1.1 đầy đủ

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
    assert response.headers.get("x-powered-by") == "Resili (built on Scrapling — BSD License)"
```

### Pytest Configuration

Thêm vào `pyproject.toml`:
```toml
[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
target-version = "py313"

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

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**NEW:**
- `.github/workflows/ci.yml`
- `.github/workflows/deploy.yml`
- `frontend/sentry.client.config.ts`
- `frontend/sentry.server.config.ts`
- `frontend/sentry.edge.config.ts`

**UPDATE:**
- `backend/app/main.py` — add Sentry init
- `backend/pyproject.toml` — add pytest config
- `frontend/next.config.ts` — add withSentryConfig
