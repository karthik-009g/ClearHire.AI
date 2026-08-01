# ClearHire.AI Build From Scratch Guide

This document explains how ClearHire.AI is built from an empty project folder into the final full-stack AI job application assistant. It describes the folder creation order, what each file does, the coding sequence, and how the backend, frontend, matching engine, RAG layer, and deployment pieces connect.

## 1. Product Starting Point

ClearHire.AI starts with one product idea:

```text
Help a candidate upload a resume, compare it against job descriptions, discover matching jobs, tailor the resume safely, and track applications.
```

The project is intentionally designed as an assistant, not a fully autonomous auto-apply bot. The user stays in control of application submission.

The end-to-end product flow is:

```text
Resume Upload
  -> Resume Parsing
  -> Resume Embedding
  -> JD Analysis
  -> Hybrid Matching
  -> RAG Evidence Reconciliation
  -> Resume Tailoring
  -> Job Search and Ranking
  -> Application Tracking
```

## 2. Create The Root Project

Start with the main application folder:

```text
job_automate/
```

Inside it, create the four top-level areas:

```text
job_automate/
  backend/
  frontend/
  deployment/
  docs/
  README.md
```

Each folder has a clear responsibility:

```text
backend/
  API, database, AI services, parsing, matching, RAG, scraping, tests

frontend/
  Next.js user interface and browser-side API clients

deployment/
  Docker, nginx, database initialization, deployment notes

docs/
  product requirements, technical architecture, execution plan, build guide
```

## 3. Write The Product Docs First

Before code, define the product scope. This prevents building random features without clear boundaries.

Create:

```text
docs/V1_PRODUCT_REQUIREMENTS.md
docs/V1_TECH_ARCHITECTURE.md
docs/V1_EXECUTION_PLAN.md
```

### V1_PRODUCT_REQUIREMENTS.md

Defines what the app should do:

```text
Resume upload
Resume parsing
JD-resume matching
Job discovery
Tailored resume generation
Apply-ready package export
Application tracking
```

It also defines what V1 should not do:

```text
No autonomous auto-apply
No ATS integrations
No n8n workflow automation
No aggressive LLM rewriting
```

### V1_TECH_ARCHITECTURE.md

Defines the technical shape:

```text
Frontend: Next.js
Backend: FastAPI
Database: PostgreSQL
Vector search: pgvector with JSON fallback
File storage: local disk for V1
AI: parser, matcher, embeddings, RAG, optional LLM
```

### V1_EXECUTION_PLAN.md

Defines build phases:

```text
Phase 1: Backend foundation
Phase 2: Matching engine
Phase 3: Tailored output
Phase 4: Web experience
Phase 5: Quality and release
```

## 4. Build The Backend Foundation

Create:

```text
backend/
  README.md
  requirements.txt
  alembic.ini
  start_backend.ps1
  app/
    __init__.py
    main.py
    database.py
```

### backend/requirements.txt

Lists backend dependencies:

```text
fastapi
uvicorn
sqlalchemy
alembic
pydantic-settings
python-jose/passlib or equivalent auth dependencies
python-docx
PyPDF2
pdfminer
spacy
sentence-transformers
pgvector
groq
pytest
```

The exact versions are pinned in the current project file.

### backend/app/main.py

This is the FastAPI entry point.

It creates the app, configures middleware, starts/stops scheduler hooks, exposes health checks, and includes routers:

```text
/api/auth
/api/resumes
/api/jobs
/api/applications
```

Build this file early because it becomes the central connection point for the backend.

### backend/app/database.py

Creates:

```text
SQLAlchemy engine
SessionLocal
Base model class
get_db dependency
init_db helper
```

Every API route that needs the database depends on `get_db()`.

## 5. Add Configuration And Utilities

Create:

```text
backend/app/utils/
  __init__.py
  config.py
  auth.py
  file_security.py
```

### config.py

This file centralizes all environment settings:

```text
database_url
redis_url
secret_key
auth_enabled
storage_root
max_upload_mb
allowed upload extensions
spacy_model
embedding_model_name
embedding_dimensions
rag settings
Groq settings
SMTP settings
scraper settings
```

