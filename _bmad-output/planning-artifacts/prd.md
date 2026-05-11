---
workflowType: 'prd'
workflow: 'edit'
classification:
  domain: 'SaaS / Developer Tools'
  projectType: 'API Service'
  complexity: 'Medium'
inputDocuments: ['docs/report.md']
stepsCompleted: ['step-e-01-discovery', 'step-e-01b-legacy-conversion', 'step-e-02-review', 'step-e-03-edit']
lastEdited: '2026-05-10'
editHistory:
  - date: '2026-05-10'
    changes: 'Chuyển đổi từ Legacy library-wrapper PRD sang BMAD format SaaS PRD. Thêm Executive Summary, Success Criteria, User Journeys (5 journeys), Product Scope (MVP/Growth/Vision), restructure FRs và NFRs. Pivot: Scrapling-as-a-Service targeting AI Developers / Agent builders. Credit-based pricing model.'
---

# PRD: Resili — AI-Agent Data Fuel

## Executive Summary

Resili là SaaS web app chuyển Scrapling thành dịch vụ thu thập dữ liệu web được quản lý hoàn toàn, truy cập qua REST API và MCP server. AI Developers và Agent builders tích hợp web scraping vào agent/pipeline trong vài phút mà không cần cài đặt Python, quản lý Playwright, hay xử lý anti-bot.

**Vấn đề:** AI Developers cần dữ liệu web sạch (Markdown/JSON) để feed vào LLM, nhưng tự dựng scraping infrastructure tiêu tốn 2–4 tuần setup và liên tục bảo trì khi trang web đổi layout hoặc tăng cường anti-bot.

**Giải pháp:** Resili quản lý toàn bộ infrastructure — IP rotation, browser fingerprinting, Playwright runtime, uptime SLA — user chỉ gọi API. Câu trả lời cho "tại sao không tự host Scrapling?": Resili quản lý những gì bạn không muốn quản lý.

**Differentiator:** Hỗ trợ MCP protocol native — AI Agents (Claude Desktop, Cursor, OpenAI) gọi scraping như một built-in tool, không cần wrapper code. Output tối ưu cho LLM (Markdown sạch, giảm ≥60% token so với HTML thô).

**Target users:** AI Developers / Agent builders tích hợp web data vào AI agents; RAG engineers cần nguồn Markdown/JSON sạch cho vector DB.

**Nền tảng:** Fork của Scrapling v0.4.7 (BSD license). MVP: Fetcher (HTTP nhanh) và DynamicFetcher (Playwright/JS rendering). StealthyFetcher trong Growth phase (Q3 roadmap).

---

## Success Criteria

**SC-01 — API Reliability:** API đạt 99.5% uptime đo bằng external uptime monitoring; planned maintenance announced ≥ 24h trước.

**SC-02 — Fetcher Performance:** 95th percentile response ≤ 3s cho Fetcher calls dưới tải bình thường (≤ 100 concurrent requests), đo bằng APM.

**SC-03 — DynamicFetcher Performance:** 95th percentile response ≤ 15s cho DynamicFetcher calls dưới tải bình thường (≤ 20 concurrent sessions), đo bằng APM.

**SC-04 — Onboarding Speed:** 80% user mới thực hiện first successful scrape trong ≤ 10 phút từ lúc đăng ký, đo bằng event tracking.

**SC-05 — Token Efficiency:** Markdown output giảm ≥ 60% token so với HTML thô cùng trang, đo bằng benchmark nội bộ trên bộ 100 trang mẫu đa dạng.

**SC-06 — MCP Integration:** AI Agents kết nối Resili qua MCP bằng 1 dòng JSON config, không cần viết code, xác nhận bằng usability test với 5 developers.

**SC-07 — Docs Quality:** ≥ 90% code examples trong documentation chạy được không cần chỉnh sửa, đo bằng automated doc testing trong CI.

**SC-08 — Early Adoption:** 50 active API users trong 60 ngày đầu sau MVP launch, đo bằng DAU tracking.

---

