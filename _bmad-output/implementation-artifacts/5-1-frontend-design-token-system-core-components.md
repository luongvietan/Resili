# Story 5.1: Frontend Design Token System & Core Components

Status: ready-for-dev

## Story

As a frontend developer,
I want the DESIGN.md token system implemented as Tailwind config and CSS variables,
so that all UI components have a consistent dark-canvas visual identity from the start.

## Acceptance Criteria

1. **Given** `tailwind.config.ts`, **When** reviewed, **Then** it extends the default palette with all DESIGN.md color tokens: `canvas`, `surface-card`, `surface-elevated`, `surface-deep`, `hairline`, `hairline-strong`, `ink`, `body`, `charcoal`, `mute`, `ash`, and 5 accent colors with `-glow` variants.

2. **Given** the entire frontend codebase, **When** searched for `box-shadow`, `drop-shadow`, or `shadow-` Tailwind utilities, **Then** none are found — elevation via surface color + hairline only.

3. **Given** the `Button` component variants, **When** rendered, **Then**: `button-primary` = `bg-ink text-canvas h-9 rounded-md`; `button-ghost` = `bg-surface-elevated border border-hairline-strong h-9 rounded-md`; `button-outline` = `bg-canvas border border-hairline-strong h-9 rounded-md`.

4. **Given** `tailwind.config.ts` breakpoints, **When** reviewed, **Then** the 6 DESIGN.md breakpoints are configured: mobile (425px), tablet (768px), tablet-lg (1024px), desktop (1280px), desktop-xl (1440px).

5. **Given** Inter and Geist Mono fonts, **When** configured via `next/font`, **Then** `fontFamily.sans` is Inter and `fontFamily.mono` is Geist Mono.

6. **Given** the DESIGN.md proprietary font requirements, **When** implementing, **Then** the developer makes an explicit decision documented in a code comment — either licensed fonts OR fallback with comment.

## Tasks / Subtasks

- [ ] Complete `tailwind.config.ts` with full token system (AC: 1, 4, 5, 6)
  - [ ] All color tokens (canvas, surfaces, hairlines, ink scale, 5 accents with glow)
  - [ ] 6 custom breakpoints per UX-DR12
  - [ ] Font family configuration
  - [ ] Typography scale (display-xxl through caption)
  - [ ] Add comment for proprietary font decision

- [ ] Create `Button` component (AC: 3)
  - [ ] `src/components/ui/Button.tsx`: 3 variants (primary, ghost, outline)
  - [ ] Mobile height 44px (mobile:h-11)
  - [ ] NO box-shadow anywhere

- [ ] Verify no shadow usage (AC: 2)
  - [ ] Search codebase for shadow-*, drop-shadow, box-shadow
  - [ ] Fix any violations

- [ ] Setup font loading (AC: 5)
  - [ ] `src/app/layout.tsx`: Inter + Geist Mono via next/font/google
  - [ ] Apply CSS variables for Tailwind

- [ ] Create additional core UI components
  - [ ] `CodeWindow` component (UX-DR7)
  - [ ] `Badge` component (UX-DR10)
  - [ ] `Input` component (UX-DR11)

## Dev Notes

### Previous Work from Story 1.4

Story 1.4 đã implement `tailwind.config.ts` và `Button` component. Story này là Epic 5 — verify/complete the full token system. Nhiều khả năng cần:
1. Verify Story 1.4 đã implement đầy đủ
2. Add dashboard-specific components (Input, Badge)
3. Ensure no shadow violations

### `tailwind.config.ts` — Complete Reference

(Đã có từ Story 1.4 Dev Notes — verify và complete nếu thiếu tokens)

**Critical check:** `hairline` color trong Tailwind config phải là:
```typescript
hairline: "rgba(255,255,255,0.06)",
"hairline-strong": "rgba(255,255,255,0.14)",
```

Không phải hex strings — phải là rgba.

### `Input` Component (UX-DR11)

```typescript
// src/components/ui/Input.tsx
export function Input({ className, ...props }: React.InputHTMLAttributes<HTMLInputElement>) {
  return (
    <input
      className={cn(
        "bg-surface-card border border-hairline-strong rounded-md",
        "px-3.5 py-2.5 h-10 text-ink text-body-sm",
        "placeholder:text-charcoal",
        "focus:outline-none focus:border-ink",  // Focus: border thickens to ink (UX-DR11)
        // NO separate focus ring color (UX-DR11 constraint)
        "mobile:h-12",  // Mobile: 48px height
        className
      )}
      {...props}
    />
  );
}
```

### `Badge` Component (UX-DR10)

```typescript
// src/components/ui/Badge.tsx
export function Badge({ children, className }: { children: React.ReactNode; className?: string }) {
  return (
    <span className={cn(
      "bg-surface-elevated rounded-full px-2.5 py-1",
      "text-caption text-body",
      className
    )}>
      {children}
    </span>
  );
}
```

### NO SHADOW Rule (UX-DR13) — ESLint Rule

Add ESLint rule to enforce:
```json
// .eslintrc.json or eslint.config.js
{
  "rules": {
    "no-restricted-syntax": [
      "error",
      {
        "selector": "Literal[value=/shadow/]",
        "message": "No shadows allowed per UX-DR13. Use surface color shifts and hairline borders."
      }
    ]
  }
}
```

Or add to `package.json` scripts:
```bash
"check:no-shadows": "grep -r 'shadow-\\|box-shadow\\|drop-shadow' src/ && exit 1 || exit 0"
```

### TanStack Query Setup (Dec-I)

Dashboard components sẽ cần TanStack Query. Setup trong `src/app/layout.tsx`:
```typescript
"use client";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";

const queryClient = new QueryClient({
  defaultOptions: {
    queries: { staleTime: 60 * 1000 }, // 1 min stale time
  },
});

export default function RootLayout({ children }) {
  return (
    <html>
      <body>
        <QueryClientProvider client={queryClient}>
          {children}
        </QueryClientProvider>
      </body>
    </html>
  );
}
```

Install: `npm install @tanstack/react-query`

### References

- [Source: epics.md#UX-DR1-UX-DR13] — full design token requirements
- [Source: epics.md#Story-5.1] — acceptance criteria
- [Source: architecture.md#Dec-I-Server-State-Management] — TanStack Query v5

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `frontend/tailwind.config.ts` — verify/complete full token system
- `frontend/src/app/layout.tsx` — add QueryClientProvider + font CSS vars

**NEW or UPDATE:**
- `frontend/src/components/ui/Button.tsx` — verify from Story 1.4
- `frontend/src/components/ui/Input.tsx`
- `frontend/src/components/ui/Badge.tsx`
- `frontend/src/components/ui/CodeWindow.tsx` — verify from Story 1.4
