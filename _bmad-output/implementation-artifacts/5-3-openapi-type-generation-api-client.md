# Story 5.3: OpenAPI Type Generation & API Client

Status: ready-for-dev

## Story

As a frontend developer,
I want auto-generated TypeScript types from the FastAPI OpenAPI spec,
so that all API calls are type-safe without manual type maintenance.

## Acceptance Criteria

1. **Given** `npx openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/types.ts` run with the backend live, **When** executed, **Then** `types.ts` is generated without errors and contains typed interfaces for all request/response schemas.

2. **Given** `src/lib/api/client.ts`, **When** reviewed, **Then** it: attaches `Authorization: Bearer {api_key}` header; parses Dec-D `error` object; throws typed `ApiError` on non-2xx.

3. **Given** `src/lib/api/endpoints.ts`, **When** reviewed, **Then** it exports typed wrapper functions: `getKeys()`, `createKey()`, `revokeKey()`, `regenerateKey()`, `getUsage(period)`, `getCredits()`.

4. **Given** passing incorrect field type to an endpoint wrapper, **When** TypeScript compiles, **Then** it fails with type error.

## Tasks / Subtasks

- [ ] Setup openapi-typescript generation (AC: 1)
  - [ ] `package.json` script: `"gen:types": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/types.ts"`
  - [ ] Generate initial `types.ts` (commit to repo)

- [ ] Implement type-safe `client.ts` (AC: 2)
  - [ ] `src/lib/api/client.ts`: fetch wrapper with auth header + Dec-D error parsing
  - [ ] `ApiError` class with typed Dec-D error structure

- [ ] Implement `endpoints.ts` with typed wrappers (AC: 3, 4)
  - [ ] `getKeys()`, `createKey()`, `revokeKey()`, `regenerateKey()`
  - [ ] `getUsage(period)`, `getCredits()`
  - [ ] All using types from `types.ts`

## Dev Notes

### `package.json` scripts

```json
{
  "scripts": {
    "gen:types": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/types.ts",
    "dev": "next dev --turbopack",
    "build": "next build",
    "test": "jest"
  },
  "devDependencies": {
    "openapi-typescript": "^7.0"
  }
}
```

Run: `npm run gen:types` with FastAPI backend running.

### `src/lib/api/client.ts` — Complete Implementation

```typescript
import { getToken } from "@/lib/auth";

const API_BASE = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

// Dec-D error structure
export interface ApiErrorData {
  code: string;
  message: string;
  hint: string;
  docs_url: string;
}

export class ApiError extends Error {
  constructor(
    public status: number,
    public error: ApiErrorData
  ) {
    super(error.message);
    this.name = "ApiError";
  }
}

export async function apiRequest<T>(
  path: string,
  options: RequestInit = {}
): Promise<T> {
  const token = getToken();

  const response = await fetch(`${API_BASE}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });

  if (!response.ok) {
    const body = await response.json().catch(() => ({}));
    const errorData: ApiErrorData = body.error ?? {
      code: "UNKNOWN_ERROR",
      message: "An unknown error occurred",
      hint: "Please try again",
      docs_url: "https://docs.resili.io/errors",
    };
    throw new ApiError(response.status, errorData);
  }

  return response.json() as Promise<T>;
}
```

### `src/lib/api/endpoints.ts` — Typed Wrappers

```typescript
import { apiRequest } from "./client";
// Import from generated types.ts
import type { components } from "./types";

// Type aliases from generated spec
type ApiKeyListResponse = components["schemas"]["ApiKeyListResponse"];
type ApiKeyCreateResponse = components["schemas"]["ApiKeyCreateResponse"];
type CreditBalanceResponse = components["schemas"]["CreditBalanceResponse"];
type UsageResponse = components["schemas"]["UsageResponse"];

export type UsagePeriod = "daily" | "weekly" | "monthly";

// API Key endpoints
export function getKeys(): Promise<ApiKeyListResponse> {
  return apiRequest<ApiKeyListResponse>("/api/v1/keys");
}

export function createKey(name?: string): Promise<ApiKeyCreateResponse> {
  return apiRequest<ApiKeyCreateResponse>("/api/v1/keys", {
    method: "POST",
    body: JSON.stringify({ name }),
  });
}

export function revokeKey(keyId: string): Promise<void> {
  return apiRequest<void>(`/api/v1/keys/${keyId}`, { method: "DELETE" });
}

export function regenerateKey(keyId: string): Promise<ApiKeyCreateResponse> {
  return apiRequest<ApiKeyCreateResponse>(`/api/v1/keys/${keyId}/regenerate`, {
    method: "POST",
  });
}

// Usage endpoints
export function getUsage(period: UsagePeriod): Promise<UsageResponse> {
  return apiRequest<UsageResponse>(`/api/v1/usage?period=${period}`);
}

export function getCredits(): Promise<CreditBalanceResponse> {
  return apiRequest<CreditBalanceResponse>("/api/v1/credits");
}
```

### FastAPI Must Expose Credits Endpoint

`GET /api/v1/credits` — Story 5.3 needs this endpoint. Add to backend:
```python
# app/api/v1/usage.py
from app.billing.schemas import CreditBalanceResponse

@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credits(
    user: User = Depends(get_current_user),  # JWT auth (dashboard)
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(select(CreditBalance).where(CreditBalance.user_id == user.id))
    balance = result.scalar_one_or_none()
    return balance
```

Also add `GET /api/v1/usage` endpoint:
```python
@router.get("/usage")
async def get_usage(
    period: str = "daily",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    # Aggregate usage_events by period
    ...
```

### Type Safety Verification (AC: 4)

```typescript
// This should cause TypeScript compile error:
import { getKeys } from "@/lib/api/endpoints";

// Correct:
const keys = await getKeys(); // Type: ApiKeyListResponse
const item = keys.items[0];   // Type: ApiKeyListItem
const id: string = item.id;   // ✅ UUID as string

// TypeScript error:
const wrongId: number = item.id;  // ❌ Type error: string not assignable to number
```

### Handling types.ts not yet generated

For CI/CD where backend isn't running:
1. Commit a generated `types.ts` to the repo
2. Or create a minimal `types.ts` stub for types that are known
3. The `gen:types` script regenerates from live backend

### References

- [Source: architecture.md#Dec-K-API-Client] — openapi-typescript strategy
- [Source: epics.md#Story-5.3] — acceptance criteria
- [Source: architecture.md#Naming-Patterns] — snake_case JSON fields

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `frontend/package.json` — add gen:types script, openapi-typescript devDep
- `backend/app/api/v1/usage.py` — add GET /usage and GET /credits endpoints

**NEW:**
- `frontend/src/lib/api/client.ts` (full implementation)
- `frontend/src/lib/api/endpoints.ts`
- `frontend/src/lib/api/types.ts` (generated — commit stub)
