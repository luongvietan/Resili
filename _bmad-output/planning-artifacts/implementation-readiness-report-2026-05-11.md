---
stepsCompleted: ['step-01-document-discovery']
outputFile: '_bmad-output/planning-artifacts/implementation-readiness-report-2026-05-11.md'
documentsUsed:
  prd: 'docs/report.md'
  ux: 'docs/DESIGN.md'
  architecture: '_bmad-output/planning-artifacts/architecture.md'
  epics: '_bmad-output/planning-artifacts/epics.md'
---

# Implementation Readiness Assessment Report

**Date:** 2026-05-11
**Project:** resili

## Document Inventory

| Loại | File | Trạng thái |
|------|------|-----------|
| PRD | docs/report.md | ✅ Tìm thấy |
| UX Design | docs/DESIGN.md | ✅ Tìm thấy |
| Architecture | _bmad-output/planning-artifacts/architecture.md | ✅ Tìm thấy |
| Epics & Stories | _bmad-output/planning-artifacts/epics.md | ✅ Tìm thấy |

---

## PRD Analysis

### Functional Requirements (16 tổng)

**Auth & Access:**
- FR-01: Users tạo được API key từ dashboard, với tùy chọn revoke và regenerate bất kỳ lúc nào.
- FR-02: Mỗi API request được xác thực qua API key trong `Authorization` header; request không có key hợp lệ nhận HTTP 401.
- FR-03: Users xem được credit usage breakdown theo Fetcher/Dynamic trong dashboard, cập nhật theo thời gian thực.

**Core Scraping API:**
- FR-04: Users gọi Fetcher endpoint với URL để nhận nội dung trang tĩnh dạng Markdown hoặc JSON.
- FR-05: Users gọi DynamicFetcher endpoint với URL để nhận nội dung trang JS-heavy sau khi render hoàn toàn.
- FR-06: Users chỉ định output format (`markdown` hoặc `json`); default là `markdown`.
- FR-07: Khi scrape thất bại, API trả về error JSON với field `message` human-readable + `hint` + `docs_url`.

**MCP Integration:**
- FR-08: AI Agents kết nối Resili qua MCP stdio với 1 JSON config entry.
- FR-09: MCP server expose 2 tools: `fetch_page` và `fetch_dynamic_page`.
- FR-10: Resili document MCP spec version; incompatibility trả về error rõ version.

**Rate Limiting & Pricing:**
- FR-11: Free tier giới hạn 1,000 Fetcher credits/tháng; DynamicFetcher không khả dụng ở Free tier.
- FR-12: Pro tier: 1 DynamicFetcher call = 5 Fetcher credits.
- FR-13: Request vượt quota nhận HTTP 429 với `Retry-After` header và body rõ credit nào hết và khi nào reset.
- FR-14: Users nhận email cảnh báo khi đạt 80% quota tháng, với link trực tiếp đến usage dashboard.
- FR-15: Users nâng cấp tier từ dashboard với 1 click, không cần contact sales.
- FR-16: Users xem credit usage theo ngày/tuần/tháng, phân tách Fetcher và Dynamic credits.

**Tổng FRs: 16**

### Non-Functional Requirements (12 tổng)

- NFR-01: API đạt 99.5% uptime; planned maintenance announced ≥ 24h trước.
- NFR-02: Fetcher p95 response ≤ 3s dưới ≤ 100 concurrent requests.
- NFR-03: DynamicFetcher p95 response ≤ 15s dưới ≤ 20 concurrent Playwright sessions.
- NFR-04: Mỗi DynamicFetcher request chạy isolated process, timeout 30s, memory cap.
- NFR-05: System scale horizontal để xử lý 10x load spike, không downtime.
- NFR-06: Toàn bộ API traffic qua HTTPS/TLS 1.2+.
- NFR-07: API keys stored dưới dạng hashed; plaintext hiển thị một lần duy nhất.
- NFR-08: URL inputs được validate và sanitize tại API gateway; SSRF blocked.
- NFR-09: Không lưu nội dung trang; chỉ lưu metadata trong 90 ngày.
- NFR-10: `respect_robots_txt` option per request; default off.
- NFR-11: BSD license attribution maintained.
- NFR-12: MVP DynamicFetcher synchronous; thiết kế không block migration lên async Growth phase.