## Product Scope

### MVP (Tháng 1–2)

**Mục tiêu:** Core value — gọi API, nhận Markdown/JSON sạch.

**Trong scope:**
- REST API: Fetcher endpoint và DynamicFetcher endpoint
- MCP Server (stdio transport) — AI Agents gọi trực tiếp
- Auth: API key per user (tạo, revoke, regenerate từ dashboard)
- Output format: Markdown và JSON
- Rate limiting với credit model: 1 DynamicFetcher = 5 Fetcher credits
- Dashboard: API key management + usage counter (Fetcher/Dynamic breakdown)
- Pricing: Free (1,000 credits/tháng, Fetcher only) + Pro ($29–49/tháng, 10,000 credits/tháng, Fetcher + Dynamic)
- Human-readable error messages với suggested action

**Ngoài scope MVP:**
- StealthyFetcher (Cloudflare bypass cao cấp) — Q3 roadmap
- Proxy rotation tùy chỉnh
- Async job queue / batch API
- Spider (multi-page crawl)
- Team accounts / multiple API keys

### Growth (Tháng 3–5)

- StealthyFetcher tier
- Async job queue cho DynamicFetcher (webhook + polling endpoint)
- Batch API (bulk URL processing)
- Team tier ($149–299/tháng): multiple API keys, usage reports, invoice PDF
- Proxy rotation integration

### Vision (Tháng 6+)

- Spider async: multi-page crawl với checkpoint, concurrency control
- Analytics dashboard: token savings report, usage pattern analysis
- Enterprise tier: SLA contract, dedicated infrastructure, on-premise option
- SDK chính thức (Python, TypeScript)

---

## User Journeys

### UJ-01: Onboarding — First Successful Scrape

**Persona:** AI Developer mới, chưa biết Resili
**Trigger:** Cần scrape dữ liệu web cho AI agent
**Success:** Nhận Markdown sạch từ URL thực trong ≤ 10 phút

1. Developer đăng ký tài khoản → nhận email xác nhận
2. Vào dashboard → copy API key (1 click, key đã pre-filled vào Quick Start guide)
3. Chạy curl/Python example có sẵn với URL thực
4. **Aha moment:** Nhận Markdown sạch, không có HTML noise — thấy ngay giá trị token savings
5. Tích hợp API call vào project

**Edge cases:** URL không hợp lệ → error rõ nguyên nhân; API key lỗi → HTTP 401 với link regenerate.

---

### UJ-02: Agent Builder — MCP Integration

**Persona:** Developer đang build AI agent (Claude Desktop, Cursor, OpenAI)
**Trigger:** Agent cần "đọc" trang web để trả lời câu hỏi của user
**Success:** Agent gọi Resili scraping tool không cần code wrapper

1. Developer mở MCP config của agent client
2. Vào Resili docs → copy 1 dòng JSON config (API key đã pre-filled từ dashboard)
3. Restart agent client → Resili tools (`fetch_page`, `fetch_dynamic_page`) xuất hiện trong tool list
4. Test: Agent nhận prompt với URL → tự chọn đúng tool → gọi Resili → nhận Markdown → trả lời
5. Deploy agent với Resili integration active

**Edge cases:** MCP spec version mismatch → error ghi rõ spec version Resili support; agent client không support MCP → guide chuyển sang REST API tự động hiện ra.

---

### UJ-03: RAG Engineer — Web-to-Vector Pipeline

**Persona:** Engineer xây dựng RAG pipeline
**Trigger:** Cần document từ web để chunk vào vector DB
**Success:** Nhận Markdown phù hợp để chunking, không cần cleanup thêm

1. Test với 1 URL đơn → kiểm tra Markdown output quality (heading structure, không có nav/footer noise)
2. Validate output phù hợp với chunking strategy (heading-based split)
3. Integrate REST API vào pipeline script
4. Scale lên nhiều URL với loop + rate limit header để pace request
5. Lên kế hoạch nâng cấp sang async batch API (Growth phase)

