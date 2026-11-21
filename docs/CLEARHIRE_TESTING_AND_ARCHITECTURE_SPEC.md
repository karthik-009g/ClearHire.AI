# ClearHire.AI Testing & Technical Architecture Specification

**Document Version:** 1.1.0  
**Status:** Approved / Spec-Frozen  
**Last Updated:** 2026-11-16  
**Audience:** Technical Leads, Backend/Frontend Engineers, QA Auditors, Site Reliability Engineers  

---

## 1. System Architecture & Topology

### 1.1 Dual-Folder Architecture & Synchronization Discipline
ClearHire.AI operates with a strictly synchronized dual-folder project topology:
- **Root Target**: `frontend/` (Next.js 16.4.2 Pages Router with React 19.3.0) and `backend/` (FastAPI with SQLAlchemy) serving production deployments, CI/CD pipelines, and Docker containers.
- **Development Mirror**: `job_automate/frontend/` and `job_automate/backend/`.
- **Strict Parity Mandate**: 100% byte-for-byte SHA-256 parity is enforced across corresponding source files (`.js`, `.jsx`, `.ts`, `.tsx`, `.py`, `.json`, `.css`). Neither directory is permitted to drift.

### 1.2 Backend Architecture & Concurrency Model
- **Framework & Runtime**: FastAPI on Python 3.11+ managed by Uvicorn.
- **Database Engine & Dual-Dialect Support**:
  - Production: PostgreSQL 15+ with `pgvector` extension for 384-dimensional cosine similarity indexing.
  - Automated Testing: In-memory SQLite with `StaticPool` (`sqlite://`, `check_same_thread=False`), with schema initialized via `Base.metadata.create_all(bind=engine)` per session.
- **Connection Pool Configuration**:
  - `QueuePool` configured with `pool_size=30`, `max_overflow=20`, `pool_timeout=30.0`, and `pool_recycle=1800` in `app/database.py`, preventing queue starvation during concurrent bursts.
- **Event-Loop Non-Blocking Architecture**: Heavy CPU-bound or blocking I/O operations (file hashing via SHA-256, spaCy NLP entity extraction, SentenceTransformer embeddings, PDF ReportLab compilation, and database readiness probes `engine.connect()`) are strictly offloaded from the asyncio event loop via `starlette.concurrency.run_in_threadpool`.
- **NLP & Embeddings**: spaCy `en_core_web_sm` pipeline for entity extraction and `SentenceTransformer` (`all-MiniLM-L6-v2`, dimensions configured via `settings.embedding_dimensions = 384`, model pre-loading governed by `settings.embedding_load_local_model = True`).
- **Caching**: Process-level thread-safe `CacheService` with TTL (default 900s) preventing repetitive network requests across 22 direct ATS providers.
- **Rate Limiting**: Thread-safe in-memory sliding window rate limiter guarded by `threading.Lock()` returning `429 Too Many Requests` when quota is exceeded.
- **Global Error Handling**: Custom exception handlers in `app.main:app` intercepting `TimeoutError` (503 Service Unavailable), `SQLAlchemyError` (503 Database Unavailable), `StarletteHTTPException`, and `RequestValidationError` (422 Unprocessable Entity), eliminating unhandled 500 crashes and propagating `X-Request-ID` telemetry headers.

### 1.3 Frontend Architecture & Design Language
- **Framework**: Next.js 16.4.2 with React 19.3.0 and Tailwind CSS 3.3.
- **Styling Tokens**: Light stone architectural aesthetic (`#f6f4ee` canvas background, `#faf7f0` tactile card panels, `#eeece2` border accents, `#24231f` primary typography, `#15803d` emerald success accent, `#5369d9` cobalt interactive accent, Newsreader serif, JetBrains Mono).
- **Session Model**: Client-side bearer token management via `localStorage` and `src/api/client.js` in-memory cache. Reverse-proxy `/api/*` routing to FastAPI backend (`http://localhost:8000`).

---

## 2. Public and Internal API Contracts

### 2.1 Jobs API (`/api/jobs`)
| Method | Path | Request Body | Success Code | Response Model | Description |
|---|---|---|---|---|---|
| `POST` | `/api/jobs/scrape` | `ScrapeJobsRequest` | `200 OK` | `ScrapeJobsResponse` | Scrapes target sources and corporate ATS portals; applies ghosting risk filtering and persistence. |
| `GET` | `/api/jobs/preferences` | None | `200 OK` | `PreferencesResponse` | Retrieves user job preferences or defaults if unconfigured. |
| `POST` | `/api/jobs/preferences` | `PreferencesRequest` | `200 OK` | `PreferencesResponse` | Upserts candidate preferences including notice period, CTC, and target companies. |
| `POST` | `/api/jobs/digest` | `DigestRequest` | `200 OK` | `DigestResponse` | Ranks matched jobs against latest resume embedding and dispatches email digest. |

