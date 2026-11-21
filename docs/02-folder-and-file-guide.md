# ClearHire.AI — Folder and File Guide

> **Target Audience**: Final-year Computer Science / AI-ML engineering student onboarding onto the codebase.  
> **Rule**: Every file is mapped with its concrete purpose, exports, callers, and a "Touch this when..." note. Every threshold/constant cites exact `file:line`. All paths are relative.

---

## 1. High-Level Workspace Architecture

```text
ClearHire.AI/
├── .github/workflows/          # GitHub Actions CI pipelines
├── backend/
│   ├── alembic/                # Database migrations (10 versions)
│   ├── app/
│   │   ├── api/                # FastAPI endpoint routers and Pydantic schemas
│   │   ├── evaluation/         # RAG evaluation benchmark harness & labeled datasets
│   │   ├── models/             # SQLAlchemy ORM models (Users, Resumes, Jobs, Vector)
│   │   ├── services/           # Business logic, AI/ML engines, scrapers, schedulers
│   │   ├── utils/              # Configuration, rate limiting, JWT auth, file security
│   │   ├── database.py         # SQLAlchemy engine, session maker, base model
│   │   └── main.py             # FastAPI ASGI application root
│   ├── storage/resumes/        # Local disk file store for uploaded/generated resumes
│   ├── tests/                  # Pytest test suite (117 collected items: 111 passed, 6 skipped integration)
│   ├── alembic.ini             # Alembic configuration
│   ├── pytest.ini              # Pytest configuration & asyncio test modes
│   └── requirements.txt        # Pinned backend dependencies
├── frontend/
│   ├── src/
│   │   ├── api/                # Axios API client functions matching backend routes
│   │   ├── components/         # 2D and 3D UI components (ModuleLayout, Three.js)
│   │   │   ├── autonomy/       # Autonomous 3D visualizers (Tailor, Hunter, Sentinel)
│   │   │   └── office/         # 3D spatial office meshes and PBR shaders
│   │   ├── lib/                # React context, sound engine, virtual scrolling
│   │   ├── pages/              # Next.js Pages router endpoints
│   │   └── styles/             # Tailwind CSS & 3D WebGL overlay rules
│   ├── __tests__/              # Jest frontend test suite (6 suites, 27 tests)
│   ├── package.json            # Pinned frontend dependencies (Next 16, React 19)
│   └── tsconfig.json           # Path resolution & compiler settings
├── docs/                       # Comprehensive onboarding & architectural documentation
├── .env.example                # Canonical environment template
└── job_automate/               # Legacy mirror folder (Technical Debt preserved for CI)
```

---

## 2. Root & CI/CD Configuration

### `.github/workflows/backend-tests.yml`
- **Purpose**: Runs the backend test suite on pull requests and pushes to `main`.
- **Depends On**: Python 3.11, [requirements.txt](../backend/requirements.txt).
- **Technical Debt**: Line 14 sets `working-directory: job_automate/backend`.
- **Touch this when...**: Updating CI triggers, changing Python versions, or fixing the hardcoded `job_automate/` path.

### `.github/workflows/frontend-build.yml`
- **Purpose**: Builds and verifies the Next.js frontend on pull requests.
- **Depends On**: Node.js, [package.json](../frontend/package.json).
- **Technical Debt**: Line 27 sets `node-version: '20'`, while `package.json` specifies `"node": ">=24.0.0"`. Line 14 sets `working-directory: job_automate/frontend`.
- **Touch this when...**: Aligning Node versions across CI and local dev or updating build steps.

### `pytest.ini`
- **Purpose**: Sets global pytest flags, python paths (`pythonpath = . backend`), and `asyncio_mode = strict`.
- **Touch this when...**: Adding test plugins, configuring coverage thresholds, or modifying async runners.

### `.env.example`
- **Purpose**: Canonical environment configuration template providing defaults for SQLite/PostgreSQL, JWT secrets, retention policies, and RAG thresholds.
- **Touch this when...**: Adding new environment variables to [config.py](../backend/app/utils/config.py).

---

## 3. Backend: Core & Database Engine

### [`backend/app/main.py`](../backend/app/main.py)
- **Purpose**: ASGI application bootstrap. Initializes FastAPI, configures CORS middleware, registers global exception handlers, manages lifespan startup/shutdown (starts `APScheduler`), and mounts all API routers.
- **Exports**: `app: FastAPI`.
- **Callers**: `uvicorn` server runner, `backend/start_backend.ps1`, pytest fixtures.
- **Touch this when...**: Mounting a new top-level API router, registering global middleware, or modifying application startup/shutdown hooks.