**Tổng NFRs: 12**

---

## Epic Coverage Validation

### Coverage Matrix

| FR | PRD Requirement | Epic Coverage | Trạng thái |
|----|----------------|---------------|-----------|
| FR-01 | API key CRUD từ dashboard | Epic 2, Story 2.3 + 2.4 + 5.4 | ✅ Covered |
| FR-02 | Auth qua Authorization header | Epic 2, Story 2.5 | ✅ Covered |
| FR-03 | Credit usage real-time trong dashboard | Epic 5, Story 5.5 | ✅ Covered |
| FR-04 | Fetcher endpoint | Epic 3, Story 3.3 | ✅ Covered |
| FR-05 | DynamicFetcher endpoint | Epic 3, Story 3.4 | ✅ Covered |
| FR-06 | Output format configurable | Epic 3, Story 3.3 + 3.4 | ✅ Covered |
| FR-07 | Error JSON human-readable | Epic 3, Story 3.5 + Epic 1 Story 1.2 | ✅ Covered |
| FR-08 | MCP stdio connect | Epic 4, Story 4.1 | ✅ Covered |
| FR-09 | MCP tools: fetch_page + fetch_dynamic_page | Epic 4, Story 4.2 | ✅ Covered |
| FR-10 | MCP spec version documented | Epic 4, Story 4.3 | ✅ Covered |
| FR-11 | Free tier 1,000 Fetcher credits | Epic 3, Story 3.2 | ✅ Covered |
| FR-12 | Credit multiplier 1 Dynamic = 5 Fetcher | Epic 3, Story 3.2 | ✅ Covered |
| FR-13 | HTTP 429 + Retry-After | Epic 3, Story 3.2 | ✅ Covered |
| FR-14 | Email alert tại 80% quota | Epic 5, Story 5.7 | ✅ Covered |
| FR-15 | 1-click tier upgrade | Epic 5, Story 5.6 | ✅ Covered |
| FR-16 | Usage visualization | Epic 5, Story 5.5 | ✅ Covered |

**Coverage Statistics:**
- Total PRD FRs: 16
- FRs covered in epics: 16
- Coverage percentage: **100%**

### NFR Coverage

| NFR | Coverage | Trạng thái |
|-----|---------|-----------|
| NFR-01 (uptime 99.5%) | Epic 5 scope + external monitoring | ⚠️ Không có story cụ thể |
| NFR-02 (Fetcher ≤ 3s) | Story 3.3 AC | ✅ Covered |
| NFR-03 (Dynamic ≤ 15s) | Story 3.4 AC | ✅ Covered |
| NFR-04 (isolation) | Story 3.4 | ✅ Covered |
| NFR-05 (10x scaling) | Infrastructure / deployment config | ✅ Covered (implicit) |
| NFR-06 (TLS) | Railway/Render ingress | ✅ Covered (implicit) |
| NFR-07 (key hashed) | Story 2.3 AC | ✅ Covered |
| NFR-08 (SSRF) | Story 2.6 | ✅ Covered |
| NFR-09 (data retention 90 days) | Story 3.1 AC | ✅ Covered |
| NFR-10 (robots.txt option) | Story 3.3 AC | ✅ Covered |
| NFR-11 (BSD attribution) | Story 1.3 AC | ✅ Covered |
| NFR-12 (async-ready shape) | Story 3.4 AC + Dec-F | ✅ Covered |

---

## UX Alignment Assessment

### UX Document Status

✅ **Tìm thấy:** `docs/DESIGN.md` — Design system đầy đủ với color tokens, typography, components, responsive behavior.

### UX → Epics Alignment

