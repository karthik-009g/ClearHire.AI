# Backend Segment

## Overview
FastAPI-based backend server handling job scraping, AI resume optimization, and automated job applications.

## Architecture

```
app/
├── api/
│   ├── __init__.py
│   ├── jobs.py              # GET jobs, filter, search
│   ├── applications.py       # POST applications, track status
│   ├── resumes.py           # Upload, manage, optimize resumes
│   ├── auth.py              # User authentication
│   └── scheduler.py         # Control automation schedules
│
├── models/
│   ├── __init__.py
│   ├── job.py               # JobListing model
│   ├── application.py       # Application record model
│   ├── resume.py            # Resume template model
│   ├── user.py              # User profile model
│   └── base.py              # Base model class
│
├── services/
│   ├── __init__.py
│   ├── job_matcher.py       # Score & filter jobs
│   ├── resume_optimizer.py  # Claude API integration
│   ├── applicator.py        # Auto-fill & submit
│   └── analytics.py         # Track metrics
│
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py      # Base class for all scrapers
│   ├── naukri_scraper.py    # Naukri.com scraper
│   ├── linkedin_scraper.py  # LinkedIn scraper
│   └── company_scraper.py   # Company career pages
│
├── utils/
│   ├── __init__.py
│   ├── config.py            # Settings & env vars
│   ├── auth.py              # JWT token handling
│   ├── validators.py        # Input validation
│   └── logger.py            # Logging configuration
│
├── main.py                  # FastAPI app initialization
└── database.py              # SQLAlchemy setup

tests/
├── test_scrapers.py
├── test_services.py
└── test_api.py

.env.example
requirements.txt
```

## Environment Variables

```ini
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/job_automation

# API Keys
CLAUDE_API_KEY=sk-ant-xxxxx
OPENAI_API_KEY=sk-xxxx (optional)

# Job Portal Credentials
NAUKRI_EMAIL=your@email.com
NAUKRI_PASSWORD=password
LINKEDIN_EMAIL=your@email.com
LINKEDIN_PASSWORD=password

# Redis (for task queue)
REDIS_URL=redis://localhost:6379/0

# JWT
SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_HOURS=24

# App Config
DEBUG=false
ENVIRONMENT=production
```

## Database Models

### User
- id (PK)
- email
- password_hash
- full_name
- preferences (JSON)
- created_at

### Resume
- id (PK)
- user_id (FK)
- file_path
- template_name
- skills (array)
- experience (text)
- education (text)
- uploaded_at

### JobListing
- id (PK)
- title
- company
- platform (naukri/linkedin/etc)
- salary_min/max
- location
- skills_required (array)
- experience_required
- job_url
- scraped_at
- status (active/filled)

### Application
- id (PK)
- user_id (FK)
- job_id (FK)
- applied_at
- status (applied/rejected/interview/offer)
- custom_resume_path
- cover_letter
- response_received_at

## API Endpoints

### Jobs
- `GET /api/jobs` - List all jobs
- `GET /api/jobs/{id}` - Get job details
- `POST /api/jobs/search` - Advanced search
- `GET /api/jobs/recommended` - AI-recommended jobs

### Applications
- `GET /api/applications` - List user applications
- `POST /api/applications/{job_id}` - Apply to job
- `GET /api/applications/{id}` - Application details
- `PATCH /api/applications/{id}` - Update status

### Resumes
- `GET /api/resumes` - List user resumes
- `POST /api/resumes/upload` - Upload resume
- `POST /api/resumes/{id}/optimize` - Optimize for job

### Scheduler
- `POST /api/scheduler/start` - Start automation
- `POST /api/scheduler/stop` - Stop automation
- `GET /api/scheduler/status` - Check status

## Key Services

### Job Matcher
Scores jobs based on:
- Skill match percentage
- Experience level match
- salary range compatibility
- Location preference

### Resume Optimizer
Uses Claude to:
- Extract job requirements
- Customize resume sections
- Reorder experience relevance
- Add ATS-friendly keywords

### Auto-Applicator
Handles:
- Form detection & parsing
- Field auto-fill
- Captcha detection (logs for manual review)
- Custom answer generation via Claude

## Dependencies

```
fastapi==0.104.0
uvicorn==0.24.0
sqlalchemy==2.0.0
psycopg2-binary==2.9.0
requests==2.31.0
selenium==4.15.0
playwright==1.40.0
anthropic==0.7.0
apscheduler==3.10.0
pydantic==2.5.0
pydantic-settings==2.1.0
python-jose==3.3.0
passlib==1.7.4
pytest==7.4.0
```

## Development

```bash
# Install dependencies
pip install -r requirements.txt

# Run migrations
alembic upgrade head

# Start server
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000 --app-dir .

# Run tests
pytest -v

# Check code quality
black app/
flake8 app/

# Create a new migration after model changes
alembic revision --autogenerate -m "describe change"
```

## Neon PostgreSQL Setup

1. Copy `.env.example` to `.env`.
2. Paste your Neon connection string into `DATABASE_URL` with `sslmode=require`.
3. Run migrations:

```bash
alembic upgrade head
```

4. Start backend:

```bash
uvicorn app.main:app --host 127.0.0.1 --port 8000 --app-dir .
```

## Quick Start Script (Windows)

From the backend folder:

```powershell
.\start_backend.ps1
```

This applies Alembic migrations and starts FastAPI.

## Jobs Digest Notes

- Configure SMTP variables in `.env` before calling `/api/jobs/digest`.
- Jobs are scraped from configured India sources via `/api/jobs/scrape`.
- Save user digest preferences using `/api/jobs/preferences`.

## Production Deployment

See `/deployment` directory for Docker, AWS, and Kubernetes setup.

## Current V1 Runtime Notes

- Authentication is required (`AUTH_ENABLED=true`).
- Resume retention defaults to 15 days (`RESUME_RETENTION_DAYS=15`).
- Resume upload persists an embedding vector for semantic matching.
- Job scrape persists job embeddings and returns top embedding matches when `resume_id` is provided.
- Login and upload trigger automation runs (scrape + match; email if configured and enabled).
- Per-user scheduler controls are saved through `/api/jobs/preferences`:
	- `auto_schedule_enabled`
	- `schedule_time`
	- `schedule_timezone`
	- `auto_scrape_on_login`
	- `auto_email_after_scrape`
- Autofill endpoint `/api/applications/autofill` is currently on hold and returns `503`.