### [`backend/app/database.py`](../backend/app/database.py)
- **Purpose**: Database engine initialization, declarative base creation, and DB session lifecycle dependency.
- **Exports**: `engine`, `SessionLocal`, `Base`, `get_db()`.
- **Callers**: Every API route and background service requiring database access.
- **Touch this when...**: Changing connection pooling options, switching database dialects (PostgreSQL vs SQLite), or modifying session commit/rollback patterns.

---

## 4. Backend: API Layer (`backend/app/api/`)

### [`backend/app/api/resumes.py`](../backend/app/api/resumes.py)
- **Purpose**: Resume lifecycle endpoints: file upload, text extraction, parsing into structured skills, 60/40 matching against JDs, 1-page resume tailoring, version history listing, and PDF compilation.
- **Exports**: FastAPI router mounted at `/api/resumes`.
- **Callers**: [api/resumes.js](../frontend/src/api/resumes.js), `ResmatAI` module.
- **Touch this when...**: Adding new file formats for upload, altering resume retention policies, or adding custom export formats.

### [`backend/app/api/jobs.py`](../backend/app/api/jobs.py)
- **Purpose**: Requisition sourcing, preference management, and resume-to-job matching endpoints. Supports direct ATS scraping, recruiter authenticity scoring, and liveness filtering.
- **Exports**: FastAPI router mounted at `/api/jobs`.
- **Callers**: [api/jobs.js](../frontend/src/api/jobs.js), `JobHunterModule.js`, `JDAnalyzerModule.js`.
- **Touch this when...**: Adding new job filters, changing candidate preference schemas, or modifying job scrape triggers.

