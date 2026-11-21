# Test Infrastructure Specification — Clear_Hire.AI

**Document Version:** 1.0.0  
**Target Environment:** Local Workstation (Windows 11 / Node v24.20 / Python 3.11.9)  
**Parity Target:** Root (`backend/`, `frontend/`) and Development Mirror (`job_automate/backend/`, `job_automate/frontend/`)  
**Scope:** Performance, Concurrency, Latency, 3D Spatial Framerate (60 FPS), and End-to-End Regressions.

---

## 1. Test Philosophy & Principles

1. **Opaque-Box Requirement-Driven Testing:**
   All end-to-end and benchmark suites treat the backend and frontend systems as opaque black-box services accessible only through their public network contracts (HTTP REST APIs, WebSocket events, and browser DOM / WebGL rendering). Tests do not mock or bind directly to internal classes or private service methods unless explicitly testing unit algorithms in isolation.

2. **Zero-Flake Determinism:**
   Network calls, database queries, and async operations must use bounded timeouts, deterministic seeds, and explicit readiness probing (`/ready`, `/health`) rather than arbitrary sleep delays.

3. **Performance as an Invariant:**
   Latency percentiles (p50, p95, p99), concurrent QPS capacity, server memory RSS stability, and UI rendering framerates (60 FPS, Mean FPS >= 55, 1% Low >= 45, dropped frames <= 5%) are treated as hard gating assertions. Any degradation beyond baseline triggers build failure.

4. **100% Mirror Parity Invariance:**
   All backend and frontend tests must pass identically with 100% byte-for-byte SHA-256 parity between root repositories and their `job_automate/` mirrors.

---

## 2. Methodology: 4-Tier Test Architecture

```
+-----------------------------------------------------------------------------------+
|                        Tier 4: Real-World User Scenarios                         |
|   (Complete multi-step user journeys from resume upload to interview simulation)  |
+-----------------------------------------------------------------------------------+
                                         ^
                                         |
+-----------------------------------------------------------------------------------+
|                  Tier 3: Pairwise Cross-Feature Combinations                      |
|       (Concurrent scraping + matching; auth session expiry + resume parsing;     |
|              WebGL camera glide + route transition under active polling)          |
+-----------------------------------------------------------------------------------+
                                         ^
                                         |
+-----------------------------------------------------------------------------------+
|                     Tier 2: Boundary & Corner Cases                               |
|   (Malformed PDF headers, 10MB payloads, 50-concurrency saturation, zero-job      |
|         scrape results, extreme aspect ratios [375x812 vs 2560x1440])             |
+-----------------------------------------------------------------------------------+
                                         ^
                                         |
+-----------------------------------------------------------------------------------+
|                        Tier 1: Feature Coverage (>=5 per feature)                 |
|   (Direct contract validation for each endpoint, component, model, and route)     |
+-----------------------------------------------------------------------------------+
```

### Tier 1: Feature Coverage (>= 5 Tests Per Core Feature)
- **Feature 1: Parse (`POST /api/resumes/upload`)**
  - T1.1: Standard single-page PDF upload with valid ATS formatting returns `ResumeUploadResponse` with 200.
  - T1.2: Plain text (`.txt`) resume upload extracts valid contact, skills, and work history sections.
  - T1.3: DOCX resume extraction correctly parses nested bullet points and dates.
  - T1.4: Async execution confirms event loop remains unblocked during extraction (`threadpool` delegation).
  - T1.5: Content hash computation (`sha256`) accurately deduplicates identical uploads for the same user.
- **Feature 2: Match (`POST /api/resumes/match`)**
  - T2.1: Matching against standard JD returns keyword score, embedding similarity, and combined score.
  - T2.2: Reconciled match provides top-K evidence snippets referencing database source entities.
  - T2.3: LangGraph state graph compilation executes once per process lifetime without per-request rebuilds.
  - T2.4: Missing keywords array accurately reflects required technologies absent from candidate resume.
  - T2.5: Zero-overlap resume and JD gracefully return low score (<25.0) without 500 runtime errors.
