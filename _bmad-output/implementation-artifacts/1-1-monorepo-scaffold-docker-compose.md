# Story 1.1: Monorepo Scaffold & Docker Compose

Status: ready-for-dev

## Story

As a developer,
I want a working monorepo structure with all services running via Docker Compose,
so that I can start development immediately without manual environment setup.

## Acceptance Criteria

1. **Given** the repo is cloned and `.env` is populated from `.env.example`, **When** `docker compose up` is run, **Then** all 5 services start without errors: `api` (FastAPI on :8000), `worker` (Playwright worker), `frontend` (Next.js on :3000), `db` (PostgreSQL 16 on :5432), `redis` (Redis on :6379).

2. **Given** the running environment, **When** GET http://localhost:3000 is visited, **Then** the Next.js default page loads without error.

3. **Given** the project root after scaffold, **When** directory structure is inspected, **Then** the following exist: `backend/`, `frontend/`, `docker-compose.yml`, `.env.example`, `README.md`, `.devcontainer/devcontainer.json`, `.github/workflows/`.

4. **Given** the frontend directory, **When** package.json is reviewed, **Then** it was created with `create-next-app` using: TypeScript, Tailwind CSS, App Router, `src/` dir, `@/*` import alias.

5. **Given** the `.env.example` file, **When** reviewed, **Then** it contains all required environment variables: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `SENTRY_DSN` (optional), `RESEND_API_KEY` (optional), `STRIPE_SECRET_KEY` (optional).

6. **Given** `backend/Dockerfile` and `backend/Dockerfile.worker`, **When** built, **Then** `Dockerfile` produces a FastAPI + uvicorn image; `Dockerfile.worker` includes `playwright install chromium`.

## Tasks / Subtasks

- [ ] Khởi tạo git repo và cấu trúc monorepo root (AC: 3)
  - [ ] `git init` tại root
  - [ ] Tạo `README.md` cơ bản
  - [ ] Tạo `.gitignore` (Python, Node, Docker)
  - [ ] Tạo thư mục `.github/workflows/` (trống, CI sẽ add ở Story 1.3)
  - [ ] Tạo `.devcontainer/devcontainer.json`

- [ ] Tạo Next.js frontend (AC: 2, 4)
  - [ ] `npx create-next-app@latest frontend --typescript --tailwind --eslint --app --src-dir --import-alias "@/*"`
  - [ ] Verify `package.json` có đúng dependencies
  - [ ] Tạo `frontend/Dockerfile`

- [ ] Tạo FastAPI backend scaffold (AC: 1, 6)
  - [ ] Tạo `backend/` directory structure theo kiến trúc
  - [ ] Tạo `backend/requirements.txt` với dependencies
  - [ ] Tạo `backend/requirements-dev.txt`
  - [ ] Tạo `backend/pyproject.toml` (ruff + mypy config)
  - [ ] Tạo `backend/app/__init__.py` và `backend/app/main.py` cơ bản (FastAPI app factory)
  - [ ] Tạo `backend/Dockerfile` (FastAPI + uvicorn)
  - [ ] Tạo `backend/Dockerfile.worker` (với `playwright install chromium`)

- [ ] Tạo Docker Compose (AC: 1)
  - [ ] Tạo `docker-compose.yml` với 5 services: `api`, `worker`, `frontend`, `db` (PostgreSQL 16), `redis`
  - [ ] Configure health checks cho `db` và `redis`
  - [ ] Configure volumes cho PostgreSQL data persistence
  - [ ] Configure networks

- [ ] Tạo environment config (AC: 5)
  - [ ] Tạo `.env.example` với tất cả required vars: `DATABASE_URL`, `REDIS_URL`, `SECRET_KEY`, `SENTRY_DSN`, `RESEND_API_KEY`, `STRIPE_SECRET_KEY`

- [ ] Tạo Alembic scaffold (chuẩn bị cho Story 1.2)
  - [ ] `alembic init alembic` trong `backend/`
  - [ ] Cấu hình `alembic.ini` và `alembic/env.py`

- [ ] Verify toàn bộ stack chạy được
  - [ ] `docker compose up` không có lỗi
  - [ ] http://localhost:3000 trả về Next.js default page
  - [ ] http://localhost:8000/docs trả về FastAPI Swagger UI

## Dev Notes

### Backend Structure (phải follow CHÍNH XÁC theo architecture.md)

```
backend/app/
├── api/v1/              # Routers ONLY — no business logic in route handlers
├── scraping/
├── auth/
├── billing/
├── notifications/
├── core/
│   ├── config.py        # pydantic-settings Settings class — TẠO NGAY trong story này
│   ├── security.py
│   ├── ssrf_guard.py
│   └── errors.py
└── db/
    ├── session.py
    └── base.py
backend/tests/           # Mirror app/ structure
```

**Tạo đầy đủ thư mục structure** (kể cả `__init__.py` ở mỗi package) để Epic 2+ không bị import errors.

### `backend/app/main.py` — cấu trúc cơ bản

```python
from fastapi import FastAPI
from app.core.config import settings

def create_app() -> FastAPI:
    app = FastAPI(
        title="Resili API",
        version="0.1.0",
        docs_url="/docs",
    )
    return app

app = create_app()

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/api/v1/")
async def root():
    return {"version": "v1", "docs": "/docs"}
```

**QUAN TRỌNG:** Đây là MVP scaffold — `GET /health` và `GET /api/v1/` được implement ngay bây giờ (Story 1.2 sẽ add error schema, Sentry, middleware; không cần làm đầy đủ ở story này).

### `backend/app/core/config.py` — pydantic-settings