UX-DR1 through UX-DR13 đều được map vào Epic 5 (Stories 5.1, 5.2, 5.8) trong epics.md. Về mặt traceability, coverage đầy đủ.

### Alignment Issues Phát Hiện

**⚠️ CẢNH BÁO NGHIÊM TRỌNG — DESIGN.MD CONTENT MISMATCH:**

DESIGN.md được viết với content language của một **email service product**, không phải scraping API:
- Overview: "Email for developers", "Email reimagined" — là headline của sản phẩm email
- Sections: "hero → atmospheric → code window → **email mockup section** → pricing → footer"
- Component `email-mockup` được mô tả là feature showcase cho email rendering
- "Beyond experience" section nói về email mockup cards

Tuy nhiên, **Resili là một web scraping API** — không phải email service. DESIGN.md dường như được copied/adapted từ design system của sản phẩm email khác (có thể là Resend hoặc tương tự).

**Hệ quả:** Story 5.8 (Public Landing Page) dùng DESIGN.md làm nguồn nhưng các ACs không yêu cầu thay thế email-specific content bằng scraping-specific content. Nếu developer follow DESIGN.md nguyên văn sẽ build landing page có "Email for developers" thay vì messaging về web scraping.

**⚠️ CẢNH BÁO — Font Licensing Gap:**

UX-DR2 yêu cầu: **Domaine Display** và **ABC Favorit** — đây là proprietary fonts cần license thương mại. Architecture không đề cập đến font licensing. Story 5.1 ACs chỉ verify Inter và Geist Mono (free fonts), bỏ qua hoàn toàn việc configure proprietary fonts. Implementation sẽ phải dùng fallbacks (Söhne/Tiempos Headline cho Domaine Display, Geist/Inter Tight cho ABC Favorit) nhưng không có story nào document quyết định này.

---

## Epic Quality Review

### Epic 1: Foundation & Project Setup — ⚠️ Minor Concern

**User Value Assessment:** Epic 1 là technical foundation — không deliver user value trực tiếp. Tuy nhiên, đây là pattern bình thường và được chấp nhận cho greenfield projects. Acceptable.

**Story Analysis:**
- Story 1.1: ✅ Monorepo scaffold — clear deliverable
- Story 1.2: ✅ Error schema + health endpoints — foundational, proper placement
- Story 1.3: ✅ CI/CD + observability — proper timing

### Epic 2: Authentication & API Key Management — 🔴 Critical Violation

**🔴 CRITICAL: Forward Dependency — Story 2.1 → Story 3.1**

Story 2.1 (User Registration, Epic 2) có acceptance criteria:
> "Given a new user completing registration (Story 2.1), When the user record is created, Then a corresponding `credit_balances` row is created automatically"

Nhưng **`credit_balances` table chỉ được tạo trong Story 3.1 (Epic 3)**. Khi implement Epic 2 trước Epic 3 (đúng thứ tự), migration `003_create_credit_balances` chưa chạy, nên không thể INSERT vào bảng này.

Điều này có nghĩa là **Story 2.1 không thể pass acceptance criteria của chính nó** nếu Epic 3 chưa được implement — vi phạm nguyên tắc epic independence.

**Khuyến nghị:** Di chuyển `credit_balances` table creation vào Story 2.1 (hoặc tạo Story 2.7 riêng trong Epic 2), hoặc thay đổi Story 2.1 để KHÔNG tạo credit_balances ngay (thay vào đó Story 3.1 thực hiện backfill/trigger).

**Story Analysis:**
- Story 2.1: 🔴 Forward dependency với Story 3.1
- Story 2.2: ✅ JWT login — independent, good ACs
- Story 2.3: ✅ API key generation — clear, testable ACs
- Story 2.4: ✅ Key management — good ACs, covers error cases
- Story 2.5: ✅ Auth middleware — depends properly on 2.3
- Story 2.6: ✅ SSRF guard — proper placement before Epic 3

### Epic 3: Core Scraping API & Credit Enforcement — 🟠 Major Issue