- **Feature 3: Search (`POST /api/jobs/scrape`)**
  - T3.1: Search with specific keywords and locations returns valid `ScrapeJobsResponse` list.
  - T3.2: Direct ATS source filtering correctly isolates Greenhouse, Lever, and Ashby requisitions.
  - T3.3: Ghost job detector flags stale listings older than configured threshold (e.g. >14 days).
  - T3.4: Concurrency deduplication preserves unique URLs during concurrent scraper execution.
  - T3.5: Liveness verification returns `fallback_career_url` when direct application link expires.
- **Feature 4: Digest (`POST /api/jobs/digest` & `GET /api/digest/preview`)**
  - T4.1: Digest preview returns top-ranked matched jobs conforming to user target role preferences.
  - T4.2: Digest email rendering constructs valid HTML layout with anti-ghosting warnings.
  - T4.3: SLA tracking alerts user for applications in applied status pending >14 days.
  - T4.4: In-memory/Redis caching prevents redundant candidate preference re-queries.
  - T4.5: Target company filtering restricts scraped jobs strictly to user whitelist.
- **Feature 5: Applications CRM (`GET /api/applications/` & Kanban)**
  - T5.1: Listing applications returns serialized list with joined job description and resume version.
  - T5.2: State transitions enforce valid lifecycle (`bookmarked` -> `applied` -> `screening` -> `offer`).
  - T5.3: Status patch updates `days_since_update` and refreshes ghosting classification.
  - T5.4: Grounded interview prep synthesis pulls exact resume version used at application creation.
  - T5.5: Consolidated joined queries execute with 1 SQL round-trip eliminating N+1 query overhead.
- **Feature 6: 3D Ambient Story UI & Module Continuity**
  - T6.1: `ClearHireAmbientWorld` mounts as a singleton persistent canvas across route transitions.
  - T6.2: Route navigation triggers smooth camera glide between station coordinates without canvas reloads.
  - T6.3: Radar reskin renders warm travertine `#f6f4ee`, walnut, and bronze aesthetic instead of dark theme.
  - T6.4: Pixel ratio capped at 1.5 and half-res bloom active to prevent GPU throttling.
  - T6.5: Zero heap allocation in `requestAnimationFrame` loop (verified through object pooling).

---

### Tier 2: Boundary & Corner Cases (>= 5 Tests Per Core Feature)
- **B1. Extreme Payload & Corrupted File Boundaries:**
  - B1.1: Uploading a 0-byte file returns HTTP 400 with descriptive error message.
  - B1.2: Uploading an oversized file (>10MB) rejected immediately before memory buffer allocation.
  - B1.3: Uploading a renamed `.exe` binary disguised as `.pdf` blocked by MIME/magic bytes check.
  - B1.4: Highly nested or cyclical JSON in JD match request returns HTTP 422 schema validation error.
  - B1.5: Non-ASCII / Unicode resume text (Devanagari, Cyrillic, emoji) parses without encoding crashes.
- **B2. Concurrency & Connection Saturation Boundaries:**
  - B2.1: 50 concurrent requests to `/api/resumes/match` complete with 0 unhandled 5xx errors.
  - B2.2: Neon PostgreSQL pool saturation (60 pool size + 40 overflow) queues requests without connection drop.
  - B2.3: Simultaneous scraper triggers for identical queries resolve via atomic upsert without integrity crash.
  - B2.4: Redis service connection refusal gracefully falls back to `InMemoryCacheProvider` within 0.2s.
  - B2.5: Server process memory RSS delta remains < 50MB after 1,000 continuous requests (no memory leaks).
- **B3. Mobile & Viewport Layout Boundaries:**
  - B3.1: Viewport resize from desktop (1440x900) to mobile (375x812) dynamically adjusts camera FOV.
  - B3.2: Mobile portrait aspect ratios (9:19.5) prevent 3D ambient world geometry clipping.
  - B3.3: Native touch scrolling operates smoothly without canvas event capture interference (`pointer-events: none`).
  - B3.4: Rapid route thrashing (5 route changes in 1 second) completes spring animation without NaN camera poses.
  - B3.5: Hidden browser tab triggers RAF throttling, reducing GPU utilization to 0%.

---

### Tier 3: Pairwise Cross-Feature Combinations
- **P1: Concurrent Resume Upload + Real-Time Scrape Matching:**
  Simultaneous execution of multipart resume uploads while the scraper is actively populating `JobPosting` records; verifies that database write locks do not block read transactions or trigger deadlocks.