Important AI defaults:

```text
embedding_model_name = sentence-transformers/all-MiniLM-L6-v2
embedding_dimensions = 384
llm_provider = groq
groq_model = llama-3.3-70b-versatile
```

### auth.py

Handles password hashing, JWT creation, JWT validation, and current-user dependency helpers.

### file_security.py

Validates uploaded resumes:

```text
allowed extension
allowed MIME type
maximum file size
basic content checks
```

This exists because resumes contain real personal data and file uploads are a common attack surface.

## 6. Build The Data Models

Create:

```text
backend/app/models/
  __init__.py
  user.py
  resume.py
  jobs.py
  vector_type.py
```

### user.py

Stores user account data:

```text
id
email
hashed_password
created_at
```

### resume.py

Stores the resume and matching domain:

```text
Resume
ResumeVersion
JobDescription
MatchResult
Application
```

Why each model exists:

```text
Resume
  original uploaded resume metadata and parsed summary

ResumeVersion
  each text version of the resume, including tailored versions

JobDescription
  JD text analyzed by the user

MatchResult
  keyword score, embedding score, total score, gaps, explanations, RAG metadata

Application
  pending/applied tracking for a job and resume version
```

### jobs.py

Stores job discovery data:

```text
JobPosting
UserPreference
```

Why:

```text
JobPosting
  scraped jobs with title, company, URL, description, score, embedding

UserPreference
  target role, email, locations, keywords, selected job sources, schedule settings
```

### vector_type.py

Creates a cross-database vector column type:

```text
PostgreSQL + pgvector available
  -> use pgvector Vector(384)

Other/test environment
  -> use JSON fallback
```

This keeps production vector search fast while keeping local testing simple.

## 7. Add Alembic Migrations

Create:

```text
backend/alembic/
  env.py
  script.py.mako
  versions/
```

Migration files define how the database evolves:

```text
0001 init resume flow
0002 optional auth and application owner
0003 jobs and preferences
0004 embeddings scheduler autofill
0005 user profile fields
0006 RAG pgvector and reconciliation foundation
```

Migrations are important because production deployments need repeatable database setup.

## 8. Build The Service Layer

Create:

```text
backend/app/services/
  __init__.py
  storage.py
  parser_service.py
  matcher_service.py
  workflow_service.py
  rag_service.py
  tailor_service.py
  job_scraper_service.py
  automation_service.py
  job_digest_service.py
  email_service.py
  scheduler_service.py
  retention_service.py
```

The service layer holds business logic. API routes should stay thin and call services.

### storage.py

Saves uploaded resume files to local disk for V1.

Design decision:

```text
Use local storage first because V1 targets low-cost launch.
Move to S3-compatible storage later if needed.
```

### parser_service.py

Extracts and structures resume content.

It handles:

```text
PDF text extraction
DOCX text extraction
text normalization
section extraction
skill extraction
experience estimation
project count estimation
```

Design decision:

```text
Use deterministic parsing heuristics because resume analysis must be explainable and testable.
```

### matcher_service.py

Computes resume/JD match scores.

It uses:

```text
keyword overlap
embedding similarity
weighted total score
```

Formula:

```text
total_score = 0.6 * keyword_score + 0.4 * embedding_score
```

Design decision:

```text
Keyword score is weighted slightly higher because V1 should behave like an ATS-aware assistant.
Embedding score is still important because users and JDs may use different words for similar ideas.
```

Embedding model:

```text
sentence-transformers/all-MiniLM-L6-v2
384 dimensions
```

Fallback:

```text
If the model cannot load, use deterministic hashed vectors.
```

This keeps tests and local environments functional.

### workflow_service.py

Combines parser and matcher into one resume analysis flow.

This prevents duplicated orchestration logic across API routes.

### rag_service.py

Implements reconciled RAG.

RAG flow:

```text
Embed JD query
  -> retrieve similar job postings
  -> retrieve similar job descriptions
  -> retrieve previous match results
  -> rank evidence
  -> reconcile confidence
  -> optionally generate grounded answer with LLM
```

Evidence sources:

```text
job_postings
job_descriptions
match_results
```

Reconciliation statuses:

```text
valid
no_match
ambiguous
low_confidence
```

Design decision:

```text
Do not trust retrieved context blindly. Job matching can affect a real person's applications, so the system should abstain when evidence is weak.
```

Optional LLM:

```text
Groq llama-3.3-70b-versatile
```

The LLM only runs if a Groq API key exists. Otherwise, the service returns a deterministic grounded summary.

### tailor_service.py

Creates controlled resume tailoring.

It does:

```text
inject missing keywords carefully
tighten bullet points
enforce one-page constraints
generate optional cover letter
return apply-ready package metadata
```

Design decision:

```text
V1 tailoring must not invent experience. It should preserve the candidate's supplied facts.
```

### job_scraper_service.py

Scrapes or fetches job listings from configured sources.

It returns normalized job items:

```text
source
company
title
location
url
description
scraped_at
```

### automation_service.py

Ranks jobs against resume embeddings and renders job digest content.

### email_service.py

Sends HTML email digests when SMTP is configured.

### scheduler_service.py

Starts and stops scheduling hooks for automation workflows.

### retention_service.py

Deletes expired resume records and files.

Design decision:

```text
Resume data is sensitive, so retention cleanup is part of the backend design.
```

## 9. Build The API Layer

Create:

```text
backend/app/api/
  __init__.py
  auth.py
  resumes.py
  jobs.py
  applications.py
  schemas/
    __init__.py
    auth.py
    resume.py
    jobs.py
```

### schemas/

Schemas define request and response shapes using Pydantic.

Design decision:

```text
Keep API contracts explicit so frontend and backend agree on payloads.
```

### auth.py

Exposes:

```text
register
login
token validation
```

### resumes.py

This is the main AI pipeline router.

Endpoints include:

```text
POST /upload
GET /{resume_id}
GET /{resume_id}/versions
POST /{resume_id}/reembed
POST /match
POST /match/reconciled
POST /tailor
POST /package/tailor
POST /cleanup-expired
```

Core upload flow:

```text
read uploaded file
validate file
extract text
parse resume
save file
build resume context
embed resume
create Resume
create ResumeVersion v1
return parsed summary
```

Core match flow:

```text
load resume
load latest version
refresh embedding if needed
run parser + matcher flow
embed JD
save JobDescription
save MatchResult
return scores and gaps
```

Core reconciled RAG flow:

```text
load resume and version
run RAG service
save RAG evidence and reconciliation fields
return grounded answer or abstention reason
```

### jobs.py

Exposes:

```text
POST /scrape
GET /preferences
POST /preferences
POST /digest
```

Core scrape flow:

```text
read sources and keywords
scrape jobs
embed jobs
store or update job_postings
rank against resume embedding
optionally send email
return jobs and top matches
```

### applications.py

Exposes:

```text
POST /
GET /
PATCH /{application_id}/status
POST /autofill
```

The autofill endpoint intentionally returns unavailable in V1.

Design decision:

```text
Application submission is high risk. V1 tracks applications but does not submit them automatically.
```

## 10. Add Tests

Create:

```text
backend/tests/
  sample_resume.docx
  test_api_endpoints.py
  test_auth_api.py
  test_evaluation_metrics.py
  test_job_scraper_service.py
  test_jobs_preferences.py
  test_matcher_service.py
  test_parser_service.py
  test_rag_service.py
  test_tailor_service.py
  test_upload_security.py
```

Test focus:

```text
file upload security
resume parsing
matcher scoring
tailor behavior
RAG abstention and ambiguity
job scraping behavior
preferences
auth APIs
general API endpoints
evaluation metrics
```

Design decision:

```text
Parser and matcher tests are the highest-value tests because they protect the core AI pipeline.
```

## 11. Build The Frontend Project

Create:

```text
frontend/
  README.md
  package.json
  package-lock.json
  src/
    api/
    components/
    lib/
    pages/
    styles/
```

The frontend is a Next.js app.

## 12. Build Frontend API Clients

Create:

```text
frontend/src/api/
  client.js
  auth.js
  resumes.js
  jobs.js
  applications.js
```

