# Story 5.2: Dashboard Shell, Auth Pages & Navigation

Status: ready-for-dev

## Story

As a developer,
I want to log in and access a structured dashboard with navigation,
so that I can manage my API keys and usage from a clean, branded interface.

## Acceptance Criteria

1. **Given** a logged-out user visiting `/dashboard`, **When** redirected, **Then** they are sent to `/login`.

2. **Given** the `/login` page, **When** rendered, **Then** it displays: email + password `text-input` fields (bg `surface-card`, height 40px, focus border `ink`), a `button-primary` "Sign in" CTA, on a `canvas` (#000) background.

3. **Given** a successful login, **When** redirected to `/dashboard`, **Then** the dashboard layout renders with: `nav-bar` (height 64px, `hairline` bottom border, logo left, user menu right), sidebar with "API Keys" and "Usage" links, and main content area.

4. **Given** `/dashboard/page.tsx`, **When** rendered, **Then** it shows a Quick Start guide with a `code-window` displaying a real `curl` example pre-filled with the user's API key.

5. **Given** the `nav-bar` at viewport < 1024px, **When** rendered, **Then** center navigation links collapse to a hamburger icon; logo and `button-primary` remain visible.

## Tasks / Subtasks

- [ ] Implement auth state management (AC: 1)
  - [ ] `src/lib/auth.ts`: store JWT in httpOnly cookie or localStorage
  - [ ] Auth middleware/redirect logic for protected routes

- [ ] Create auth route group with pages (AC: 1, 2)
  - [ ] `src/app/(auth)/login/page.tsx`: login form
  - [ ] `src/app/(auth)/register/page.tsx`: registration form
  - [ ] Route group layout with canvas background

- [ ] Implement login form (AC: 2)
  - [ ] Form with email `Input` + password `Input` components
  - [ ] Submit → POST /api/v1/auth/login → store token → redirect to /dashboard

- [ ] Create dashboard shell layout (AC: 3)
  - [ ] `src/app/dashboard/layout.tsx`: sidebar + header shell
  - [ ] Auth protection: redirect to /login if no token
  - [ ] Sidebar: "API Keys" and "Usage" links

- [ ] Create NavBar component (AC: 3, 5)
  - [ ] `src/components/layout/NavBar.tsx`: 64px height, hairline bottom
  - [ ] Hamburger at < 1024px, logo + CTA always visible

- [ ] Create dashboard overview page (AC: 4)
  - [ ] `src/app/dashboard/page.tsx`: Quick Start with CodeWindow

- [ ] Create empty placeholder pages
  - [ ] `src/app/dashboard/keys/page.tsx` (Story 5.4)
  - [ ] `src/app/dashboard/usage/page.tsx` (Story 5.5)

## Dev Notes

### Auth Token Storage

Next.js App Router best practice: store JWT in `httpOnly` cookie (secure, no XSS). BUT frontend can't read httpOnly cookies for conditional rendering.

**Pragmatic approach for MVP:**
- Store JWT in `localStorage` (simpler, sufficient for developer tool)
- Note: production hardening would use httpOnly cookie + refresh token

```typescript
// src/lib/auth.ts
export const AUTH_TOKEN_KEY = "resili_access_token";

export function getToken(): string | null {
  if (typeof window === "undefined") return null;
  return localStorage.getItem(AUTH_TOKEN_KEY);
}

export function setToken(token: string): void {
  localStorage.setItem(AUTH_TOKEN_KEY, token);
}

export function clearToken(): void {
  localStorage.removeItem(AUTH_TOKEN_KEY);
}

export function isAuthenticated(): boolean {
  return !!getToken();
}
```

### Dashboard Layout with Auth Protection (AC: 1, 3)

```typescript
// src/app/dashboard/layout.tsx
"use client";
import { useEffect } from "react";
import { useRouter } from "next/navigation";
import { getToken } from "@/lib/auth";

export default function DashboardLayout({ children }: { children: React.ReactNode }) {
  const router = useRouter();

  useEffect(() => {
    if (!getToken()) {
      router.replace("/login");  // AC: 1 — redirect to /login
    }
  }, [router]);

  return (
    <div className="min-h-screen bg-canvas flex">
      {/* Sidebar */}
      <aside className="w-56 border-r border-hairline flex flex-col py-6">
        <nav className="flex flex-col gap-1 px-3">
          <SidebarLink href="/dashboard/keys" label="API Keys" />
          <SidebarLink href="/dashboard/usage" label="Usage" />
        </nav>
      </aside>

      {/* Main content */}
      <main className="flex-1 flex flex-col">
        <NavBar />
        <div className="p-8">{children}</div>
      </main>
    </div>
  );
}
```

### Login Page (AC: 2)

```typescript
// src/app/(auth)/login/page.tsx
"use client";
import { useState } from "react";
import { useRouter } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { Input } from "@/components/ui/Input";
import { setToken } from "@/lib/auth";

export default function LoginPage() {
  const router = useRouter();
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState("");

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    const res = await fetch("/api/v1/auth/login", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ email, password }),
    });

    if (res.ok) {
      const data = await res.json();
      setToken(data.access_token);
      router.push("/dashboard");
    } else {
      const err = await res.json();
      setError(err.error?.message || "Login failed");
    }
  }

  return (
    <div className="min-h-screen bg-canvas flex items-center justify-center">
      <div className="w-full max-w-sm bg-surface-card border border-hairline-strong rounded-lg p-8">
        <h1 className="text-display-xs text-ink font-display mb-6">Sign in to Resili</h1>
        <form onSubmit={handleSubmit} className="flex flex-col gap-4">
          <Input
            type="email"
            placeholder="Email address"
            value={email}
            onChange={e => setEmail(e.target.value)}
            required
          />
          <Input
            type="password"
            placeholder="Password"
            value={password}
            onChange={e => setPassword(e.target.value)}
            required
          />
          {error && <p className="text-accent-red text-body-sm">{error}</p>}
          <Button type="submit" variant="primary" className="w-full">
            Sign in
          </Button>
        </form>
        <p className="text-body-sm text-charcoal mt-4 text-center">
          Don't have an account?{" "}
          <a href="/register" className="text-accent-blue hover:underline">Sign up</a>
        </p>
      </div>
    </div>
  );
}
```

### NavBar Component (AC: 3, 5)

```typescript
// src/components/layout/NavBar.tsx
"use client";
import { useState } from "react";
import { Button } from "@/components/ui/Button";

export function NavBar() {
  const [menuOpen, setMenuOpen] = useState(false);

  return (
    <header className="h-16 border-b border-hairline flex items-center px-6 gap-4 bg-canvas">
      {/* Logo — always visible */}
      <a href="/" className="text-ink font-display font-medium text-body-lg">Resili</a>

      {/* Desktop nav — hidden on tablet-lg and below */}
      <nav className="hidden tablet-lg:flex gap-6 flex-1 justify-center">
        <a href="/dashboard" className="text-body-sm text-charcoal hover:text-ink transition-colors">Overview</a>
        <a href="/dashboard/keys" className="text-body-sm text-charcoal hover:text-ink transition-colors">API Keys</a>
        <a href="/dashboard/usage" className="text-body-sm text-charcoal hover:text-ink transition-colors">Usage</a>
      </nav>

      {/* Actions */}
      <div className="ml-auto flex items-center gap-3">
        <Button variant="ghost" className="hidden tablet-lg:block text-body-sm h-8">Docs</Button>
        {/* Hamburger — visible below tablet-lg */}
        <button
          className="tablet-lg:hidden p-2 text-charcoal hover:text-ink"
          onClick={() => setMenuOpen(!menuOpen)}
          aria-label="Toggle menu"
        >
          {/* Simple hamburger icon */}
          <div className="w-5 h-0.5 bg-current mb-1.5" />
          <div className="w-5 h-0.5 bg-current mb-1.5" />
          <div className="w-5 h-0.5 bg-current" />
        </button>
      </div>
    </header>
  );
}
```

### Quick Start CodeWindow (AC: 4)

```typescript
// src/app/dashboard/page.tsx
"use client";
import { CodeWindow } from "@/components/ui/CodeWindow";
import { useApiKeys } from "@/hooks/use-api-keys";

export default function DashboardPage() {
  const { data } = useApiKeys();
  const firstKey = data?.items?.[0];

  const curlExample = firstKey
    ? `curl -X POST https://api.resili.io/api/v1/scrape/fetch \\
  -H "Authorization: Bearer ${firstKey.masked_key || "rsl_your_key_here"}" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "format": "markdown"}'`
    : `curl -X POST https://api.resili.io/api/v1/scrape/fetch \\
  -H "Authorization: Bearer rsl_your_key_here" \\
  -H "Content-Type: application/json" \\
  -d '{"url": "https://example.com", "format": "markdown"}'`;

  return (
    <div className="max-w-3xl">
      <h1 className="text-display-sm text-ink font-display mb-2">Quick Start</h1>
      <p className="text-body text-body-md mb-6">Make your first API call:</p>
      <CodeWindow code={curlExample} tabs={["curl", "Python"]} />
    </div>
  );
}
```

### API Client for Login

Next.js frontend calls FastAPI backend. In development (Docker Compose):
- Frontend: `http://localhost:3000`
- API: `http://localhost:8000`