- **P2: Auth Session Expiry Mid-Stream on Long-Polling Kanban:**
  Candidate JWT access token expires while `/api/applications/` is polling or during a drag-and-drop Kanban transition; verifies that client state handles HTTP 401 gracefully without losing uncommitted card state.
- **P3: High-Concurrency 3D Camera Glide + Live DB Ping Polling:**
  Browser switches active modules while `ModuleLayout` fires `/ready` polling; confirms 60 FPS framerate remains stable with zero main-thread hitching from JSON deserialization.
- **P4: Direct ATS Fetching with Corrupted Outbound Career Portals:**
  Third-party career site returns HTTP 503 or DNS failure during `filter_live_jobs_concurrently`; verifies that fallback career URL is generated and the job search response returns with healthy 200.

---

### Tier 4: Real-World End-to-End User Scenarios (>= 5 Scenarios)

1. **Scenario 1: Fresh Graduate Job Hunt Journey**
   - Step 1: Candidate registers and logs into Clear_Hire.AI dashboard.
   - Step 2: Uploads entry-level resume (`student_resume.pdf`).
   - Step 3: Configures preferences: Software Engineer, Bengaluru & Remote, <3 days post age.
   - Step 4: Triggers job search across direct ATS sources (Greenhouse/Lever).
   - Step 5: Matches resume against top 3 job descriptions, verifies keyword match scores >75%.
   - Step 6: Generates tailored 1-page ATS resume variant and downloads PDF.
   - Step 7: Verifies application is automatically tracked in Pipeline Kanban as `pending`.

2. **Scenario 2: Experienced Candidate Direct ATS Pipeline & Outreach**
   - Step 1: Candidate authenticates with existing account holding multiple resume versions.
   - Step 2: Ingests a high-priority Staff Backend Engineer JD via `/jd-analyzer`.
   - Step 3: Reconciled RAG service highlights verified candidate repository achievements.
   - Step 4: System generates personalized hiring manager InMail and recruiter connection note.
   - Step 5: Candidate moves application card to `applied` on `/applications` Kanban.
   - Step 6: Daily briefing digest preview reflects the new active pipeline entry.

3. **Scenario 3: Anti-Ghosting SLA & Grounded Interview Preparation**
   - Step 1: Candidate opens `/applications` view after 15 days of inactivity on an applied role.
   - Step 2: Anti-ghosting SLA detector flags the application as potentially ghosted (>14 days threshold).
   - Step 3: System suggests 3 verified alternative direct ATS openings with active hiring signals.
   - Step 4: Candidate receives invitation for another role and clicks "Generate Interview Pack".
   - Step 5: Grounded interview prep synthesis builds customized technical and behavioral Q&A based exactly on the submitted resume version and JD requirements.

4. **Scenario 4: Mobile Responsive Quick Application Audit**
   - Step 1: User navigates to `/job-hunter` on mobile viewport (375x812 iPhone dimension).
   - Step 2: 3D ambient world renders smoothly at 60 FPS with adaptive camera positioning.
   - Step 3: User filters for direct portal jobs only, excluding staffing agencies.
   - Step 4: User reviews job details, verifies compensation and remote work status.
   - Step 5: User triggers one-click autofill preparation and confirms card appears in Kanban.

5. **Scenario 5: High-Concurrency Burst Load & System Recovery**
   - Step 1: 50 concurrent virtual users execute simultaneous login and token acquisitions.
   - Step 2: All 50 users simultaneously request `/api/applications/` and `/ready`.
   - Step 3: Event loop unblocking ensures all responses return within 1500ms p95 latency.
   - Step 4: Server process RSS memory delta is measured, verifying memory recovers without leaks.
   - Step 5: Health checks confirm zero 5xx server errors and database connection pool health.

---

## 3. Feature Inventory & Mapping