### client.js

Central fetch wrapper.

It handles:

```text
API base URL
auth token storage
Authorization header
JSON response parsing
error normalization
```

### auth.js

Calls backend auth endpoints.

### resumes.js

Calls resume endpoints:

```text
upload
match
reconciled match
tailor
package download
versions
re-embed
```

### jobs.js

Calls job scraping, preferences, and digest endpoints.

### applications.js

Calls application tracking endpoints.

Design decision:

```text
Keep raw fetch logic out of pages so UI files stay focused on user interaction.
```

## 13. Build Shared Frontend State

Create:

```text
frontend/src/lib/moduleState.js
```

This stores browser-side state:

```text
clearhire_resmat_context
clearhire_jd_context
```

It also provides helpers:

```text
formatPercent
parseCsv
normalizeSkills
extractSkillKeywords
inferTargetSkills
computeSkillGap
```

Design decision:

```text
The app is modular but the modules need to share current resume and JD context. localStorage is enough for V1.
```

## 14. Build Shared Layout

Create:

```text
frontend/src/components/ModuleLayout.js
```

This wraps pages with shared navigation and consistent layout.

Design decision:

```text
All modules should feel like one product, not unrelated pages.
```

## 15. Build Frontend Pages

Create:

```text
frontend/src/pages/
  _app.js
  index.js
  login.js
  resmat-ai.js
  jd-analyzer.js
  job-hunter.js
  applications.js
  student-lab.js
```

### _app.js

Loads global styles and wraps the Next.js app.

### index.js

Mission Control dashboard.

Shows:

```text
resume readiness
latest match score
skill gap count
links to modules
```

### login.js

Handles user login/registration flow.

### resmat-ai.js

Resume intelligence page.

Features:

```text
upload resume
display extracted skills
show version timeline
sync parsed summary
tailor resume for latest JD
download apply-ready package
```

### jd-analyzer.js

JD analysis page.

Features:

```text
paste JD
run match
show keyword score
show embedding score
show total score
infer target tech stack
compute skill gaps
show market signals from job scrape
```

### job-hunter.js

Job discovery page.

Features:

```text
choose sources
enter keywords
search jobs
rank jobs against resume
tailor resume for top jobs
```

### applications.js

Application tracking page.

Features:

```text
list applications
show job title/company
show resume version used
update pending/applied status
```

### student-lab.js

Learning support page.

Features:

```text
learning path
project practice
interview preparation
student growth modules
```

## 16. Add Global Styles

Create:

```text
frontend/src/styles/globals.css
```

This defines the visual language for:

```text
layout
cards
buttons
forms
metrics
chips
lists
error/success states
responsive grids
```

Design decision:

```text
A module-based dashboard needs consistent UI primitives so each page feels connected.
```

## 17. Add Evaluation Tools

Create:

```text
backend/app/evaluation/
  __init__.py
  metrics.py
  run_evaluation.py
  datasets/
    reconciled_match_eval_20.json
```

Evaluation checks:

```text
retrieval precision
hallucination rate
abstain rate
latency
```

Design decision:

```text
RAG systems need evaluation because a grounded answer is only useful if it actually stays grounded.
```

## 18. Add Scripts

Create:

```text
backend/app/scripts/
  __init__.py
  backfill_vectors.py
```

### backfill_vectors.py

Used when embeddings need to be regenerated for existing data.

Design decision:

```text
Embedding dimensions or model logic may change. A backfill script lets the database be repaired without manual updates.
```

## 19. Add Deployment Files

Create:

```text
deployment/
  README.md
  docker/
    Dockerfile
    Dockerfile.frontend
    docker-compose.yml
    init-db.sql
    nginx.conf
```

### Dockerfile

Builds the backend container.

### Dockerfile.frontend

Builds the frontend container.

### docker-compose.yml

Runs:

```text
backend
frontend
postgres
nginx or proxy support
```

### init-db.sql

Initializes database extensions or bootstrap SQL.

For vector search, this is where pgvector setup belongs.

### nginx.conf

Routes frontend/backend traffic in containerized deployment.

Design decision:

```text
Keep deployment repeatable and separate from local development.
```

## 20. Add Project README Files

Create:

```text
README.md
backend/README.md
frontend/README.md
deployment/README.md
```

Each README should explain its own layer:

```text
root README
  product overview and full app flow

backend README
  API, services, environment, test notes

frontend README
  Next.js setup and pages

deployment README
  Docker/deployment instructions
```

## 21. Final File Structure

The final tracked project structure is:

```text
job_automate/
  README.md
  backend/
    README.md
    alembic.ini
    requirements.txt
    start_backend.ps1
    alembic/
    app/
      main.py
      database.py
      api/
      evaluation/
      models/
      scrapers/
      scripts/
      services/
      utils/
    tests/
  deployment/
    README.md
    docker/
  docs/
    V1_EXECUTION_PLAN.md
    V1_PRODUCT_REQUIREMENTS.md
    V1_TECH_ARCHITECTURE.md
    BUILD_FROM_SCRATCH.md
  frontend/
    README.md
    package.json
    package-lock.json
    src/
      api/
      components/
      lib/
      pages/
      styles/
```

## 22. End-To-End Runtime Flow

When the final app runs, the user journey is:

```text
1. User logs in.
2. User uploads resume in ResMat.ai.
3. Backend validates and parses the resume.
4. Backend stores resume metadata and version text.
5. Backend creates a resume embedding.
6. User opens JD Analyzer and pastes a JD.
7. Backend computes keyword score, embedding score, and total score.
8. Backend stores the JD and match result.
9. Optional RAG match retrieves previous jobs/JDs/matches as evidence.
10. RAG reconciliation returns valid, no_match, ambiguous, or low_confidence.
11. Frontend displays score, gaps, target stack, and market signals.
12. User tailors resume for the JD or top jobs.
13. Backend creates a new resume version.
14. User searches jobs in Job Hunter.
15. Backend scrapes jobs, embeds them, ranks them, and returns top matches.
16. User tracks applications as pending or applied.
```

## 23. Why The Project Was Built This Way

### Modular backend

The backend separates API routes from services so each part can evolve independently.

```text
API route
  handles HTTP

Service
  handles business logic

Model
  handles persistence shape
```

### Hybrid matching

Pure keyword matching is too strict. Pure semantic matching is hard to explain.

ClearHire uses both:

```text
keyword overlap for ATS-style clarity
embedding similarity for meaning
```

### Reconciled RAG

Normal RAG may hallucinate. ClearHire adds reconciliation and abstention because job matching should not invent facts.

### pgvector with JSON fallback

Production gets vector search. Local/test environments stay simple.

### Deterministic tailoring

V1 avoids unsafe resume rewriting. The system improves alignment without fabricating experience.

### No auto-submit

Application submission has legal, ethical, and user-control concerns. V1 tracks applications but does not submit them automatically.

### Local storage first

Local disk storage keeps V1 cheap and simple. S3-compatible storage can be added later.

### Tests around parser, matcher, and RAG

These are the highest-risk parts because they directly affect user trust.

## 24. Build Order Recap

If rebuilding from scratch, follow this order:

```text
1. Product docs
2. Backend app shell
3. Config and database
4. Models and migrations
5. Parser service
6. Matcher service
7. Resume APIs
8. Frontend API clients
9. ResMat.ai page
10. JD Analyzer page
11. RAG service
12. Tailor service
13. Job scraping and ranking
14. Job Hunter page
15. Application tracking
16. Evaluation and tests
17. Deployment files
18. README cleanup
```

That order matters because each layer depends on the previous one. The frontend pages need API contracts. API routes need services. Services need models and config. Models need database setup.

## 25. Final Result

The finished ClearHire.AI project is a full-stack AI career engine:

```text
Next.js dashboard
FastAPI backend
PostgreSQL database
pgvector-powered semantic search
sentence-transformers embeddings
optional Groq LLM grounded summaries
resume parser
hybrid matcher
reconciled RAG
controlled resume tailor
job scraper and ranker
application tracker
Docker deployment support
```

The project is designed to be useful first, explainable second, and safely extendable into more advanced automation later.