### [`backend/app/api/applications.py`](../backend/app/api/applications.py)
- **Purpose**: Finite state machine for application tracking (`draft` → `pending` → `review_required` → `reviewed` → `applied`), autofill payload generation, submission confirmation, 14-day ghosting alerts ([line 85](../backend/app/api/applications.py#L85)), recruiter outreach generation, and grounded interview prep packs.
- **Exports**: FastAPI router mounted at `/api/applications`.
- **Callers**: [api/applications.js](../frontend/src/api/applications.js), `ApplicationsModule.js`.
- **Touch this when...**: Adding new Kanban status columns, modifying the status transition matrix ([lines 42-54](../backend/app/api/applications.py#L42-L54)), or altering rate limits (10 apps/hour at line 276).

### [`backend/app/api/auth.py`](../backend/app/api/auth.py)
- **Purpose**: Candidate authentication and profile management. Provides `/register`, `/login` with auto-provisioning, `/me` profile updates, and `/account` deletion cascading across stored files, resumes, and applications.
- **Exports**: FastAPI router mounted at `/api/auth`.
- **Callers**: [api/auth.js](../frontend/src/api/auth.js), [pages/login.js](../frontend/src/pages/login.js), [moduleState.js](../frontend/src/lib/moduleState.js).
- **Touch this when...**: Changing password hashing algorithms, adjusting JWT token expiration, or adding OAuth / SSO providers.

### [`backend/app/api/digest.py`](../backend/app/api/digest.py)
- **Purpose**: Candidate notification and recruitment funnel analytics. Generates morning summary digests of high-match jobs and aggregates application conversion rates across pipeline stages.
- **Exports**: FastAPI router mounted at `/api/digest`.
- **Callers**: [api/digest.js](../frontend/src/api/digest.js), `FunnelAnalyticsModule.js`.
- **Touch this when...**: Adding funnel metrics, altering email notification layouts, or customizing digest scoring thresholds.

### [`backend/app/api/public_api.py`](../backend/app/api/public_api.py)
- **Purpose**: External developer API (`/api/v1`) with API key generation, revocation, and scope validation (`read`, `write`, `admin`).
- **Exports**: FastAPI router mounted at `/api/v1`.
- **Callers**: Third-party integrations, external browser extensions.
- **Touch this when...**: Exposing new public endpoints for external developers or modifying API key rate limits.

---

## 5. Backend: Data Models (`backend/app/models/`)

| Model File | Key Classes | Table Names | Purpose | Touch this when... |
|---|---|---|---|---|
| [`user.py`](../backend/app/models/user.py) | `User`, `UserPreference` | `users`, `user_preferences` | Stores credentials, profile data, job search filters, notice periods, and schedule preferences. | Adding user profile fields or candidate preference criteria. |
| [`resume.py`](../backend/app/models/resume.py) | `Resume`, `ResumeVersion`, `JobDescription` | `resumes`, `resume_versions`, `job_descriptions` | Stores uploaded resumes, parsed JSON summaries, version history, dense vector embeddings, and analyzed JDs. | Altering resume storage structures or versioning logic. |
| [`jobs.py`](../backend/app/models/jobs.py) | `JobPosting`, `Application`, `ApplicationSubmissionLog` | `job_postings`, `applications`, `application_submission_logs` | Stores scraped jobs with embeddings, tracked job applications, and immutable audit logs of application reviews/submissions. | Adding job metadata fields, ATS identifiers, or application audit actions. |
| [`api_key.py`](../backend/app/models/api_key.py) | `ApiKey` | `api_keys` | Stores hashed API keys, user associations, scopes, and revocation flags. | Modifying API security or authorization scopes. |
| [`vector_type.py`](../backend/app/models/vector_type.py) | `VectorType` | N/A (SQLAlchemy Type) | Dynamic vector abstraction: uses native `pgvector.sqlalchemy.Vector` on PostgreSQL and JSON text serialization on SQLite. | Supporting alternative vector stores or changing vector serialization. |

---

## 6. Backend: AI/ML, Sourcing & Business Services (`backend/app/services/`)

### [`matcher_service.py`](../backend/app/services/matcher_service.py)
- **Purpose**: Core hybrid matching engine. Computes a weighted keyword overlap score and a dense semantic cosine similarity score using `sentence-transformers/all-MiniLM-L6-v2` (384 dimensions at [line 77](../backend/app/services/matcher_service.py#L77)). Blends scores into a final match rating using a strict **60% lexical / 40% embedding** split ([line 293](../backend/app/services/matcher_service.py#L293)). Applies a 1.7x multiplier to 51 curated technical keywords ([lines 17-48, 167](../backend/app/services/matcher_service.py#L17-L48)), 1.5x to phrases ([line 169](../backend/app/services/matcher_service.py#L169)), and 1.0x to standard words ([line 170](../backend/app/services/matcher_service.py#L170)).
- **Exports**: `ResumeMatcherService`.
- **Callers**: [api/resumes.py](../backend/app/api/resumes.py), [api/jobs.py](../backend/app/api/jobs.py), [rag_service.py](../backend/app/services/rag_service.py), [run_evaluation.py](../backend/app/evaluation/run_evaluation.py).
- **Touch this when...**: Adjusting scoring weights, tuning the 51-keyword dictionary, or upgrading the embedding model.

### [`parser_service.py`](../backend/app/services/parser_service.py)
- **Purpose**: Deterministic resume parsing pipeline. Extracts raw text from PDF (PyPDF2) and DOCX (python-docx), cleans Unicode artifacts, and uses `spaCy` (`en_core_web_sm`) along with regex patterns to extract contact details, structured skills, education, and work experience.
- **Exports**: `ResumeParserService`.
- **Callers**: [api/resumes.py](../backend/app/api/resumes.py), [automation_service.py](../backend/app/services/automation_service.py).
- **Touch this when...**: Improving contact information extraction, adding new skill categories, or handling edge-case resume layouts.

### [`rag_service.py`](../backend/app/services/rag_service.py)
- **Purpose**: Reconciled Retrieval-Augmented Generation engine. Executes dense vector retrieval over `job_postings` in PostgreSQL `pgvector` using cosine distance `<=>` ([line 89](../backend/app/services/rag_service.py#L89)) combined with string-matched candidate resume evidence. Evaluates snippets against `rag_similarity_threshold: 0.35` ([config.py:66](../backend/app/utils/config.py#L66), [line 312](../backend/app/services/rag_service.py#L312)) for `strong_evidence_count`, checks conflicting evidence margins (`<= 0.03` at [lines 270-272](../backend/app/services/rag_service.py#L270-L272)), and gates final confidence against `rag_abstain_threshold: 0.55` ([config.py:67](../backend/app/utils/config.py#L67), [line 414](../backend/app/services/rag_service.py#L414)), marking `abstained = True` with status `low_confidence` if unsupported.
- **Exports**: `ReconciledRAGService`.
- **Callers**: [api/jobs.py](../backend/app/api/jobs.py), [run_evaluation.py](../backend/app/evaluation/run_evaluation.py).
- **Touch this when...**: Tuning RAG abstention thresholds (0.35 snippet vs 0.55 composite), modifying evidence reconciliation prompts, or changing vector similarity metrics.

### [`workflow_service.py`](../backend/app/services/workflow_service.py)
- **Purpose**: LangGraph-orchestrated resume analysis pipeline. Compiles a 2-node linear `StateGraph` (`parse_step` -> `match_step` -> `END` at [lines 30-60](../backend/app/services/workflow_service.py#L30-L60)) that chains deterministic parsing and 60/40 hybrid matching into an auditable state object.
- **Exports**: `run_resume_analysis_flow()`, `ResumeAnalysisState`.
- **Callers**: [api/resumes.py:255, 280](../backend/app/api/resumes.py#L255).
- **Touch this when...**: Adding new steps (e.g. ATS optimization, formatting linting) to the LangGraph pipeline.

### [`email_service.py`](../backend/app/services/email_service.py)
- **Purpose**: Synchronous notification dispatcher built on Python's standard library `smtplib.SMTP` ([line 33](../backend/app/services/email_service.py#L33)). Formats and sends HTML morning digests and ghosting alerts. Telegram and WhatsApp channels present in the `UserPreference` schema are currently unrouted model columns.
- **Exports**: `EmailService`, `send_email()`.
- **Callers**: [notification_digest_service.py](../backend/app/services/notification_digest_service.py), [scheduler_service.py](../backend/app/services/scheduler_service.py).
- **Touch this when...**: Configuring SMTP credentials, customizing HTML digest email templates, or implementing real WhatsApp/Telegram providers.

### [`tailor_service.py`](../backend/app/services/tailor_service.py)
- **Purpose**: Resume customization engine enforcing physical single-page constraints: maximum 48 lines ([line 10](../backend/app/services/tailor_service.py#L10)), maximum 620 words ([line 11](../backend/app/services/tailor_service.py#L11)), and maximum 24 words per bullet point ([line 12](../backend/app/services/tailor_service.py#L12)). Re-aligns existing candidate experience with target job keywords while flagging unsupported skills as `review_required` rather than fabricating achievements.
- **Exports**: `ResumeTailorService`.
- **Callers**: [api/resumes.py](../backend/app/api/resumes.py), `ResmatAI` module.
- **Touch this when...**: Changing resume length constraints, modifying bullet restructuring logic, or adjusting cover letter generation.

### [`direct_ats_service.py`](../backend/app/services/direct_ats_service.py)
- **Purpose**: First-party requisition scraper querying official public API endpoints for **Greenhouse, Lever, and Ashby**. Maintains a curated registry of 17 tech companies ([lines 60-80](../backend/app/services/direct_ats_service.py#L60-L80)), strips HTML payloads, filters by location (India/Remote keywords at line 82), and caches results for 900 seconds (15 minutes at line 332).
- **Exports**: `DirectAtsService`, `CURATED_ATS_REGISTRY`.
- **Callers**: [api/jobs.py](../backend/app/api/jobs.py), [api/applications.py](../backend/app/api/applications.py), [automation_service.py](../backend/app/services/automation_service.py).
- **Touch this when...**: Adding new companies to the ATS registry, adding support for new ATS platforms, or modifying ATS cache TTL.

### [`liveness_service.py`](../backend/app/services/liveness_service.py)
- **Purpose**: Job link verification and dead link filter. Performs concurrent HTTP stream requests (ThreadPoolExecutor) checking for HTTP 404/410 codes, expired redirects, and scans the first 8192 bytes ([line 159](../backend/app/services/liveness_service.py#L159)) for 12 closure phrases ([lines 56-69](../backend/app/services/liveness_service.py#L56-L69)). Provides 34 verified fallback official career portals ([lines 19-54](../backend/app/services/liveness_service.py#L19-L54)).
- **Exports**: `verify_job_url()`, `filter_live_jobs_concurrently()`, `get_company_fallback_career_url()`.
- **Callers**: [api/jobs.py](../backend/app/api/jobs.py), [api/applications.py](../backend/app/api/applications.py).
- **Touch this when...**: Adding closure detection phrases, registering fallback career URLs, or tuning verification timeouts.

### [`authenticity_service.py`](../backend/app/services/authenticity_service.py)
- **Purpose**: Recruiter and posting authenticity scoring engine. Evaluates listings on a 0-100 scale starting from a base score of 50.0 ([line 173](../backend/app/services/authenticity_service.py#L173)), applying bonuses for verified direct ATS (+35.0 at line 176) and company career portals (+25.0 at line 181), and deducting penalties for staffing agencies (-40.0 at line 194).
- **Exports**: `JobAuthenticityService`.
- **Callers**: [api/jobs.py](../backend/app/api/jobs.py), `JobHunterModule.js`.
- **Touch this when...**: Updating agency keyword blocklists or tuning authenticity weight parameters.

### [`scheduler_service.py`](../backend/app/services/scheduler_service.py)
- **Purpose**: Background execution engine utilizing APScheduler `BackgroundScheduler`. Manages per-user cron triggers for automated scraping, morning digests, and runs automation passes on user login or resume upload events.
- **Exports**: `start_scheduler()`, `stop_scheduler()`, `sync_user_schedule()`, `run_on_login()`, `run_on_upload()`.
- **Callers**: [main.py](../backend/app/main.py) lifespan, [api/auth.py](../backend/app/api/auth.py), [api/resumes.py](../backend/app/api/resumes.py).
- **Touch this when...**: Changing background execution intervals or adding new automated trigger events.

### [`interview_prep_service.py`](../backend/app/services/interview_prep_service.py)
- **Purpose**: Generates grounded interview preparation kits from the exact resume version and job description used for an application. Produces technical deep dives, behavioral STAR questions, and company cultural insights.
- **Exports**: `InterviewPrepService`.
- **Callers**: [api/applications.py](../backend/app/api/applications.py).
- **Touch this when...**: Customizing interview question generation prompts or adding question categories.

### [`recruiter_outreach_service.py`](../backend/app/services/recruiter_outreach_service.py)
- **Purpose**: Generates customized recruiter communications: InMail messages, LinkedIn connection notes strictly under 300 characters ([line 140](../backend/app/services/recruiter_outreach_service.py#L140)), and follow-up emails grounded in candidate highlights.
- **Exports**: `RecruiterOutreachService`.
- **Callers**: [api/applications.py](../backend/app/api/applications.py).
- **Touch this when...**: Modifying outreach templates or tuning tone and character constraints.

### [`screener_answer_service.py`](../backend/app/services/screener_answer_service.py)
- **Purpose**: Detects the intent of employer screener questions (e.g. notice period, compensation/CTC, work authorization, motivation) and generates grounded answers from candidate preferences and resume summary.
- **Exports**: `ScreenerAnswerService`.
- **Callers**: [api/applications.py](../backend/app/api/applications.py).
- **Touch this when...**: Adding new screener intent categories or refining answer synthesis logic.

### [`pdf_generator_service.py`](../backend/app/services/pdf_generator_service.py)
- **Purpose**: Programmatic PDF compiler built on ReportLab. Calculates exact typographic leading, margins, and section spacing to guarantee single-page rendering.
- **Exports**: `generate_resume_pdf()`.
- **Callers**: [api/resumes.py](../backend/app/api/resumes.py).
- **Touch this when...**: Modifying resume visual styling, typography, margins, or color palettes.

---

## 7. Backend: Evaluation Suite (`backend/app/evaluation/`)

### [`run_evaluation.py`](../backend/app/evaluation/run_evaluation.py)
- **Purpose**: In-memory SQLite evaluation harness. Replays test datasets against the `ReconciledRAGService`, computing Precision@K, hallucination rates, and abstention compliance without requiring external databases.
- **Exports**: CLI entrypoint `main()`, `run()`.
- **Touch this when...**: Adding new evaluation metrics or running automated regression tests against RAG prompt changes.

### [`metrics.py`](../backend/app/evaluation/metrics.py)
- **Purpose**: Statistical metric calculators: match accuracy, precision at K, hallucination rate, abstain rate, and P95 latency via 100-quantile interpolation ([line 14](../backend/app/evaluation/metrics.py#L14)).
- **Exports**: `compute_metrics()`, `latency_p95_ms()`.
- **Touch this when...**: Modifying statistical calculation formulas or quantile boundaries.

### [`datasets/reconciled_match_eval_20.json`](../backend/app/evaluation/datasets/reconciled_match_eval_20.json)
- **Purpose**: Ground-truth benchmark dataset with 20 labeled candidate-job pairs and 24 monitored technical hallucination terms ([lines 3-28](../backend/app/evaluation/datasets/reconciled_match_eval_20.json#L3-L28)).
- **Touch this when...**: Expanding benchmark coverage or adding new domain skill terms.

---

## 8. Frontend: Pages & State Layer (`frontend/src/`)

### [`pages/index.js`](../frontend/src/pages/index.js)
- **Purpose**: Root application page dynamically loading `ModuleLayout` with SSR disabled to ensure WebGL canvas compatibility.
- **Exports**: Next.js default page component.
- **Touch this when...**: Changing root page metadata or default landing redirects.

### [`pages/login.js`](../frontend/src/pages/login.js)
- **Purpose**: Dedicated candidate authentication page with sign-in, account creation, and demo credential auto-fill buttons.
- **Touch this when...**: Modifying login branding, error handling, or authentication redirects.

### [`lib/moduleState.js`](../frontend/src/lib/moduleState.js)
- **Purpose**: Centralized React Context providing global state across all modules: current active tab, authenticated candidate profile, uploaded resumes, application lists, and system notifications.
- **Exports**: `ModuleStateContext`, `ModuleStateProvider`, `useModuleState()`.
- **Touch this when...**: Adding new global state variables, sharing state between modules, or managing user session persistence.

### [`api/client.js`](../frontend/src/api/client.js)
- **Purpose**: Configured Axios instance with baseURL (`http://127.0.0.1:8000`), automatic Bearer JWT token injection from `localStorage`, and response error interceptors.
- **Exports**: `apiClient`, `setAuthToken()`.
- **Touch this when...**: Changing API endpoints, adding request headers, or handling global 401 unauthenticated redirects.

---

## 9. Frontend: 3D Spatial UI & Modules (`frontend/src/components/`)

### [`ModuleLayout.js`](../frontend/src/components/ModuleLayout.js)
- **Purpose**: Core 2D/3D orchestrator. Mounts the `ClearHireStoryEngine` 3D background canvas, top navigation header with user profile, module navigation tabs (`job-hunter`, `jd-analyzer`, `resmat-ai`, `applications`, `student-lab`, `funnel-analytics`), and renders the active module container.
- **Touch this when...**: Adding new workspace modules, modifying navigation headers, or adjusting responsive layouts.

### [`ClearHireStoryEngine.js`](../frontend/src/components/ClearHireStoryEngine.js)
- **Purpose**: Three.js WebGL canvas engine. Defines 3D spatial waypoints for each module, renders ambient lighting, animated grid floors, particle clouds, and controls camera spring physics as the candidate switches between modules.
- **Touch this when...**: Adjusting camera angles, modifying 3D scene lighting, or adding 3D office meshes.

### Autonomous 3D Visualizers (`frontend/src/components/autonomy/`)
- **`ASTTailorAutonomy.js`**: Renders real-time 3D visual feedback for resume AST parsing and tailoring.
- **`ATSHunterAutonomy.js`**: Renders 3D radar scanning animations representing active ATS job requisition sweeps.
- **`SLASentinelAutonomy.js`**: Renders 3D visual indicators for the 14-day application ghosting sentinel.
- **Touch these when...**: Enhancing visual 3D feedback for AI background processes.

---

## 10. "Where Do I Look to Change X?" (Developer Quick Reference)

| If you need to change or fix... | Open these files |
|---|---|
| **Scoring formula (e.g. adjust 60/40 blend)** | [matcher_service.py:293](../backend/app/services/matcher_service.py#L293) |
| **Direct ATS company endpoints or tokens** | [direct_ats_service.py:60-80](../backend/app/services/direct_ats_service.py#L60-L80) |
| **Liveness closure keywords or portals** | [liveness_service.py:19-69](../backend/app/services/liveness_service.py#L19-L69) |
| **Resume 1-page limits (lines, words)** | [tailor_service.py:10-12](../backend/app/services/tailor_service.py#L10-L12) |
| **RAG snippet threshold (0.35) or abstention (0.55)** | [config.py:66-68](../backend/app/utils/config.py#L66-L68), [rag_service.py:270, 312, 414](../backend/app/services/rag_service.py#L270) |
| **Application status transitions / rules** | [applications.py:42-54](../backend/app/api/applications.py#L42-L54) |
| **Database schemas or migrations** | [backend/alembic/versions/](../backend/alembic/versions/) |
| **Frontend tab routing or module display** | [ModuleLayout.js](../frontend/src/components/ModuleLayout.js) |
| **3D spatial camera angles or animations** | [ClearHireStoryEngine.js](../frontend/src/components/ClearHireStoryEngine.js) |
| **API Base URL or JWT Authorization header**| [client.js](../frontend/src/api/client.js) |