**Edge cases:** Trang yêu cầu JS rendering → Fetcher trả về empty content → error gợi ý "Try DynamicFetcher for JS-heavy pages".

---

### UJ-04: Error Recovery — Failed Scrape

**Persona:** Bất kỳ developer nào, scrape thất bại
**Trigger:** API call trả về lỗi
**Success:** Developer hiểu nguyên nhân và biết bước tiếp theo trong ≤ 2 phút

1. API call thất bại → nhận error JSON với `message` human-readable
2. Message mô tả rõ nguyên nhân: _"Anti-bot detected. Try DynamicFetcher."_ hoặc _"Timeout after 30s. Page may require JS rendering."_ hoặc _"URL returned 404."_
3. Developer thử action được gợi ý
4. Nếu vẫn thất bại → link trực tiếp đến troubleshooting doc có trong error response

---

### UJ-05: Cost Accountability — Quota Management

**Persona:** Developer/Agent builder đang dùng Pro tier
**Trigger:** Nhận email cảnh báo "đã dùng 80% quota tháng này"
**Success:** Developer quyết định upgrade hoặc optimize usage

1. Nhận email với breakdown: Fetcher vs Dynamic credit usage theo ngày
2. Click link → vào dashboard usage page trực tiếp (không phải homepage)
3. Xem biểu đồ usage → identify spike ngày nào, endpoint nào
4. Quyết định: upgrade tier (1 click) hoặc optimize (xem calls nào dùng Dynamic không cần thiết)
5. Nếu upgrade → chuyển sang Team tier → nhận invoice PDF

---

## Functional Requirements

### Auth & Access

**FR-01:** Users tạo được API key từ dashboard, với tùy chọn revoke và regenerate bất kỳ lúc nào.

**FR-02:** Mỗi API request được xác thực qua API key trong `Authorization` header; request không có key hợp lệ nhận HTTP 401 với message giải thích rõ.

**FR-03:** Users xem được credit usage breakdown theo Fetcher/Dynamic trong dashboard, cập nhật theo thời gian thực.

### Core Scraping API

**FR-04:** Users gọi Fetcher endpoint với URL để nhận nội dung trang tĩnh dạng Markdown hoặc JSON, không cần JS rendering.

**FR-05:** Users gọi DynamicFetcher endpoint với URL để nhận nội dung trang JS-heavy sau khi render hoàn toàn, dạng Markdown hoặc JSON.

**FR-06:** Users chỉ định output format (`markdown` hoặc `json`) qua request parameter; default là `markdown`.

**FR-07:** Khi scrape thất bại, API trả về error JSON với field `message` human-readable mô tả nguyên nhân cụ thể và action được gợi ý, kèm link troubleshooting doc.

### MCP Integration

**FR-08:** AI Agents kết nối được Resili qua MCP stdio transport bằng cách thêm 1 JSON config entry, không cần viết code wrapper.

**FR-09:** MCP server expose tối thiểu 2 tools: `fetch_page` (Fetcher) và `fetch_dynamic_page` (DynamicFetcher), với description đủ rõ để LLM chọn đúng tool theo context.

**FR-10:** Resili document MCP spec version được support; incompatibility trả về error message có ghi rõ spec version đang dùng và version Resili support.

### Rate Limiting & Pricing Tiers

**FR-11:** Free tier giới hạn 1,000 Fetcher credits/tháng; DynamicFetcher không khả dụng ở Free tier.

**FR-12:** Pro tier áp dụng credit multiplier: 1 DynamicFetcher call tiêu thụ 5 Fetcher credits.

**FR-13:** Request vượt quota nhận HTTP 429 với header `Retry-After` và body ghi rõ credit loại nào đã hết và khi nào reset.

**FR-14:** Users nhận email cảnh báo khi đạt 80% quota tháng, với link trực tiếp đến usage dashboard.

**FR-15:** Users nâng cấp tier từ dashboard với 1 click, không cần contact sales.

### Dashboard

**FR-16:** Users xem được credit usage theo ngày/tuần/tháng, phân tách Fetcher credits và Dynamic credits.

