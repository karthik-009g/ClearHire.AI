# clearhire.ai

clearhire.ai is an agentic job application assistant focused on helping candidates prepare better applications faster.

The current version is built around secure resume handling, semantic job matching, tailored resume generation, and job digest automation. It is designed to be practical for daily use while keeping sensitive data handling and explainability in mind.

## Current Status

- Product stage: V1 active development
- Frontend in use: Streamlit client
- Backend: FastAPI + PostgreSQL
- Authentication: enabled by default
- Resume retention: 15 days (configurable)

## What Works Today

### Core candidate workflow
- Account registration and login with JWT authentication
- Resume upload with file safety checks (extension, MIME, signature)
- Resume parsing for structured summary extraction
- Semantic JD matching with:
  - keyword score
  - embedding score
  - total score + explanation
- Tailored resume generation with version history
- Apply-ready package export (ZIP)
- Application tracking (create, list, status update)

### Job discovery and automation
- Job scraping from configured India-focused sources
- Job ranking using resume embeddings + keywords
- User preferences for role, locations, keywords, sources
- Scheduler preferences per user (time + timezone)
- Automated scrape triggers on login/upload (when enabled)
- Email digest delivery for top matched jobs (SMTP-based)

### Frontend
- Streamlit login-first experience
- Multipage flows for upload, match, tailor, applications, preferences, scrape/digest

## Planned Features (Roadmap)

The following are planned/in-progress ideas and are not fully available in current V1:

- Auto job application form filling across supported portals
- Career portal automation for company careers sites
- Naukri integration via compliant interface (API or automation path)
- LinkedIn jobs integration via compliant interface (API or automation path)
- Expanded source adapters with stronger retry/observability
- Optional ATS integrations and enterprise workflow hooks

Note: Portal API availability and terms differ by provider. Implementation will follow legal and platform policy constraints.

## What Is Explicitly On Hold

- Autofill endpoint for direct application filling is intentionally on hold in V1.
- Current endpoint behavior: returns HTTP 503 with on-hold message.

## High-Level Architecture

- Backend: FastAPI service layer, SQLAlchemy ORM, Alembic migrations
- Database: PostgreSQL (local or Neon-compatible)
- Matching/NLP: spaCy + sentence-transformers
- Scheduling: APScheduler
- Email: SMTP
- Frontend: Streamlit multipage client
- Deployment options: Docker Compose, AWS/Kubernetes scaffolding

## Repository Layout

```text
job-automation-tool/
  backend/                 FastAPI app, services, models, migrations, tests
  streamlit-client/        Active Streamlit frontend
  frontend/                Future/alternative web frontend scaffold
  deployment/              Docker, AWS, Kubernetes assets
  docs/                    Product and technical docs
  README.md                This file
```

## API Overview (V1)

### Auth
- POST /api/auth/register
- POST /api/auth/login
- GET /api/auth/me

### Resumes
- POST /api/resumes/upload
- POST /api/resumes/match
- POST /api/resumes/tailor
- POST /api/resumes/package/tailor
- GET /api/resumes/{resume_id}
- GET /api/resumes/{resume_id}/versions
- POST /api/resumes/cleanup-expired

### Jobs
- POST /api/jobs/scrape
- POST /api/jobs/preferences
- GET /api/jobs/preferences
- POST /api/jobs/digest

### Applications
- POST /api/applications/
- GET /api/applications/
- PATCH /api/applications/{application_id}/status
- POST /api/applications/autofill (on hold)

## Local Development Setup

## Prerequisites

- Python 3.11+
- PostgreSQL 14+
- Node.js 18+ (only if using the future web frontend)
- Optional: Docker + Docker Compose

## 1) Start Backend

```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt

# configure backend/.env first
alembic upgrade head
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

Windows shortcut:

```powershell
cd backend
.\start_backend.ps1
```

## 2) Start Streamlit Client

```powershell
cd streamlit-client
python -m venv .venv
.\.venv\Scripts\activate
pip install -r requirements.txt
streamlit run app.py
```

Default URLs:

- Backend: http://127.0.0.1:8000
- API docs: http://127.0.0.1:8000/docs
- Streamlit: http://localhost:8501

## Key Configuration

Set values in backend/.env as needed:

- DATABASE_URL
- SECRET_KEY
- AUTH_ENABLED
- RESUME_RETENTION_DAYS
- EMBEDDING_MODEL_NAME
- SPACY_MODEL
- SMTP_HOST, SMTP_PORT, SMTP_USERNAME, SMTP_PASSWORD, SMTP_SENDER_EMAIL
- NAUKRI_EMAIL, NAUKRI_PASSWORD
- LINKEDIN_EMAIL, LINKEDIN_PASSWORD

## Testing

```powershell
cd backend
pytest -q
```

## Docker (Optional)

```powershell
cd deployment/docker
docker-compose up -d
```

## Security Notes

- Uploads are validated before parsing.
- Ownership checks are enforced for resume/application resources when auth is enabled.
- Avoid logging raw resume text in production.
- Rotate secrets and use strong SMTP/API credentials.

## Contributing

1. Create a feature branch.
2. Keep PRs focused and test-backed.
3. Update docs when behavior changes.

## License

Proprietary or internal-use by default unless a separate LICENSE file is added.