| Feature ID | Feature Name | Source Requirement | Target Architecture / Route | Primary Test Suites |
|---|---|---|---|---|
| F-01 | DB Pool Scaling & Optimization | R1 / PROJECT.md #1 | `backend/app/database.py` (QueuePool 60/40) | `scripts/benchmark_api.py`, `backend/tests/test_stress_load.py` |
| F-02 | Async Event Loop Unblocking | R1 / PROJECT.md #2 | `backend/app/api/resumes.py` (threadpool DB calls) | `scripts/benchmark_api.py`, `backend/tests/test_resumes_endpoints_complete.py` |
| F-03 | Auth Token & Me Query Caching | R1 / PROJECT.md #3 | `backend/app/utils/auth.py` (120s TTL cache) | `backend/tests/test_auth_api.py`, `scripts/benchmark_api.py` |
| F-04 | N+1 Query Consolidation | R1 / PROJECT.md #4 | `backend/app/api/applications.py`, `digest.py` | `backend/tests/test_applications_api.py`, `scripts/benchmark_api.py` |
| F-05 | CacheService Timeout Hardening | R1 / PROJECT.md #5 | `backend/app/services/cache_service.py` (0.2s socket timeout) | `backend/tests/test_cache_service.py` |
| F-06 | LangGraph Workflow Pre-Compilation | R1 / PROJECT.md #6 | `backend/app/services/workflow_service.py` (singleton StateGraph) | `backend/tests/test_matcher_service.py`, `scripts/benchmark_api.py` |
| F-07 | Readiness Ping Caching | R1 / PROJECT.md #7 | `backend/app/main.py` (`/ready` 5s TTL) | `backend/tests/test_api_endpoints.py`, `scripts/benchmark_api.py` |
| F-08 | Persistent 3D Ambient World | R2 / PROJECT.md #8 | `frontend/src/components/ModuleLayout.js`, `ClearHireAmbientWorld.js` | `scripts/benchmark_ui_fps.py`, `frontend/__tests__/ModuleLayout.test.js` |
| F-09 | 6-View 3D Station Mapping | R2 / PROJECT.md #9 | `/`, `/applications`, `/jd-analyzer`, `/job-hunter`, `/resmat-ai`, `/student-lab` | `scripts/benchmark_ui_fps.py` |
| F-10 | Warm Editorial Radar Reskinning | R2 / PROJECT.md #10 | `frontend/src/components/ThreeSpatialRadar.js` (travertine/bronze) | `scripts/benchmark_ui_fps.py` |
| F-11 | Adaptive Mobile Viewport & Touch | R2 / PROJECT.md #11 | Responsive FOV, 375x812 & 1440x900 viewports | `scripts/benchmark_ui_fps.py` |
| F-12 | 60 FPS Framerate Guardrails | R2 / PROJECT.md #12 | Pixel ratio <= 1.5, half-res bloom, RAF pooling | `scripts/benchmark_ui_fps.py` |
| F-13 | UI Brand & Consistency Audit | R3 / PROJECT.md #13 | Visual tokens, palette alignment, typographic scale | Playwright snapshots & UI review |
| F-14 | Automated API Latency Suite | Acceptance / PROJECT.md #14 | `scripts/benchmark_api.py` | Standalone CLI |
| F-15 | Automated UI Framerate Suite | Acceptance / PROJECT.md #15 | `scripts/benchmark_ui_fps.py` | Standalone CLI |

---

## 4. Test Architecture & Execution Guide

### Directory & Harness Layout
```
Clear_Hire.AI/
├── TEST_INFRA.md                          # Authoritative testing specification (this file)
├── pytest.ini                             # Python pytest configuration (testpaths = backend/tests)
├── backend/
│   └── tests/                             # 31 unit, integration, and load test files
│       ├── test_api_endpoints.py
│       ├── test_applications_api.py
│       ├── test_auth_api.py
│       ├── test_resumes_endpoints_complete.py
│       ├── test_stress_load.py            # Integration load suite (@pytest.mark.integration)
│       └── stress_test_harness.py         # Asynchronous concurrent load harness
├── frontend/
│   ├── package.json                       # Next.js 16.4.2, React 19.3.0, Jest 30.5.2
│   └── __tests__/                         # 6 frontend test suites (27 tests)
│       ├── applications.test.js
│       ├── applicationsKanban.test.js
│       ├── client.test.js
│       ├── login.test.js
│       ├── ModuleLayout.test.js
│       └── moduleState.test.js
├── job_automate/                          # 100% SHA-256 byte-for-byte development mirror
│   ├── backend/tests/
│   └── frontend/__tests__/
└── scripts/
    ├── benchmark_api.py                   # Automated API latency & QPS benchmark suite
    └── benchmark_ui_fps.py                # Automated Playwright 60 FPS UI benchmark suite
```

