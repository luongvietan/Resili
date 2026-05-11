# Resili

> Web scraping API for AI agents — built on [Scrapling](https://github.com/D4Vinci/Scrapling) (BSD License)

Resili provides a simple REST API and MCP server that lets developers and AI agents scrape web content without managing scraping infrastructure.

## Services

| Service    | Description                     | Port |
|------------|---------------------------------|------|
| `api`      | FastAPI backend                 | 8000 |
| `worker`   | Playwright worker               | —    |
| `frontend` | Next.js dashboard               | 3000 |
| `db`       | PostgreSQL 16                   | 5432 |
| `redis`    | Redis                           | 6379 |

## Quick Start

```bash
# 1. Clone the repo
git clone <repo-url>
cd resili

# 2. Setup environment
cp .env.example .env
# Edit .env with your values

# 3. Start all services
docker compose up
```

## API Endpoints

- `GET /health` — liveness probe
- `GET /api/v1/` — version info
- `POST /api/v1/scrape/fetch` — static page fetcher (1 credit)
- `POST /api/v1/scrape/dynamic` — JS-rendered fetcher (5 credits, Pro only)

## MCP Integration

Add to your MCP client config:

```json
{
  "resili": {
    "command": "python",
    "args": ["path/to/backend/mcp_server.py"],
    "env": { "RESILI_API_KEY": "rsl_..." }
  }
}
```

## Attribution

Built on [Scrapling](https://github.com/D4Vinci/Scrapling) — BSD License. See [LICENSE-SCRAPLING](./LICENSE-SCRAPLING).