**🟠 MAJOR: Pro Tier Credit Limit Undefined**

Story 3.2 và Story 5.6 đề cập đến "Pro limit" nhưng con số cụ thể **không được define ở bất kỳ đâu**:
- PRD nói "$29–49/tháng" nhưng không nói bao nhiêu credits
- Architecture không define `monthly_limit` cho Pro tier
- Story 5.6 AC: "update `credit_balances.monthly_limit` to the Pro limit" — Pro limit là gì?

Nếu developer không có số này, họ sẽ phải đoán. Đây là implementation ambiguity có thể gây ra discrepancy giữa frontend (pricing page) và backend (credit enforcement).

**Story Analysis:**
- Story 3.1: ✅ DB tables — clear schema, good ACs
- Story 3.2: ✅ Credit accounting — proper SELECT FOR UPDATE, concurrent test AC ✅
- Story 3.3: ✅ Fetcher endpoint — async-ready shape, good error cases
- Story 3.4: ✅ DynamicFetcher — isolation, timeout, async-ready shape ✅
- Story 3.5: ✅ Error handling — comprehensive error codes

### Epic 4: MCP Server Integration — ✅ Good

**Story Analysis:**
- Story 4.1: ✅ MCP process — good isolation test, direct import constraint
- Story 4.2: ✅ Tool descriptions — LLM-readability criteria ✅
- Story 4.3: ✅ Spec compatibility + documentation

**Minor:** Story 4.1 dependencies trên Epic 3 (cần `app.scraping.fetcher` và `app.scraping.dynamic`) là proper sequential dependency — không phải forward dependency.

### Epic 5: Dashboard, Billing & Notifications — 🟠 Major Issues

**🟠 MAJOR: Story 5.8 đặt sai Epic**

Story 5.8 (Public Landing Page) thuộc về Epic 5 "Dashboard, Billing & Notifications" — nhưng landing page là **public marketing page**, không liên quan đến billing hay dashboard. Điều này:
- Tạo confusion về scope của Epic 5
- Landing page nên được build sớm hơn (có thể trong Epic 1 hoặc Epic 2) để có product presence từ sớm

**🟠 MAJOR: UX-DR2 Proprietary Fonts Không Được Handle**

Story 5.1 ACs chỉ verify: "Inter và Geist Mono fonts khi configured via next/font" — bỏ qua hoàn toàn Domaine Display và ABC Favorit. Developer không biết phải làm gì với proprietary fonts.

**🟡 MINOR: NFR-01 Uptime Monitoring Không Có Story**

Epic 5 coverage list bao gồm NFR-01 nhưng không có story nào cho việc setup BetterUptime/UptimeRobot. "Covered" ở đây chỉ là implicit.

**Story Analysis:**
- Story 5.1: 🟠 Font handling incomplete
- Story 5.2: ✅ Dashboard shell — good responsive ACs
- Story 5.3: ✅ OpenAPI type generation — type safety enforced ✅
- Story 5.4: ✅ API key management UI — copy-to-clipboard AC ✅
- Story 5.5: ✅ Usage dashboard — Recharts color tokens ✅
- Story 5.6: 🟠 Pro credit limit undefined
- Story 5.7: ✅ Quota email — one-email-per-threshold AC ✅
- Story 5.8: 🟠 Content mismatch với DESIGN.md; wrong epic placement

---

## Summary and Recommendations

### Overall Readiness Status

## 🟡 NEEDS WORK — 1 Critical Issue, 4 Major Issues

Tài liệu được chuẩn bị rất tốt với coverage 16/16 FRs và 12/12 NFRs. Nhưng có những vấn đề cần giải quyết trước khi bắt đầu implementation để tránh blockers.

---

### Critical Issues Requiring Immediate Action

**🔴 CRITICAL-1: Forward Dependency Story 2.1 → Story 3.1 (credit_balances table)**