### Execution Commands & Exit Code Contracts

| Suite | Command | Execution Target | Exit Code Contract |
|---|---|---|---|
| **Backend Unit Tests** | `.\.venv\Scripts\pytest -q -m "not integration" backend/tests` | All unit tests in root backend | Exit code `0` on 100% pass (111 tests passing) |
| **Frontend Unit Tests (Root)** | `npm --prefix frontend test -- --watchAll=false` | Jest test suites in root frontend | Exit code `0` on 100% pass (6 suites, 27 tests) |
| **Frontend Unit Tests (Mirror)** | `npm --prefix job_automate/frontend test -- --watchAll=false` | Jest test suites in mirror frontend | Exit code `0` on 100% pass (6 suites, 27 tests) |
| **API Latency Benchmark** | `.\.venv\Scripts\python scripts/benchmark_api.py --concurrency 25 --requests-per-endpoint 20` | Critical backend API endpoints | Exit code `0` if 5xx error rate == 0% and latencies within SLA |
| **API Benchmark Dry-Run** | `.\.venv\Scripts\python scripts/benchmark_api.py --dry-run` | Offline simulated harness self-test | Exit code `0` confirming harness syntax and metrics pipeline |
| **UI 60 FPS Benchmark** | `.\.venv\Scripts\python scripts/benchmark_ui_fps.py --frontend-url http://localhost:3000` | 6 authenticated views across 2 viewports | Exit code `0` if Mean FPS >= 55, 1% Low >= 45, Drops <= 5% |
| **UI Benchmark Mock Mode** | `.\.venv\Scripts\python scripts/benchmark_ui_fps.py --mock` | Offline WebGL RAF telemetry self-test | Exit code `0` confirming Playwright WebGL rendering & math |

---

## 5. Coverage & Performance Pass/Fail Thresholds

| Metric Category | Target Indicator | Baseline Profile | Target SLA / Passing Threshold | Hard Gate Criteria |
|---|---|---|---|---|
| **Unit Test Coverage** | Backend Test Pass Rate | 111 / 111 (100%) | 100% Pass (0 failures) | Any test failure rejects build |
| **Unit Test Coverage** | Frontend Test Pass Rate | 27 / 27 (100%) | 100% Pass (0 failures) | Any test failure rejects build |
| **Mirror Parity** | SHA-256 Parity | 100% byte match | 100% byte match | Any checksum divergence rejects build |
| **API Latency (Match)** | `POST /api/resumes/match` p50 | ~1,200ms | **<= 650ms** | p50 > 1,000ms fails gate |
| **API Latency (Parse)** | `POST /api/resumes/upload` p50 | ~950ms | **<= 500ms** | p50 > 800ms fails gate |
| **API Latency (Search)** | `POST /api/jobs/scrape` p50 | ~7,990ms | **<= 3,500ms** | p50 > 5,000ms fails gate |
| **API Latency (Digest)** | `POST /api/jobs/digest` p50 | ~1,800ms | **<= 900ms** | p50 > 1,500ms fails gate |
| **API Latency (Apps)** | `GET /api/applications/` p50 | ~1,240ms | **<= 350ms** | p50 > 600ms fails gate |
| **API Error Rate** | HTTP 5xx Status Distribution | 0% at <= 25 conc. | **0.0% at 50 concurrency** | Any 5xx error fails gate |
| **Memory Stability** | Server Process RSS Delta | < 35MB | **<= 50MB delta after 1,000 reqs** | Unbounded RSS growth fails gate |
| **UI Mean Framerate** | Mean FPS across 6 views | ~57.5 FPS (synthetic) | **>= 55.0 FPS** | Mean FPS < 50.0 fails gate |
| **UI 1% Low Framerate** | 99th percentile frame delta | ~42.0 FPS | **>= 45.0 FPS** | 1% Low < 35.0 fails gate |
| **UI Dropped Frames** | Inter-frame intervals > 20ms | ~4.5% | **<= 5.0% of total frames** | Dropped frames > 8.0% fails gate |
| **Responsiveness** | Mobile Viewport (375x812) | Unprofiled | **100% Layout Integrity, 60 FPS** | Horizontal overflow or clip fails gate |