- **`ScrapeJobsRequest`**: `sources: list[str]`, `keywords: list[str]`, `locations: list[str] | None`, `target_companies: list[str] | None`, `direct_portals_only: bool`, `posted_within_hours: int | None`.
- **`PreferencesRequest`**: `preferred_email: EmailStr`, `target_role: str`, `locations: list[str]`, `keywords: list[str]`, `target_companies: list[str]`, `notice_period_days: int | None`, `serving_notice: bool`, `current_ctc_lpa: float | None`, `expected_ctc_lpa: float | None`, `direct_portals_only: bool`.

### 2.2 Resumes API (`/api/resumes`)
| Method | Path | Request Body | Success Code | Response Model | Description |
|---|---|---|---|---|---|
| `POST` | `/api/resumes/upload` | `multipart/form-data` | `200 OK` | `ResumeUploadResponse` | Validates file security (magic bytes, extension), stores artifact, parses AST, and generates embedding. |
| `GET` | `/api/resumes/{id}/versions` | None | `200 OK` | `ResumeVersionsResponse` | Lists chronological versions for a candidate resume sorted by `version_no.asc()`. |
| `GET` | `/api/resumes/{id}/download` | None | `200 OK` | Binary stream | Downloads raw stored resume file with `Content-Disposition: attachment; filename="..."`. |
| `POST` | `/api/resumes/cleanup-expired` | None | `200 OK` | `CleanupResponse` | Enforces data retention SLA by deleting expired resume files and DB records. |
| `GET` | `/api/resumes/{id}/versions/{v}/export-pdf` | None | `200 OK` | PDF stream | Compiles ATS-optimized single-page PDF with ReportLab (`Content-Disposition: inline; filename="resume_{id}_v{v}.pdf"`). |

### 2.3 Applications API (`/api/applications`)
| Method | Path | Request Body | Success Code | Response Model | Description |
|---|---|---|---|---|---|
| `GET` | `/api/applications` | None | `200 OK` | `list[dict]` | Retrieves all tracked job applications with associated JD and resume version details. |
| `PATCH` | `/api/applications/{id}/status` | `dict` (`status`, `notes`) | `200 OK` | `dict` | Transitions pipeline state (`pending`, `applied`, `screening`, `interviewing`, `offer`, `rejected`, `ghosted`). |
| `GET` | `/api/applications/{id}/interview-prep` | None | `200 OK` | `InterviewPrepPack` | Synthesizes grounded interview prep pack from application's exact resume version and job description. |
| `POST` | `/api/applications/{id}/outreach` | None | `200 OK` | `dict` | Generates AI recruiter InMail, LinkedIn short note, and follow-up templates. |

- **`InterviewPrepPack` Schema**:
  ```json
  {
    "application_context": {
      "role": "string",
      "company": "string",
      "resume_version": 1
    },
    "grounding_note": "string",
    "method": "Deterministic term matching and excerpt retrieval",
    "resume_evidence": [{"requirement": "string", "found_in_resume": true, "resume_excerpt": "string"}],
    "requirements_to_prepare": [{"requirement": "string", "found_in_resume": false}],
    "technical_questions": [{"requirement": "string", "question": "string", "coaching": "string"}],
    "behavioral_questions": ["string"],
    "recruiter_screen_india": {
      "notice_period_days": 30,
      "serving_notice": true,
      "current_ctc_lpa": 38.0,
      "expected_ctc_lpa": 52.0,
      "work_mode": "Hybrid",
      "preferred_locations": ["Bengaluru"],
      "confirm_before_sharing": true,
      "guidance": "string"
    },
    "practice_steps": ["string"]
  }
  ```

### 2.4 Public Scoped API (`/api/public`)
| Method | Path | Auth Header | Success Code | Response Model | Description |
|---|---|---|---|---|---|
| `POST` | `/api/public/keys` | Optional Bearer | `200 OK` | `APIKeyResponse` | Generates cryptographically secure API key with defined scopes (`read`, `write`). |
| `GET` | `/api/public/keys` | Optional Bearer | `200 OK` | `list[APIKeyResponse]` | Lists active API keys. |
| `POST` | `/api/public/keys/{id}/revoke` | Optional Bearer | `200 OK` | `dict` | Revokes API key immediately. |
| `GET` | `/api/public/whoami` | `X-API-Key: ch_...` | `200 OK` | `dict` (`key_id`, `scopes`) | Validates API key and verifies `read` scope. |

