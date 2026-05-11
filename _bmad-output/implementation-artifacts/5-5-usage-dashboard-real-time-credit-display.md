# Story 5.5: Usage Dashboard & Real-Time Credit Display

Status: ready-for-dev

## Story

As a developer,
I want to see my API usage charts and current credit balance in the dashboard,
so that I can monitor consumption and plan usage accordingly.

## Acceptance Criteria

1. **Given** GET /api/v1/usage with `?period=daily` (or `weekly`/`monthly`) and a valid JWT, **When** called, **Then** HTTP 200 is returned with `{"period": "daily", "items": [{"date": "2026-05-11", "fetcher_credits": 45, "dynamic_credits": 15}], "total_fetcher": N, "total_dynamic": M}`.

2. **Given** `/dashboard/usage`, **When** rendered, **Then** a Recharts chart displays Fetcher credits and Dynamic credits as separate series; a period switcher toggles between daily/weekly/monthly.

3. **Given** the `credit-badge.tsx` component, **When** rendered in the dashboard header, **Then** it displays: current `credits_used`, `monthly_limit`, tier label ("Free"/"Pro"), and a progress bar.

4. **Given** the `useCredits()` hook, **When** the dashboard is open, **Then** TanStack Query refetches credit data every 60 seconds — no manual polling loop.

5. **Given** Recharts chart colors, **When** rendered, **Then** Fetcher series uses `accent-blue` and Dynamic series uses `accent-orange` — no default Recharts colors.

## Tasks / Subtasks

- [ ] Implement `GET /api/v1/usage` backend endpoint (AC: 1)
  - [ ] `app/api/v1/usage.py`: aggregate `usage_events` by period (daily/weekly/monthly)
  - [ ] Group by day/week/month, sum `credits_used` by `endpoint_type`

- [ ] Install and configure Recharts (AC: 2, 5)
  - [ ] `npm install recharts`
  - [ ] `src/components/dashboard/usage-chart.tsx`: LineChart or BarChart

- [ ] Create `credit-badge.tsx` component (AC: 3)
  - [ ] Display: credits_used / monthly_limit, tier, progress bar
  - [ ] Wire into dashboard header/NavBar

- [ ] Create `useCredits()` hook with 60s refetch (AC: 4)
  - [ ] `src/hooks/use-credits.ts`: TanStack Query with `refetchInterval: 60000`

- [ ] Create `useUsage()` hook (AC: 2)
  - [ ] `src/hooks/use-usage.ts`: TanStack Query with period param

- [ ] Complete `/dashboard/usage/page.tsx` (AC: 2)

## Dev Notes

### Backend: `GET /api/v1/usage` Endpoint

```python
# app/api/v1/usage.py
from sqlalchemy import select, func, extract
from app.billing.models import UsageEvent
from datetime import datetime, timedelta, timezone


@router.get("/usage")
async def get_usage(
    period: str = "daily",
    user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Aggregate usage_events for dashboard visualization."""
    now = datetime.now(timezone.utc)

    # Determine lookback window
    if period == "daily":
        since = now - timedelta(days=30)
        group_format = "YYYY-MM-DD"
    elif period == "weekly":
        since = now - timedelta(weeks=12)
        group_format = "IYYY-IW"  # ISO week
    else:  # monthly
        since = now - timedelta(days=365)
        group_format = "YYYY-MM"

    result = await db.execute(
        select(
            func.to_char(UsageEvent.created_at, group_format).label("date"),
            func.sum(
                func.case((UsageEvent.endpoint_type == "fetcher", UsageEvent.credits_used), else_=0)
            ).label("fetcher_credits"),
            func.sum(
                func.case((UsageEvent.endpoint_type == "dynamic", UsageEvent.credits_used), else_=0)
            ).label("dynamic_credits"),
        )
        .where(UsageEvent.user_id == user.id)
        .where(UsageEvent.created_at >= since)
        .where(UsageEvent.status == "success")
        .group_by(func.to_char(UsageEvent.created_at, group_format))
        .order_by(func.to_char(UsageEvent.created_at, group_format))
    )

    items = [
        {"date": row.date, "fetcher_credits": int(row.fetcher_credits or 0),
         "dynamic_credits": int(row.dynamic_credits or 0)}
        for row in result
    ]

    total_fetcher = sum(item["fetcher_credits"] for item in items)
    total_dynamic = sum(item["dynamic_credits"] for item in items)

    return {
        "period": period,
        "items": items,
        "total_fetcher": total_fetcher,
        "total_dynamic": total_dynamic,
    }
```

### `src/hooks/use-usage.ts`

```typescript
import { useQuery } from "@tanstack/react-query";
import { getUsage, type UsagePeriod } from "@/lib/api/endpoints";

export function useUsage(period: UsagePeriod) {
  return useQuery({
    queryKey: ["usage", period],
    queryFn: () => getUsage(period),
  });
}
```

