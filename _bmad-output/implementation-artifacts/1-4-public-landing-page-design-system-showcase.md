# Story 1.4: Public Landing Page & Design System Showcase

Status: ready-for-dev

## Story

As a prospective Resili user,
I want a compelling public landing page that showcases Resili's value proposition,
so that I understand what Resili does and can start using it immediately.

## Acceptance Criteria

1. **Given** a logged-out user visiting `/`, **When** the page loads, **Then** the public landing page renders (no redirect) with: `hero-stripe` section (Domaine Display or configured fallback, `display-xxl` headline, `button-primary` "Get started", `button-ghost` "View docs"), and at least two feature sections below.

2. **Given** the `hero-stripe` section, **When** rendered, **Then** the headline communicates Resili's scraping value proposition (e.g. "Web data for AI agents") — NOT email-related copy.

3. **Given** the DESIGN.md component system, **When** applied, **Then** `email-mockup` component is NOT used — replaced with `code-window` demonstrating actual Fetcher API output.

4. **Given** the hero headline, **When** rendered, **Then** it uses `display-xxl` (96px) with `lineHeight: 1.0` and negative letter-spacing; clamps to 44px on mobile ≤ 425px.

5. **Given** at least one section below the hero, **When** rendered, **Then** an atmospheric glow (CSS radial gradient using one `accent-*-glow` token) is anchored at top, fades ~600px; no two adjacent sections share same glow color.

6. **Given** the pricing section, **When** rendered, **Then** 3 tier cards use `pricing-tier` component; Pro tier uses `pricing-tier-featured` (bg `surface-elevated`) — elevation from luminance only, no drop shadow.

7. **Given** at least one `code-window` component, **When** rendered, **Then** it uses bg `surface-deep`, Geist Mono, traffic-light dots (solid red/yellow/green), code tabs, real curl/Python Fetcher API example.

8. **Given** landing page on mobile (≤ 425px), **When** rendered, **Then** feature grid is 1-up, hero font clamps to 44px, nav collapses to hamburger, section padding reduces to 64px.

## Tasks / Subtasks

- [ ] Setup Tailwind design token system (AC: 4, 5, 6, 8)
  - [ ] Extend `tailwind.config.ts` với DESIGN.md color tokens
  - [ ] Configure 6 custom breakpoints
  - [ ] Configure font families (Inter, Geist Mono + fallbacks cho proprietary fonts)
  - [ ] Verify không có `box-shadow`, `drop-shadow` utilities

- [ ] Tạo core UI components
  - [ ] `Button` component (3 variants: primary, ghost, outline) theo UX-DR5
  - [ ] `NavBar` component (desktop + mobile hamburger) theo UX-DR8
  - [ ] `CodeWindow` component (traffic-light dots, tabs, Geist Mono) theo UX-DR7
  - [ ] Pricing tier card components (`PricingTier`, `PricingTierFeatured`) theo UX-DR6

- [ ] Implement landing page sections (AC: 1, 2, 3)
  - [ ] Hero section (`hero-stripe`) với scraping value prop headline
  - [ ] Feature section 1 (e.g. "How it works" với `code-window`)
  - [ ] Feature section 2 (e.g. "Built for AI Agents")
  - [ ] Pricing section (3 tiers: Free, Pro, Enterprise)
  - [ ] Footer theo UX-DR10

- [ ] Implement atmospheric glows (AC: 5)
  - [ ] CSS radial gradient glow cho mỗi section
  - [ ] Đảm bảo không có 2 adjacent sections dùng cùng glow color

- [ ] Responsive layout (AC: 8)
  - [ ] Mobile ≤425px: 1-up grid, 44px hero, hamburger nav, 64px section padding
  - [ ] Tablet 768px: 2-up feature grid
  - [ ] Desktop 1280px+: full layout

## Dev Notes

### `tailwind.config.ts` — COMPLETE Design Token System