- **Key Cryptography & Storage Contract**:
  - Raw Key Generation: `raw_key = f"ch_{secrets.token_urlsafe(32)}"`
  - Storage Hash: `key_hash = hashlib.sha256(raw_key.encode('utf-8')).hexdigest()`
  - Identifier Model: Database row has integer primary key `id: int` for administrative routing, and public string identifier `key_id: str` (UUID4) returned in `whoami` payload.

---

## 3. Testing Tiers & Quality Assurance Standards

### 3.1 Repository Test File Inventory
The test suites are co-located and mirrored across both folder trees:
```
backend/tests/ & job_automate/backend/tests/:
├── test_api_endpoints.py
├── test_applications_api.py
├── test_applications_interview_prep.py     [M4 New]
├── test_auth_api.py
├── test_authenticity_service.py
├── test_background_jobs.py
├── test_cache_service.py
├── test_digest_api.py
├── test_direct_ats_service.py
├── test_evaluation_metrics.py
├── test_job_scraper_service.py
├── test_jobs_endpoints.py                 [M4 New]
├── test_jobs_preferences.py
├── test_matcher_service.py
├── test_notification_digest_service.py
├── test_parser_service.py
├── test_pdf_generator_service.py
├── test_production_config.py
├── test_production_observability.py
├── test_public_api_complete.py            [M4 New]
├── test_public_api_foundation.py
├── test_rag_service.py
├── test_rate_limit_hardening.py
├── test_recruiter_outreach_service.py
├── test_resumes_endpoints_complete.py     [M4 New]
├── test_screener_answer_service.py
├── test_storage_provider.py
├── test_tailor_service.py
└── test_upload_security.py

frontend/__tests__/ & job_automate/frontend/__tests__/:
├── applications.test.js
├── applicationsKanban.test.js              [M4 New]
├── client.test.js
├── login.test.js                           [M4 New]
├── ModuleLayout.test.js                    [M4 New]
└── moduleState.test.js
```

### 3.2 Canonical Verification Commands
1. **Root Backend Test Suite**:
   ```powershell
   .\.venv\Scripts\pytest -q backend/tests
   ```
2. **Mirror Backend Test Suite**:
   ```powershell
   .\.venv\Scripts\pytest -q job_automate/backend/tests
   ```
3. **Root Frontend Test Suite**:
   ```powershell
   npm --prefix frontend test -- --watchAll=false
   ```
4. **Mirror Frontend Test Suite**:
   ```powershell
   npm --prefix job_automate/frontend test -- --watchAll=false
   ```

### 3.3 Testing Tiers Breakdown
- **Tier 1 (Unit & Services)**: Pure Python and JavaScript unit tests verifying parsing algorithms, AST generation, tokenization, and vector cosine calculations without external side-effects.
- **Tier 2 (API Integration)**: Comprehensive route integration tests using `FastAPI.testclient.TestClient` with in-memory SQLite dependency overrides. Verifies status codes 200, 201, 400, 401, 403, 404, 409, 422, and 503.
- **Tier 3 (Frontend RTL Component & Route)**: React Testing Library suites verifying user interactions, accessibility roles, unauthenticated redirects, layout styling, form validation, and modal workflows.
- **Tier 4 (Contract & Dual-Folder Parity)**: Automated SHA-256 hash comparison across all files in `backend/` vs `job_automate/backend/` and `frontend/` vs `job_automate/frontend/`.

---

## 4. Reliability, SLAs & Error Handling Standards

### 4.1 Anti-Ghosting SLA Protocol
- Applications in `applied` or `screening` status with no employer activity for 14+ calendar days are automatically flagged with `ghosting_risk: "high"`.
- Daily briefing digest surfaces ghosting alerts with 1-click follow-up dispatch.

### 4.2 Latency & Concurrency Budgets
- Fast metadata endpoints (`/health`, `/ready`, `/api/jobs/preferences`, `/api/public/whoami`): p95 < 50ms, p99 < 150ms.
- Heavy computational endpoints (`/api/resumes/upload`, `/api/jobs/scrape`, `/api/jobs/digest`): p95 < 1200ms, p99 < 2500ms under 25 concurrent clients.
- Memory leak tolerance: 0% memory growth over 10,000 synthetic requests. Zero unhandled 5xx exceptions.