### `src/hooks/use-credits.ts` (AC: 4 — 60s refetch)

```typescript
import { useQuery } from "@tanstack/react-query";
import { getCredits } from "@/lib/api/endpoints";

export function useCredits() {
  return useQuery({
    queryKey: ["credits"],
    queryFn: getCredits,
    refetchInterval: 60 * 1000,  // 60 seconds — no manual polling (AC: 4)
  });
}
```

### `src/components/dashboard/usage-chart.tsx` — Recharts (Dec-J)

```typescript
"use client";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, Legend } from "recharts";
import { useUsage } from "@/hooks/use-usage";
import { useState } from "react";

type Period = "daily" | "weekly" | "monthly";

export function UsageChart() {
  const [period, setPeriod] = useState<Period>("daily");
  const { data, isLoading } = useUsage(period);

  if (isLoading) {
    return <div className="h-64 bg-surface-card rounded-md animate-pulse" />;
  }

  return (
    <div>
      {/* Period switcher */}
      <div className="flex gap-2 mb-4">
        {(["daily", "weekly", "monthly"] as Period[]).map(p => (
          <button
            key={p}
            onClick={() => setPeriod(p)}
            className={`px-3 py-1 rounded-full text-caption capitalize ${
              period === p
                ? "bg-surface-elevated text-ink border border-hairline-strong"
                : "text-charcoal hover:text-ink"
            }`}
          >
            {p}
          </button>
        ))}
      </div>

      {/* Recharts BarChart */}
      <ResponsiveContainer width="100%" height={300}>
        <BarChart data={data?.items ?? []}>
          <XAxis dataKey="date" stroke="#5a6070" tick={{ fontSize: 12 }} />
          <YAxis stroke="#5a6070" tick={{ fontSize: 12 }} />
          <Tooltip
            contentStyle={{ background: "#0a0a0c", border: "1px solid rgba(255,255,255,0.14)" }}
            labelStyle={{ color: "#fcfdff" }}
          />
          <Legend />
          {/* MUST use accent-blue and accent-orange (AC: 5) */}
          <Bar dataKey="fetcher_credits" name="Fetcher" fill="#3b9eff" radius={[2, 2, 0, 0]} />
          <Bar dataKey="dynamic_credits" name="Dynamic" fill="#ff801f" radius={[2, 2, 0, 0]} />
        </BarChart>
      </ResponsiveContainer>
    </div>
  );
}
```

### `src/components/dashboard/credit-badge.tsx` (AC: 3)

```typescript
"use client";
import { useCredits } from "@/hooks/use-credits";
import { Badge } from "@/components/ui/Badge";

export function CreditBadge() {
  const { data } = useCredits();

  if (!data) return null;

  const used = data.credits_used;
  const limit = data.monthly_limit;
  const percentage = Math.min(100, Math.round((used / limit) * 100));
  const tierLabel = data.tier === "pro" ? "Pro" : "Free";

  return (
    <div className="flex items-center gap-3">
      <div>
        <div className="flex items-center gap-2">
          <span className="text-body-sm text-ink">{used.toLocaleString()} / {limit.toLocaleString()}</span>
          <Badge>{tierLabel}</Badge>
        </div>
        {/* Progress bar — no box-shadow! */}
        <div className="w-32 h-1 bg-surface-elevated rounded-full mt-1 overflow-hidden">
          <div
            className={`h-full rounded-full transition-all ${
              percentage >= 80 ? "bg-accent-red" : percentage >= 60 ? "bg-accent-yellow" : "bg-accent-blue"
            }`}
            style={{ width: `${percentage}%` }}
          />
        </div>
      </div>
    </div>
  );
}
```

### Recharts Color Enforcement (AC: 5)

NEVER use default Recharts colors (blue `#8884d8`, green `#82ca9d`). ALWAYS use:
- Fetcher: `#3b9eff` (accent-blue)
- Dynamic: `#ff801f` (accent-orange)

### References

- [Source: architecture.md#Dec-J-Dashboard-Charts] — Recharts
- [Source: architecture.md#Dec-I-Server-State-Management] — TanStack Query
- [Source: epics.md#Story-5.5] — acceptance criteria

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `backend/app/api/v1/usage.py` — implement GET /usage aggregation
- `frontend/src/app/dashboard/usage/page.tsx` — complete implementation

**NEW:**
- `frontend/src/hooks/use-usage.ts`
- `frontend/src/hooks/use-credits.ts`
- `frontend/src/components/dashboard/usage-chart.tsx`
- `frontend/src/components/dashboard/usage-chart.test.tsx`
- `frontend/src/components/dashboard/credit-badge.tsx`
- `frontend/package.json` — add recharts