```typescript
import type { Config } from "tailwindcss";

const config: Config = {
  content: ["./src/**/*.{ts,tsx}"],
  theme: {
    extend: {
      colors: {
        // Canvas & surfaces (UX-DR1)
        canvas: "#000000",
        "surface-card": "#0a0a0c",
        "surface-elevated": "#101012",
        "surface-deep": "#06060a",
        // Hairlines
        hairline: "rgba(255,255,255,0.06)",
        "hairline-strong": "rgba(255,255,255,0.14)",
        "divider-soft": "rgba(255,255,255,0.08)",
        // Ink scale
        ink: "#fcfdff",
        body: "#c8cdd8",
        charcoal: "#8b919e",
        mute: "#5a6070",
        ash: "#3a3f4a",
        stone: "#1e2028",
        // Accent colors with glow (UX-DR3)
        "accent-orange": "#ff801f",
        "accent-orange-glow": "rgba(255,89,0,0.22)",
        "accent-yellow": "#ffc53d",
        "accent-blue": "#3b9eff",
        "accent-blue-glow": "rgba(0,117,255,0.34)",
        "accent-green": "#11ff99",
        "accent-green-glow": "rgba(34,255,153,0.18)",
        "accent-red": "#ff2047",
        "accent-red-glow": "rgba(255,32,71,0.34)",
      },
      fontFamily: {
        // UX-DR2: Proprietary fonts — use licensed or fallback
        // DEVELOPER DECISION: Fallback mode (no license) — replace when licensed fonts available
        serif: ["'Tiempos Headline'", "Georgia", "serif"], // Fallback for Domaine Display
        display: ["'Inter Tight'", "Inter", "sans-serif"], // Fallback for ABC Favorit
        sans: ["Inter", "system-ui", "sans-serif"], // UI labels
        mono: ["'Geist Mono'", "monospace"], // Code
      },
      fontSize: {
        // UX-DR4: Typography scale
        "display-xxl": ["96px", { lineHeight: "1.0", letterSpacing: "-0.96px" }],
        "display-xl": ["72px", { lineHeight: "1.0", letterSpacing: "-0.72px" }],
        "display-lg": ["56px", { lineHeight: "1.0", letterSpacing: "-0.56px" }],
        "display-md": ["48px", { lineHeight: "1.05", letterSpacing: "-0.48px" }],
        "display-sm": ["40px", { lineHeight: "1.1", letterSpacing: "-0.4px" }],
        "display-xs": ["32px", { lineHeight: "1.15", letterSpacing: "-0.32px" }],
        "body-xl": ["20px", { lineHeight: "1.6", letterSpacing: "0" }],
        "body-lg": ["18px", { lineHeight: "1.6", letterSpacing: "0" }],
        "body-md": ["16px", { lineHeight: "1.6", letterSpacing: "0" }],
        "body-sm": ["14px", { lineHeight: "1.5", letterSpacing: "0" }],
        "body-xs": ["13px", { lineHeight: "1.5", letterSpacing: "0" }],
        caption: ["12px", { lineHeight: "1.4", letterSpacing: "0.02em" }],
        "code-md": ["13px", { lineHeight: "1.6", letterSpacing: "0" }],
      },
      screens: {
        // UX-DR12: 6 breakpoints
        mobile: "425px",
        tablet: "768px",
        "tablet-lg": "1024px",
        desktop: "1280px",
        "desktop-xl": "1440px",
      },
      maxWidth: {
        body: "1200px",
      },
    },
  },
  plugins: [],
};

export default config;
```

### Button Component (UX-DR5) — `src/components/ui/Button.tsx`

```typescript
import { ButtonHTMLAttributes, forwardRef } from "react";
import { cn } from "@/lib/utils";

type ButtonVariant = "primary" | "ghost" | "outline";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
}

const variantClasses: Record<ButtonVariant, string> = {
  // button-primary: bright pixel on canvas — bg #fcfdff, text black
  primary: "bg-ink text-canvas h-9 px-4 rounded-md font-sans text-body-sm font-medium " +
           "hover:bg-[#f1f7fe] active:bg-[#f1f7fe] transition-colors " +
           "mobile:h-11", // Mobile: 44px
  // button-ghost: surface-elevated, hairline-strong border
  ghost: "bg-surface-elevated text-ink border border-hairline-strong h-9 px-4 rounded-md font-sans text-body-sm " +
         "hover:bg-surface-card transition-colors mobile:h-11",
  // button-outline: canvas bg, hairline-strong border
  outline: "bg-canvas text-ink border border-hairline-strong h-9 px-4 rounded-md font-sans text-body-sm " +
           "hover:bg-surface-card transition-colors mobile:h-11",
};

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", className, ...props }, ref) => {
    return (
      <button
        ref={ref}
        className={cn(variantClasses[variant], className)}
        {...props}
      />
    );
  }
);
Button.displayName = "Button";
```

### CodeWindow Component (UX-DR7) — `src/components/ui/CodeWindow.tsx`

```typescript
interface CodeWindowProps {
  tabs?: string[];
  activeTab?: number;
  code: string;
  language?: string;
}

export function CodeWindow({ tabs = ["curl"], activeTab = 0, code, language = "bash" }: CodeWindowProps) {
  return (
    <div className="bg-surface-deep border border-hairline-strong rounded-lg p-6 font-mono">
      {/* Traffic-light dots */}
      <div className="flex gap-2 mb-4">
        <div className="w-3 h-3 rounded-full bg-accent-red" />
        <div className="w-3 h-3 rounded-full bg-accent-yellow" />
        <div className="w-3 h-3 rounded-full bg-accent-green" />
      </div>
      {/* Tab strip */}
      {tabs.length > 1 && (
        <div className="flex gap-1 mb-4 border-b border-hairline">
          {tabs.map((tab, i) => (
            <button
              key={tab}
              className={cn(
                "px-3 py-1 text-caption rounded-sm",
                i === activeTab
                  ? "bg-surface-card text-ink border-b-2 border-hairline-strong"
                  : "text-charcoal"
              )}
            >
              {tab}
            </button>
          ))}
        </div>
      )}
      {/* Code content */}
      <pre className="text-code-md text-body overflow-x-auto">
        <code>{code}</code>
      </pre>
    </div>
  );
}
```

