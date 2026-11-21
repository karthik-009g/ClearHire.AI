# ClearHire.AI — Comprehensive Feature Map & Technical Walkthroughs

> **Target Audience**: Final-year Computer Science / AI-ML engineering student onboarding onto the codebase.  
> **Rule**: Every feature is mapped to its exact frontend component, API route, controller, service logic, DB tables, implementation type (Deterministic vs LLM), and external APIs with relative file paths and verified lines.

---

## 1. End-to-End Feature Matrix

| Feature | Frontend Page / Component | API Route & Method | Backend Controller Function | Core Service / Algorithm | Implementation Type | DB Models / Tables | External APIs |
|---|---|---|---|---|---|---|---|
| **1. Candidate Auth & Auto-Provisioning** | [pages/login.js](../frontend/src/pages/login.js) | `POST /api/auth/login`<br/>`POST /api/auth/register` | [auth.py:login](../backend/app/api/auth.py#L72)<br/>[auth.py:register](../backend/app/api/auth.py#L50) | `bcrypt` hash verification via `app.utils.auth` & auto-user creation ([lines 80-89](../backend/app/api/auth.py#L80-L89)) | **Deterministic** | `User` (`users`), `UserPreference` | None |
| **2. Resume Upload & spaCy Parsing** | [pages/resmat-ai.js](../frontend/src/pages/resmat-ai.js) | `POST /api/resumes/upload` | [resumes.py:upload_resume](../backend/app/api/resumes.py#L171) | `ResumeParserService` (PyPDF2, python-docx, `en_core_web_sm`, 49 `SKILL_KEYWORDS`) | **Deterministic** | `Resume`, `ResumeVersion` | None |
| **3. 60/40 Hybrid JD Matching** | [pages/jd-analyzer.js](../frontend/src/pages/jd-analyzer.js) | `POST /api/resumes/match` | [resumes.py:match_resume](../backend/app/api/resumes.py#L243) | `ResumeMatcherService` (60% custom lexical overlap + 40% MiniLM cosine at [matcher_service.py:293](../backend/app/services/matcher_service.py#L293)) | **Deterministic** (Wrapped in LangGraph StateGraph in [workflow_service.py](../backend/app/services/workflow_service.py)) | `JobDescription`, `ResumeVersion` | None |
| **4. Direct First-Party ATS Sourcing** | [pages/job-hunter.js](../frontend/src/pages/job-hunter.js) | `POST /api/jobs/scrape` | [jobs.py:scrape_jobs](../backend/app/api/jobs.py#L195) | `DirectAtsService` ([direct_ats_service.py:343](../backend/app/services/direct_ats_service.py#L343)) across 17 curated ATS boards | **Deterministic** | `JobPosting` (`job_postings`) | Greenhouse, Lever, Ashby Public APIs |
| **5. Real-Time Link Liveness Filtering** | [pages/job-hunter.js](../frontend/src/pages/job-hunter.js) | Called in `POST /api/jobs/scrape` | [liveness_service.py:filter_live_jobs_concurrently](../backend/app/services/liveness_service.py#L210) | Concurrent thread pool (`max_workers=10` at line 237, `timeout=5.0s` at line 128), 8KB buffer (line 159), 12 closure phrases | **Deterministic** | In-Memory `_LIVENESS_CACHE` | Target Job Requisition URLs |
| **6. Reconciled RAG with Abstention** | [pages/student-lab.js](../frontend/src/pages/student-lab.js) | `POST /api/resumes/match/reconciled` | [resumes.py:match_resume_reconciled](../backend/app/api/resumes.py#L316) | `ReconciledRAGService` (pgvector cosine search, 0.35 similarity threshold at [config.py:67](../backend/app/utils/config.py#L67), margin `<= 0.03` at [rag_service.py:270-272](../backend/app/services/rag_service.py#L270-L272)) | **LLM-Optional** (Groq `llama3-8b-8192` in [rag_service.py:454](../backend/app/services/rag_service.py#L454) for summary explanation; deterministic fallback if no API key) | `JobPosting`, `ResumeVersion` | Groq API (Optional) |
| **7. 1-Page Resume Tailor & PDF Export** | [pages/resmat-ai.js](../frontend/src/pages/resmat-ai.js) | `POST /api/resumes/tailor`<br/>`POST /api/resumes/package/tailor`<br/>`GET /api/resumes/{resume_id}/versions/{version_no}/export-pdf` | [resumes.py:tailor_resume](../backend/app/api/resumes.py#L555)<br/>[resumes.py:export_version_pdf](../backend/app/api/resumes.py#L651) | `ResumeTailorService` (48 lines, 620 words, 24 words/bullet at [tailor_service.py:10-12](../backend/app/services/tailor_service.py#L10-L12)) + ReportLab 4.2.5 | **Deterministic** (Rule-based bullet rearrangement & template cover letter) | `ResumeVersion` (`resume_versions`) | None |
| **8. Application Tracking Kanban & FSM** | [pages/applications.js](../frontend/src/pages/applications.js) | `GET /api/applications/`<br/>`POST /api/applications/`<br/>`POST /api/applications/autofill`<br/>`PATCH /api/applications/{application_id}/status` | [applications.py:list_applications](../backend/app/api/applications.py#L505)<br/>[applications.py:prepare_application_autofill](../backend/app/api/applications.py#L295) | Finite state machine enforcing human review confirmation before submission ([applications.py:42-54](../backend/app/api/applications.py#L42-L54)) | **Deterministic** | `Application`, `ApplicationSubmissionLog` | None |
| **9. 14-Day Inactivity Ghosting Sentinel** | [pages/applications.js](../frontend/src/pages/applications.js) | `GET /api/applications/ghosting-alerts` | [applications.py:get_ghosting_alerts](../backend/app/api/applications.py#L564) | Evaluates application `updated_at` (`age >= 14 days` at [line 85](../backend/app/api/applications.py#L85)), recommends 5 direct ATS alternatives | **Deterministic** | `Application`, `JobDescription` | Greenhouse / Lever / Ashby |
| **10. Grounded Recruiter Outreach** | [pages/applications.js](../frontend/src/pages/applications.js) | `POST /api/applications/outreach`<br/>`POST /api/applications/{application_id}/outreach` | [applications.py:generate_custom_outreach](../backend/app/api/applications.py#L629)<br/>[applications.py:generate_application_outreach](../backend/app/api/applications.py#L689) | `RecruiterOutreachService` generating InMail, email, & LinkedIn note (< 300 chars at [line 140](../backend/app/services/recruiter_outreach_service.py#L140)) | **Deterministic** (Template slot-filling with detected highlights) | `Resume`, `UserPreference` | LinkedIn Search URL |
| **11. Grounded Interview Prep Kits** | [pages/applications.js](../frontend/src/pages/applications.js) | `GET /api/applications/{application_id}/interview-prep` | [applications.py:get_application_interview_prep](../backend/app/api/applications.py#L523) | `InterviewPrepService` extracting factual evidence from the exact applied resume version | **Deterministic** (Skill-to-STAR question mappings) | `Application`, `JobDescription`, `ResumeVersion` | None |
| **12. Screener Question Answering** | [pages/applications.js](../frontend/src/pages/applications.js) | `POST /api/applications/answer-screener` | [applications.py:answer_screener_question](../backend/app/api/applications.py#L176) | `ScreenerAnswerService` (intent detection: notice period, CTC, work authorization) | **LLM-Optional** (Groq `llama3-8b-8192` in [automation_service.py:402](../backend/app/services/automation_service.py#L402) with deterministic regex fallback in [screener_answer_service.py](../backend/app/services/screener_answer_service.py)) | `Resume`, `UserPreference` | Groq API (Optional) |
| **13. Funnel Analytics & Morning Digest** | [pages/funnel-analytics.js](../frontend/src/pages/funnel-analytics.js) | `GET /api/analytics/funnel`<br/>`GET /api/digest/preview`<br/>`POST /api/digest/send` | [digest.py:get_funnel_analytics](../backend/app/api/digest.py#L143)<br/>[digest.py:preview_digest](../backend/app/api/digest.py#L42)<br/>[digest.py:send_digest](../backend/app/api/digest.py#L74) | Conversion funnel aggregations; HTML email delivery via standard `smtplib.SMTP` in [email_service.py:33](../backend/app/services/email_service.py#L33) | **Deterministic** | `Application`, `JobPosting`, `UserPreference`, `DigestLog` | SMTP Mail Server (Gmail/Custom) |
| **14. Public Developer API & Scoped Keys** | N/A (External Developer Surface) | `POST /api/public/keys`<br/>`GET /api/public/keys`<br/>`POST /api/public/keys/{api_key_id}/revoke`<br/>`GET /api/public/whoami` | [public_api.py:create_api_key_endpoint](../backend/app/api/public_api.py#L51)<br/>[public_api.py:public_whoami](../backend/app/api/public_api.py#L112) | SHA-256 hashed API key creation, revocation, and scope validation (`read`, `write`, `admin`) | **Deterministic** | `ApiKey` (`api_keys`), `User` | None |
| **15. Background Scheduler & Retention Purge** | Automated Lifespan | N/A (APScheduler cron)<br/>`POST /api/resumes/cleanup-expired` | [scheduler_service.py:start_scheduler](../backend/app/services/scheduler_service.py#L33)<br/>[resumes.py:cleanup_expired_resumes](../backend/app/api/resumes.py#L541) | APScheduler cron triggers; `RetentionService` removes resumes older than 15 days ([config.py:53](../backend/app/utils/config.py#L53)) | **Deterministic** | `Resume`, `UserPreference`, `JobPosting` | None |
| **16. Candidate Profile & Preference Engine** | [pages/job-hunter.js](../frontend/src/pages/job-hunter.js) | `GET /api/auth/me`<br/>`GET /api/jobs/preferences`<br/>`POST /api/jobs/preferences` | [auth.py:me](../backend/app/api/auth.py#L101)<br/>[jobs.py:get_preferences](../backend/app/api/jobs.py#L454)<br/>[jobs.py:update_preferences](../backend/app/api/jobs.py#L380) | Updates target role, notice period, CTC, work mode, and schedule preferences | **Deterministic** | `User`, `UserPreference` | None |
| **17. 3D Spatial Radar & Autonomy Mesh** | [components/ClearHireStoryEngine.js](../frontend/src/components/ClearHireStoryEngine.js) | N/A (Client WebGL Animation) | Mounted in `useEffect` in [ClearHireStoryEngine.js](../frontend/src/components/ClearHireStoryEngine.js) | Native Three.js WebGL rendering ([ThreeSpatialRadar.js](../frontend/src/components/ThreeSpatialRadar.js), [autonomy/](../frontend/src/components/autonomy/)) | **Deterministic WebGL** | Client-only render state | None |

---

## 2. In-Depth Technical Walkthroughs

---

### Feature 1: Candidate Authentication & Vulnerability Remediation

#### What happens under the hood:
1. Candidate submits credentials on [pages/login.js](../frontend/src/pages/login.js).
2. The request reaches `POST /api/auth/login` in [backend/app/api/auth.py:72](../backend/app/api/auth.py#L72).
3. The server executes credential validation:
```python
    clean_email = request.email.strip().lower()
    user = db.query(User).filter(User.email == clean_email).first()
    if not user:
        if getattr(settings, "auth_auto_provision_users", False):
            user = User(email=clean_email, password_hash=hash_password(request.password))
            db.add(user)
            db.commit()
            db.refresh(user)
        else:
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail="Invalid email or password",
            )
    elif not verify_password(request.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid email or password",
        )
```

> [!NOTE]
> ### Security Vulnerability & Applied Remediation
> **Original Vulnerability**: Historically, lines 85–89 contained an ungated fallback `user.password_hash = hash_password(request.password)` when `verify_password` returned `False`. An attacker submitting any password for a known email address would overwrite the user's password hash in the database and receive a valid JWT token. Additionally, unknown users were auto-provisioned unconditionally.
> **Remediation Implemented**:
> 1. **Password Mismatch**: Now unconditionally returns `401 Unauthorized` (`detail="Invalid email or password"`) and never overwrites `user.password_hash`.
> 2. **Auto-Provisioning Gate**: Auto-provisioning is gated behind `settings.auth_auto_provision_users: bool = False` ([config.py:35](../backend/app/utils/config.py#L35)). When `False` (default), unregistered emails receive `401 Unauthorized`. When explicitly set to `True`, seamless first-login auto-provisioning is permitted.
> 3. **Regression Tests**: Verified by `test_auth_password_mismatch_returns_401_and_preserves_hash`, `test_auth_unregistered_user_returns_401_when_auto_provision_disabled`, and `test_auth_auto_provision_when_enabled` in [test_auth_api.py](../backend/tests/test_auth_api.py).

---

### Feature 2: Resume Ingestion & Deterministic Parsing

1. File uploaded via [pages/resmat-ai.js](../frontend/src/pages/resmat-ai.js) to `POST /api/resumes/upload` ([resumes.py:171](../backend/app/api/resumes.py#L171)).
2. [file_security.py:35-67](../backend/app/utils/file_security.py#L35-L67) inspects raw magic bytes: `%PDF-` for PDF ([line 15](../backend/app/utils/file_security.py#L15)), `PK\x03\x04` container with required XML components for DOCX ([lines 18-32](../backend/app/utils/file_security.py#L18-L32)).
3. [parser_service.py:267](../backend/app/services/parser_service.py#L267) runs `parse_resume()`, executing spaCy `en_core_web_sm` to extract named entities and matching skills against 49 curated `SKILL_KEYWORDS` ([parser_service.py:14-21](../backend/app/services/parser_service.py#L14-L21)).
4. Embeds text with `all-MiniLM-L6-v2` into 384 dimensions ([matcher_service.py:77](../backend/app/services/matcher_service.py#L77)).

---

### Feature 3: 60/40 Hybrid JD Matching & LangGraph Orchestration

1. Evaluates custom weighted keyword overlap in [matcher_service.py:149-195](../backend/app/services/matcher_service.py#L149-L195):
   - Tech keywords (51 terms in [matcher_service.py:63-70](../backend/app/services/matcher_service.py#L63-L70)) get 1.7x multiplier ([line 167](../backend/app/services/matcher_service.py#L167)).
   - Multi-word phrases get 1.5x multiplier ([line 169](../backend/app/services/matcher_service.py#L169)).
   - Standard words get 1.0x ([line 170](../backend/app/services/matcher_service.py#L170)).
2. Computes dense embedding cosine similarity, normalized to 0-100: `round(((similarity + 1.0) / 2.0) * 100, 2)` ([line 202](../backend/app/services/matcher_service.py#L202)).
3. Blends scores into a final rating: `round((0.6 * keyword_score) + (0.4 * embedding_score), 2)` ([line 293](../backend/app/services/matcher_service.py#L293)).
4. **Where LangGraph is used**: [workflow_service.py:30-60](../backend/app/services/workflow_service.py#L30-L60) compiles a 2-node graph:
   ```python
   graph = StateGraph(ResumeAnalysisState)
   graph.add_node("parse_step", parse_node)
   graph.add_node("match_step", match_node)
   graph.set_entry_point("parse_step")
   graph.add_edge("parse_step", "match_step")
   graph.add_edge("match_step", END)
   ```
   Invoked in [resumes.py:273](../backend/app/api/resumes.py#L273) as `run_resume_analysis_flow()`.

---

### Feature 6: Reconciled RAG Engine & Dual Thresholds

#### The Real Retrieval Query ([rag_service.py:90-99](../backend/app/services/rag_service.py#L90-L99)):
```sql
SELECT id, title, company, description,
       (1 - (embedding_vector <=> CAST(:query_vector AS vector))) AS similarity
FROM job_postings
WHERE embedding_vector IS NOT NULL
ORDER BY embedding_vector <=> CAST(:query_vector AS vector)
LIMIT :k
```
- **Column Used**: Native PostgreSQL `pgvector` column **`embedding_vector`**.
- **What is Retrieved**: Requisitions from the **`job_postings`** table. Resume evidence is not queried from the database; it is extracted deterministically via string-matching candidate resume lines ([lines 72-80](../backend/app/services/rag_service.py#L72-L80)).
- **Execution on SQLite**:
  When running on SQLite (`is_pg = False` at [line 88](../backend/app/services/rag_service.py#L88)), the service executes a fallback query loading the most recent 100 `JobPosting` records ([lines 116-121](../backend/app/services/rag_service.py#L116-L121)), deserializes their JSON embeddings (`candidate_embedding = row.embedding_vector or row.embedding`), computes cosine similarity in Python via `matcher.cosine_similarity()`, normalizes to `(sim + 1.0) / 2.0`, and sorts in Python memory ([lines 133-145](../backend/app/services/rag_service.py#L133-L145)).

#### `RAG_SIMILARITY_THRESHOLD = 0.35` vs `RAG_ABSTAIN_THRESHOLD = 0.55`:
- **`rag_similarity_threshold: float = 0.35`** ([config.py:66](../backend/app/utils/config.py#L66)):
  Used in [rag_service.py:312](../backend/app/services/rag_service.py#L312) (`_evidence_quality`). This is the threshold for an **individual evidence snippet** to count toward `strong_evidence_count`.
- **`rag_abstain_threshold: float = 0.55`** ([config.py:67](../backend/app/utils/config.py#L67)):
  Used in [rag_service.py:414](../backend/app/services/rag_service.py#L414). This evaluates the **overall composite confidence**:
  $$\text{confidence} = 0.55 \times \text{top\_sim} + 0.25 \times \frac{\text{total\_score}}{100} + 0.20 \times \text{overlap\_ratio} + \text{title\_bonus} - \text{company\_penalty}$$
  If composite $\text{confidence} < 0.55$, the engine returns `status: "low_confidence"` with `abstained: True`.
- **Ambiguity Margin**: If the top two evidence items have $|\text{sim}_0 - \text{sim}_1| \le 0.03$ ([lines 270-272](../backend/app/services/rag_service.py#L270-L272)), the evidence is flagged as conflicting.

---

### Feature 8 & 9: Application Tracking & The 14-Day Ghosting Timestamp

In [models/resume.py:91-103](../backend/app/models/resume.py#L91-L103), the `Application` model contains:
- `id`, `user_id`, `job_description_id`, `resume_version_id`, `status`, `application_url`, `autofill_payload`, `notes`, `updated_at`.
- **There is no `applied_at` column in the database.**
- The ghosting check in [applications.py:83-85](../backend/app/api/applications.py#L83-L85) evaluates:
  ```python
  days_since_update = (datetime.utcnow() - application.updated_at).days
  is_ghosted = application.status in {"applied", "screening"} and days_since_update >= 14
  ```
- **What resets it**: Any update to the application resets `updated_at = datetime.utcnow()`:
  - Status updates ([line 455](../backend/app/api/applications.py#L455))
  - Review confirmations ([line 488](../backend/app/api/applications.py#L488))
  - Submissions ([line 769](../backend/app/api/applications.py#L769))
  - Autofill edits or note modifications ([line 874](../backend/app/api/applications.py#L874))
  *If a candidate edits a note on an application on day 13, the ghosting timer resets back to 0 days.*

---

## 3. Known Architectural & Algorithmic Weaknesses

### 1. Mathematical Embedding Score Compression ([matcher_service.py:202](../backend/app/services/matcher_service.py#L202))
Cosine similarity between Sentence Transformer dense embeddings of natural English text almost never drops below 0.0; typical unrelated texts score between 0.05 and 0.25.
Because `_embedding_similarity` normalizes cosine similarity using:
$$\text{normalized} = \frac{\text{similarity} + 1.0}{2.0} \times 100$$
The practical output range is compressed into **`[50.0, 95.0]`**:
- A completely unrelated resume ($\text{cosine} \approx 0.0$) receives an embedding score of **`50.0%`**.
- Because the final match formula weights embeddings at 40% (`0.4 * embedding_score`), an applicant with **zero matching keywords** receives a baseline total match score of:
  $$\text{total\_score} = (0.6 \times 0.0) + (0.4 \times 50.0) = \mathbf{20.0\%}$$
This artificially inflates match scores for unqualified applicants.

### 2. In-Memory Process-Isolated Cache ([direct_ats_service.py:107](../backend/app/services/direct_ats_service.py#L107))
While Redis is installed in `backend/requirements.txt`, the application currently instantiates `CacheService` as an in-memory dictionary. Under multi-worker deployments (e.g. Uvicorn with `--workers 4`), cache entries are not shared across processes, resulting in redundant external ATS API queries.

### 3. Synchronous HTTP in External Scraping
`DirectAtsService` utilizes synchronous `requests.Session()` within thread pools rather than native async I/O (`httpx.AsyncClient`). Under heavy concurrency, threads block on slow external ATS servers.

### 4. Ghosting Inactivity Timer Reset
Because the 14-day ghosting threshold measures `updated_at` rather than an immutable `submitted_at` or `applied_at` timestamp, adding or editing personal notes on an applied requisition resets the ghosting alert timer back to day 0.