Configure `NEXT_PUBLIC_API_URL=http://localhost:8000` in `.env.local`.

```typescript
// src/lib/api/client.ts
const API_URL = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";

export async function apiRequest(path: string, options: RequestInit = {}) {
  const token = getToken();
  return fetch(`${API_URL}${path}`, {
    ...options,
    headers: {
      "Content-Type": "application/json",
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
      ...options.headers,
    },
  });
}
```

### References

- [Source: epics.md#Story-5.2] — acceptance criteria
- [Source: epics.md#UX-DR8] — NavBar component specs
- [Source: epics.md#UX-DR11] — text-input focus: border ink, no separate ring
- [Source: architecture.md#Dec-I] — TanStack Query

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**NEW:**
- `frontend/src/app/(auth)/login/page.tsx`
- `frontend/src/app/(auth)/register/page.tsx`
- `frontend/src/app/dashboard/layout.tsx`
- `frontend/src/app/dashboard/page.tsx`
- `frontend/src/app/dashboard/keys/page.tsx` (placeholder)
- `frontend/src/app/dashboard/usage/page.tsx` (placeholder)
- `frontend/src/components/layout/NavBar.tsx`
- `frontend/src/components/layout/SidebarLink.tsx`
- `frontend/src/lib/auth.ts`
- `frontend/src/lib/api/client.ts`
- `frontend/src/hooks/use-api-keys.ts` (placeholder)

**UPDATE:**
- `frontend/src/app/layout.tsx` — ensure QueryClientProvider
- `frontend/.env.local.example` — add NEXT_PUBLIC_API_URL