### Hero Section — Atmospheric Glow (UX-DR9)

```typescript
// Glow phải là CSS radial-gradient, anchored at top, fade ~600px
// KHÔNG BAOGIỜ dùng solid color

const heroStyle = {
  background: "radial-gradient(ellipse 80% 600px at 50% -100px, var(--accent-blue-glow), transparent)",
};

// Mỗi section dùng 1 màu glow khác nhau:
// Hero → accent-blue-glow
// Feature 1 → accent-orange-glow  
// Feature 2 → accent-green-glow
// Pricing → accent-orange-glow (đủ xa để không adjacent với Feature 2)
```

### Hero Responsive Typography (UX-DR4, UX-DR12)

```css
/* Dùng clamp() cho display-xxl responsive */
.hero-headline {
  font-size: clamp(44px, 6vw, 96px); /* 44px mobile → 96px desktop */
  line-height: 1.0;
  letter-spacing: -0.96px;
}
```

Hoặc trong Tailwind:
```typescript
// Sử dụng responsive prefix
<h1 className="text-[44px] tablet:text-[56px] desktop:text-display-xxl leading-none tracking-[-0.96px]">
```

### NO DROP SHADOW POLICY (UX-DR13) — CRITICAL

**Tuyệt đối KHÔNG** dùng bất kỳ dạng shadow nào:
- ❌ `box-shadow: ...`
- ❌ `drop-shadow(...)`
- ❌ Tailwind: `shadow-*`, `drop-shadow-*`

Elevation ONLY qua:
- Surface color shift: `canvas` → `surface-card` → `surface-elevated` → `surface-deep`
- Hairline border: `1px solid rgba(255,255,255,0.06)` hoặc `0.14`

### Pricing Section (UX-DR6)

```typescript
// pricing-tier: bg surface-card, hairline-strong border, rounded-lg
// pricing-tier-featured (Pro): bg surface-elevated — luminance elevation ONLY
// Price display: display-lg (56px), ABC Favorit (use display font family)

<div className="bg-surface-card border border-hairline-strong rounded-lg p-8">
  <div className="text-display-lg font-display text-ink">$29</div>
</div>

// Pro tier (featured):
<div className="bg-surface-elevated border border-hairline-strong rounded-lg p-8">
```

### Landing Page Structure

```
src/app/page.tsx → Landing page (no redirect for logged-out users)
src/components/ui/Button.tsx
src/components/ui/CodeWindow.tsx
src/components/layout/NavBar.tsx     ← hamburger < 1024px
src/components/landing/Hero.tsx
src/components/landing/Features.tsx
src/components/landing/Pricing.tsx
src/components/layout/Footer.tsx
```

### Real Fetcher API curl example (for CodeWindow)

```bash
curl -X POST https://api.resili.io/api/v1/scrape/fetch \
  -H "Authorization: Bearer rsl_your_key_here" \
  -H "Content-Type: application/json" \
  -d '{"url": "https://example.com", "format": "markdown"}'
```

### Project Structure Notes

- `src/app/page.tsx` là landing page — KHÔNG redirect khi logged-out (AC: 1)
- `src/lib/utils.ts` phải có `cn()` helper (clsx + tailwind-merge)
- Font: Inter và Geist Mono load qua `next/font/google`; proprietary fonts qua `@font-face` khi có license
- Phải add `Inter` và `Geist_Mono` trong `src/app/layout.tsx` qua `next/font`

### References

- [Source: architecture.md#Dec-I-Server-State-Management] — TanStack Query (cho dashboard, không phải landing)
- [Source: epics.md#Story-1.4] — acceptance criteria
- [Source: epics.md#UX-DR1-UX-DR13] — design system requirements
- [Source: architecture.md#Frontend-File-Organization] — component structure

## Dev Agent Record

### Agent Model Used

Claude Sonnet 4.6 (Thinking)

### Debug Log References

### Completion Notes List

- Ultimate context engine analysis completed - comprehensive developer guide created

### File List

**UPDATE:**
- `frontend/tailwind.config.ts` — full design token system
- `frontend/src/app/page.tsx` — landing page

**NEW:**
- `frontend/src/components/ui/Button.tsx`
- `frontend/src/components/ui/CodeWindow.tsx`
- `frontend/src/components/layout/NavBar.tsx`
- `frontend/src/components/landing/Hero.tsx`
- `frontend/src/components/landing/Features.tsx`
- `frontend/src/components/landing/Pricing.tsx`
- `frontend/src/components/layout/Footer.tsx`
- `frontend/src/lib/utils.ts`
- `frontend/src/app/layout.tsx` — font setup