---

## Non-Functional Requirements

**NFR-01 — Availability:** API đạt 99.5% uptime đo bằng external uptime monitoring; planned maintenance announced ≥ 24h trước qua email và status page.

**NFR-02 — Fetcher Latency:** Fetcher API response time ≤ 3s ở 95th percentile dưới tải bình thường (≤ 100 concurrent requests), đo bằng APM monitoring.

**NFR-03 — DynamicFetcher Latency:** DynamicFetcher API response time ≤ 15s ở 95th percentile dưới tải bình thường (≤ 20 concurrent Playwright sessions), đo bằng APM monitoring.

**NFR-04 — DynamicFetcher Isolation:** Mỗi DynamicFetcher request chạy trong isolated process với timeout 30s và memory cap; một request lỗi không affect request khác.

**NFR-05 — Scalability:** System scale horizontal để xử lý 10x load spike mà không có downtime, thông qua container orchestration.

**NFR-06 — Transport Security:** Toàn bộ API traffic qua HTTPS/TLS 1.2+; HTTP requests bị redirect tự động sang HTTPS.

**NFR-07 — API Key Security:** API keys được store dưới dạng hashed; plaintext key chỉ hiển thị một lần duy nhất tại thời điểm tạo.

**NFR-08 — Input Validation:** System validate và sanitize tất cả URL inputs tại API gateway; SSRF attack vectors bị block trước khi đến scraping layer.

**NFR-09 — Data Retention:** Resili không lưu nội dung trang đã scrape; chỉ lưu metadata request (timestamp, URL hash, credit usage) trong 90 ngày.

**NFR-10 — Robots.txt Compliance:** Resili expose tùy chọn `respect_robots_txt` per request; default off; behavior documented rõ trong ToS để user hiểu trách nhiệm tuân thủ.

**NFR-11 — License Compliance:** BSD license của Scrapling upstream được giữ nguyên trong fork; attribution hiển thị trong About page và response headers.

**NFR-12 — DynamicFetcher Async Architecture:** MVP: DynamicFetcher synchronous với timeout 30s. Growth phase: async job queue với webhook callback và polling endpoint — thiết kế MVP không được block migration này.

---

## Innovation Analysis

**Competitors:**
- **Apify, ScrapingBee, Zyte:** General-purpose scraping APIs, không tối ưu cho LLM consumption, không có MCP support native.
- **Jina Reader, FireCrawl:** Web-to-Markdown focused nhưng không có adaptive parsing hay stealth capability roadmap.

**Resili differentiators:**
1. **MCP-native:** Scraping-as-MCP-tool — AI Agents gọi trực tiếp không cần wrapper code. Duy nhất trong phân khúc tại thời điểm launch.
2. **Scrapling adaptive parsing:** Parser thích ứng khi DOM thay đổi (opt-in, `adaptive=True`) — giảm maintenance cho long-running pipelines.
3. **LLM-optimized output:** Markdown pipeline qua `markdownify` tối ưu token consumption, không phải HTML dump.

**Moat:** MCP ecosystem tăng trưởng nhanh (2025–2026); first-mover advantage với scraping-as-MCP-tool tạo switching cost khi agent ecosystem trưởng thành.

---

## Project-Type Requirements

**Platform:** REST API Service + Web Dashboard (SaaS)
**Auth model:** API key (MVP); OAuth/SSO (Growth phase)
**Billing:** Stripe metered billing với credit-based model; Free + Pro tiers tại MVP launch
**Runtime:** Docker containers; browser-capable images (Playwright) cho DynamicFetcher, isolated per request
**Observability:** APM cho API latency tracking, external uptime monitoring, credit usage event tracking
**Documentation:** OpenAPI spec tự động generated từ code; Quick Start guide với code examples đã test; MCP config guide với copy-paste JSON
**Legal:** ToS nêu rõ robots.txt responsibility; BSD attribution maintained; user chịu trách nhiệm tuân thủ ToS của target sites