Epic 2 Story 2.1 (User Registration) yêu cầu tạo `credit_balances` row khi user đăng ký, nhưng bảng `credit_balances` chỉ được tạo ở Epic 3 Story 3.1. Epic 2 phải implement trước Epic 3, tạo ra impossible state.

**Fix options (chọn 1):**
- Option A: Thêm migration `003_create_credit_balances` vào Story 2.1 (gộp với `001_create_users`)
- Option B: Thêm Story 2.7 "Credit Balance DB Initialization" vào Epic 2 với migration cho `credit_balances`
- Option C: Xóa AC "tạo credit_balances tự động" khỏi Story 2.1, thay bằng cách Story 3.1 chạy backfill/trigger

---

### Major Issues

**🟠 MAJOR-1: Pro Tier Monthly Credit Limit Undefined**

Cần define con số cụ thể (e.g., 10,000 credits/tháng cho Pro tier) và add vào PRD/Architecture. Story 5.6 và pricing page cần con số này để implement. Đề xuất: Add định nghĩa vào PRD Product Scope section và Architecture `credit_balances` schema.

**🟠 MAJOR-2: DESIGN.MD Content Mismatch — Email vs Scraping Product**

DESIGN.md dùng language của email product ("Email for developers", "email mockup" as core section). Story 5.8 ACs không yêu cầu adapt content cho scraping API. Developer cần hướng dẫn rõ ràng: dùng design system (colors, typography, components) từ DESIGN.md nhưng THAY THẾ toàn bộ email-specific content bằng scraping-specific messaging.

**Khuyến nghị:** Thêm AC vào Story 5.8: "Hero headline mô tả giá trị scraping API (không phải email service); email-mockup component được thay thế bằng code-window component showcase scraping output."

**🟠 MAJOR-3: Proprietary Font Licensing Not Addressed**

Cần quyết định: Mua license Domaine Display + ABC Favorit, hoặc chính thức document dùng fallbacks (Söhne/Tiempos Headline, Geist/Inter Tight). Story 5.1 phải có AC rõ ràng về font strategy này.

**🟠 MAJOR-4: Story 5.8 Placed in Wrong Epic**

Public landing page không thuộc "Dashboard, Billing & Notifications". Đề xuất: Di chuyển Story 5.8 thành Story 2.7 (trong Epic 2) hoặc tạo Epic 0 / Story 1.4 trong Epic 1. Landing page cần có sớm để product có web presence.

---

### Minor Issues

**🟡 MINOR-1: NFR-01 Uptime Monitoring Không Có Story**

Thêm story hoặc task trong Epic 5 cho việc setup BetterUptime/UptimeRobot account và configure public status page.

**🟡 MINOR-2: Không Có Password Reset Flow**

PRD không mention account recovery — có thể intentional (MVP simplification). Nhưng nên document explicitly là out-of-scope nếu đúng vậy.

---

### Recommended Next Steps

1. **Ngay lập tức:** Giải quyết CRITICAL-1 — quyết định Option A/B/C cho credit_balances forward dependency và cập nhật epics.md.
2. **Trước Sprint 1:** Define Pro tier credit limit (MAJOR-1) — add vào PRD và Architecture.
3. **Trước Story 5.8:** Clarify DESIGN.MD content intent (MAJOR-2) — add explicit AC về scraping-specific content.
4. **Trước Story 5.1:** Quyết định font licensing strategy (MAJOR-3) — update Story 5.1 ACs.
5. **Nice-to-have:** Move Story 5.8 vào Epic 1 hoặc 2 để có early web presence.

---

### Final Note

Đánh giá này phát hiện **1 Critical** và **4 Major** và **2 Minor** issues trên **4 categories**. Tài liệu nhìn chung được chuẩn bị rất tốt — coverage 16/16 FRs, 12/12 NFRs, architectural decisions rõ ràng, acceptance criteria phần lớn testable. Chỉ cần address Critical-1 trước khi bắt đầu, các Major issues còn lại có thể giải quyết trong sprint planning.