```python
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    SENTRY_DSN: str | None = None
    RESEND_API_KEY: str | None = None
    STRIPE_SECRET_KEY: str | None = None
    STRIPE_WEBHOOK_SECRET: str | None = None

    model_config = SettingsConfigDict(env_file=".env")

settings = Settings()
```

**KHÔNG BAO GIỜ** dùng `os.environ.get()` trực tiếp — luôn qua `settings.*`.

### `backend/requirements.txt` — versions đã được validate

```
fastapi[standard]>=0.115
uvicorn[standard]>=0.32
sqlalchemy>=2.0
alembic>=1.14
pydantic-settings>=2.6
psycopg[binary]>=3.2
redis>=5.2
scrapling>=0.4.7
playwright>=1.49
apscheduler>=3.10
sentry-sdk[fastapi]>=2.19
resend>=2.5
stripe>=11.3
bcrypt>=4.2
python-jose[cryptography]>=3.3
```

### `backend/requirements-dev.txt`

```
pytest>=8.3
pytest-asyncio>=0.24
httpx>=0.27
ruff>=0.8
mypy>=1.13
```

### `backend/pyproject.toml` — ruff + mypy config

```toml
[tool.ruff]
line-length = 100
target-version = "py313"
select = ["E", "F", "I", "N", "UP"]

[tool.mypy]
python_version = "3.13"
strict = false
ignore_missing_imports = true
```

### `docker-compose.yml` — services

```yaml
services:
  api:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql+psycopg://resili:resili@db:5432/resili
      - REDIS_URL=redis://redis:6379
    depends_on:
      db:
        condition: service_healthy
      redis:
        condition: service_started
    command: uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

  worker:
    build:
      context: ./backend
      dockerfile: Dockerfile.worker
    environment:
      - DATABASE_URL=postgresql+psycopg://resili:resili@db:5432/resili
    depends_on:
      - db

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "3000:3000"
    command: npm run dev

  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: resili
      POSTGRES_PASSWORD: resili
      POSTGRES_DB: resili
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U resili"]
      interval: 5s
      timeout: 5s
      retries: 5

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"

volumes:
  postgres_data:
```

### `backend/Dockerfile`

```dockerfile
FROM python:3.13-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
COPY . .
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### `backend/Dockerfile.worker`

```dockerfile
FROM python:3.13-slim
WORKDIR /app
RUN apt-get update && apt-get install -y \
    libglib2.0-0 libnss3 libnspr4 libdbus-1-3 \
    libatk1.0-0 libatk-bridge2.0-0 libcups2 \
    libdrm2 libxkbcommon0 libxcomposite1 libxdamage1 \
    libxfixes3 libxrandr2 libgbm1 libasound2 \
    && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt
RUN playwright install chromium
COPY . .
CMD ["python", "-m", "workers.playwright_pool"]
```

### `frontend/Dockerfile`

```dockerfile
FROM node:20-alpine
WORKDIR /app
COPY package*.json .
RUN npm ci
COPY . .
CMD ["npm", "run", "dev"]
```

### `.devcontainer/devcontainer.json`

```json
{
  "name": "Resili Dev Container",
  "dockerComposeFile": "../docker-compose.yml",
  "service": "api",
  "workspaceFolder": "/app",
  "extensions": ["ms-python.python", "charliermarsh.ruff"]
}
```

### Alembic Configuration

`alembic/env.py` phải import `DATABASE_URL` từ `settings`:
```python
from app.core.config import settings
config.set_main_option("sqlalchemy.url", settings.DATABASE_URL)
```

DB models sẽ được import trong Epic 2+. Story này chỉ cần cấu hình Alembic ready.

### Project Structure Notes

- Tạo đầy đủ `__init__.py` ở MỌI package directory: `app/`, `app/api/`, `app/api/v1/`, `app/core/`, `app/db/`, `app/auth/`, `app/scraping/`, `app/billing/`, `app/notifications/`
- `workers/` directory cần `__init__.py` và placeholder `playwright_pool.py`
- **KHÔNG** tạo Alembic migrations ở story này — migrations sẽ được tạo từ Story 2.1 trở đi

### References

- [Source: architecture.md#Selected-Starter-Custom-Monorepo] — init commands
- [Source: architecture.md#Complete-Project-Directory-Structure] — full structure
- [Source: architecture.md#Process-Patterns] — pydantic-settings usage
- [Source: epics.md#Story-1.1] — acceptance criteria
- [Source: architecture.md#Backend-File-Organization] — package structure

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**NEW FILES:**
- `backend/app/__init__.py`
- `backend/app/main.py`
- `backend/app/core/__init__.py`
- `backend/app/core/config.py`
- `backend/app/api/__init__.py`
- `backend/app/api/v1/__init__.py`
- `backend/app/auth/__init__.py`
- `backend/app/scraping/__init__.py`
- `backend/app/billing/__init__.py`
- `backend/app/notifications/__init__.py`
- `backend/app/db/__init__.py`
- `backend/app/db/base.py`
- `backend/app/db/session.py`
- `backend/workers/__init__.py`
- `backend/workers/playwright_pool.py`
- `backend/requirements.txt`
- `backend/requirements-dev.txt`
- `backend/pyproject.toml`
- `backend/Dockerfile`
- `backend/Dockerfile.worker`
- `backend/alembic.ini`
- `backend/alembic/env.py`
- `backend/alembic/versions/` (empty dir)
- `backend/tests/__init__.py`
- `backend/tests/conftest.py`
- `frontend/` (via create-next-app)
- `frontend/Dockerfile`
- `docker-compose.yml`
- `.env.example`
- `README.md`
- `.gitignore`
- `.devcontainer/devcontainer.json`
- `.github/workflows/` (empty dir)
