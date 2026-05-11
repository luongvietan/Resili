# Sprint Change Proposal
**Date:** 2026-05-11
**Project:** resili
**Scope:** Pre-Implementation Corrections (triggered by Implementation Readiness Assessment)
**Classification:** Minor — Direct adjustment by Developer agent

---

## 1. Issue Summary

Implementation Readiness Assessment (2026-05-11) phát hiện 5 vấn đề cần giải quyết trước Sprint Planning để tránh blockers trong implementation. Không có thay đổi về MVP scope hay architectural decisions — đây là corrections trong epics/stories và PRD.

---

## 2. Impact Analysis

**Epic Impact:**
- Epic 1: Thêm Story 1.4 (Public Landing Page — di chuyển từ Epic 5); cập nhật scope description
- Epic 2: Thêm Story 2.7 (Credit Balance DB Initialization); thêm AC vào Story 2.1
- Epic 3: Cập nhật Story 3.1 (xóa ACs về credit_balances, đổi migration number thành 004)
- Epic 5: Xóa Story 5.8 (di chuyển vào Epic 1); cập nhật scope; cập nhật Story 5.1 (font AC), Story 5.6 (Pro limit)

**Artifact Conflicts:**
- `epics.md` — 8 thay đổi cụ thể
- `docs/report.md` (PRD) — 1 thay đổi (Pro tier credit limit)

**Technical Impact:** Không có thay đổi architectural. Migration numbering cập nhật (003 = credit_balances, 004 = usage_events).

---

## 3. Recommended Approach

**Option 1 — Direct Adjustment** ✅ (Đã thực hiện)

Không cần rollback hay thay đổi MVP scope. Tất cả corrections là additive (thêm story, thêm ACs) hoặc clarifying (define Pro limit, font strategy).

**Effort:** Low | **Risk:** Low | **Timeline impact:** None

---

## 4. Detailed Change Proposals (Đã Apply)

### Change 1 — 🔴 Critical: Forward Dependency Fix

**File:** `epics.md`

| Item | Thay đổi |
|------|---------|
| Story 2.1 | Thêm AC: tạo `credit_balances` row trong cùng registration transaction |
| Story 2.7 (MỚI) | Tạo migration `003_create_credit_balances`; wire vào registration; backfill |
| Story 3.1 | Xóa ACs về credit_balances; migration đổi thành `004_create_usage_events` |

**Rationale:** Giải quyết impossible state khi Epic 2 implement trước Epic 3.

---

### Change 2 — 🟠 Major: Pro Tier Credit Limit

**Files:** `docs/report.md`, `epics.md`

| Item | Thay đổi |
|------|---------|
| PRD Product Scope MVP | "Pro ($29–49/tháng, **10,000 credits/tháng**, Fetcher + Dynamic)" |
| Story 5.6 AC | `monthly_limit` to `10000` (explicit value, không còn ambiguous) |

---

### Change 3 — 🟠 Major: Landing Page Content Mismatch

**File:** `epics.md`

| Item | Thay đổi |
|------|---------|
| Story 1.4 (= Story 5.8 cũ) | Thêm 2 ACs: scraping-specific headline; email-mockup → code-window |

---

### Change 4 — 🟠 Major: Font Licensing Strategy

**File:** `epics.md`

| Item | Thay đổi |
|------|---------|
| Story 5.1 | Thêm AC: developer chọn licensed hoặc fallback fonts, document trong code comment |

---

### Change 5 — 🟠 Major: Story 5.8 → Story 1.4 (Epic Relocation)

**File:** `epics.md`

| Item | Thay đổi |
|------|---------|
| Epic 1 | Thêm Story 1.4 (Public Landing Page); cập nhật UX-DRs covered |
| Epic 5 | Xóa Story 5.8; cập nhật UX-DRs covered |

---

## 5. Implementation Handoff

**Scope Classification:** Minor — Developer agent có thể proceed trực tiếp.

**Không cần:** Thay đổi PRD goals, architecture decisions, hay epic sequence.

**Next Step:** Chạy `/bmad-sprint-planning` trong fresh context window để generate sprint plan từ epics đã cập nhật.

---

## 6. Summary

| Vấn đề | Severity | Status |
|--------|---------|--------|
| Forward dependency credit_balances | 🔴 Critical | ✅ Fixed |
| Pro tier credit limit undefined | 🟠 Major | ✅ Fixed (10,000 credits) |
| Landing page email content mismatch | 🟠 Major | ✅ Fixed |
| Proprietary font licensing gap | 🟠 Major | ✅ Fixed |
| Story 5.8 wrong epic placement | 🟠 Major | ✅ Fixed |
