# jobswithc.ai
# 🚀 ClearHire.ai — AI-Powered Job Application Assistant

> **A full-stack AI product built to help candidates land jobs smarter — not harder.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat&logo=python&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat&logo=fastapi&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=flat&logo=postgresql&logoColor=white)](https://postgresql.org)
[![Streamlit](https://img.shields.io/badge/Streamlit-Frontend-FF4B4B?style=flat&logo=streamlit&logoColor=white)](https://streamlit.io)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat&logo=docker&logoColor=white)](https://docker.com)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=flat)]()

---

## 📌 What Is This Project?

**ClearHire.ai** is an end-to-end agentic job application assistant I designed and built from scratch. It combines **NLP-powered resume analysis**, **semantic job matching**, and **automated email digests** into a production-grade web application.

The project addresses a real problem: job seekers waste hours tailoring resumes and manually sifting through job listings. ClearHire automates the repetitive parts so candidates can focus on what actually matters — preparing for interviews.

This is a solo full-stack build covering backend APIs, NLP pipelines, database design, auth systems, scheduling, and a multi-page frontend.

---

## 🎯 Key Features

| Feature | Description |
|---|---|
| 🔐 **JWT Authentication** | Secure register/login with token-based auth |
| 📄 **Smart Resume Upload** | File safety validation (extension + MIME + signature checks) |
| 🧠 **Semantic Job Matching** | Dual-score matching using keyword overlap + sentence embeddings |
| ✍️ **AI Resume Tailoring** | Auto-generates tailored resume versions per job description |
| 📦 **Apply-Ready Export** | Packages tailored resume into a downloadable ZIP |
| 🔍 **Job Scraping Engine** | Scrapes India-focused job boards on demand or on login |
| 📬 **Email Digest Automation** | Sends top-matched job alerts via SMTP scheduler |
| 📊 **Application Tracker** | Full CRUD for tracking job application status |
| ⚙️ **User Preferences** | Per-user role, location, keyword, and schedule config |

---

## 🛠️ Tech Stack

### Backend
- **FastAPI** — REST API with automatic OpenAPI docs
- **PostgreSQL** — Relational database (Neon-compatible for cloud)
- **SQLAlchemy + Alembic** — ORM and schema migrations
- **spaCy + sentence-transformers** — NLP pipeline for matching and parsing
- **APScheduler** — Cron-based job digest automation
- **JWT (python-jose)** — Stateless authentication

### Frontend
- **Streamlit** — Multi-page interactive web client (active)
- **React scaffold** — Future web frontend (in progress)

### DevOps
- **Docker Compose** — One-command local environment
- **AWS + Kubernetes scaffolding** — Cloud-ready deployment assets

---

## 🧠 How the Matching Engine Works

```
User Resume  ──►  spaCy Parser  ──►  Keyword Extraction
                                          │
Job Description ──►  Embedding Model  ──►  Cosine Similarity Score
                                          │
                              ┌───────────▼───────────┐
                              │  Keyword Score (40%)  │
                              │  Embedding Score (60%) │
                              │  → Final Match Score  │
                              │  → Explanation Text   │
                              └───────────────────────┘
```

The system uses **sentence-transformers** to embed both the resume and job description into vector space, then computes cosine similarity. This goes beyond keyword matching to understand semantic meaning — catching synonyms and related skills that naive keyword search misses.

---

## 📁 Project Structure

```
clearhire.ai/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── api/               # Route handlers
│   │   ├── services/          # Business logic (matching, tailoring, scraping)
│   │   ├── models/            # SQLAlchemy ORM models
│   │   └── core/              # Auth, config, database
│   ├── migrations/            # Alembic migrations
│   └── tests/                 # Pytest test suite
│
├── streamlit-client/           # Active frontend (multi-page Streamlit app)
│   └── app.py
│
├── frontend/                   # Future React frontend scaffold
├── deployment/
│   ├── docker/                # Docker Compose setup
│   ├── aws/                   # AWS deployment assets
│   └── kubernetes/            # K8s manifests
│
└── docs/                       # Architecture and API documentation
```

---

## ⚡ Getting Started (Local Setup)

### Prerequisites
- Python 3.11+
- PostgreSQL 14+
- Docker (optional but recommended)

### Option 1 — Docker (Fastest)

```bash
cd deployment/docker
docker-compose up -d
```

### Option 2 — Manual Setup

**1. Start the Backend**

```bash
cd backend
python -m venv .venv && source .venv/bin/activate   # Linux/Mac
# OR: .\.venv\Scripts\activate                       # Windows

pip install -r requirements.txt

# Copy and configure your environment variables
cp .env.example .env

# Run database migrations
alembic upgrade head

# Start the server
uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

**2. Start the Frontend**

```bash
cd streamlit-client
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
streamlit run app.py
```

**3. Access the App**

| Service | URL |
|---|---|
| Streamlit Frontend | http://localhost:8501 |
| FastAPI Backend | http://127.0.0.1:8000 |
| Swagger API Docs | http://127.0.0.1:8000/docs |

---

## 🔑 Environment Variables

Create `backend/.env` with:

```env
# Database
DATABASE_URL=postgresql://user:password@localhost:5432/clearhire

# Auth
SECRET_KEY=your-secret-key-here
AUTH_ENABLED=true

# Resume
RESUME_RETENTION_DAYS=15

# NLP Models
EMBEDDING_MODEL_NAME=all-MiniLM-L6-v2
SPACY_MODEL=en_core_web_sm

# Email (for job digests)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your@email.com
SMTP_PASSWORD=your-app-password
SMTP_SENDER_EMAIL=your@email.com
```

---

## 📡 API Reference

### Authentication
```
POST   /api/auth/register          Register a new user
POST   /api/auth/login             Login and get JWT token
GET    /api/auth/me                Get current user profile
```

### Resume Operations
```
POST   /api/resumes/upload         Upload and parse a resume
POST   /api/resumes/match          Semantic match against a job description
POST   /api/resumes/tailor         Generate a tailored resume version
POST   /api/resumes/package/tailor Export apply-ready ZIP package
GET    /api/resumes/{id}           Fetch resume by ID
GET    /api/resumes/{id}/versions  Get all tailored versions
```

### Jobs
```
POST   /api/jobs/scrape            Trigger job scraping
POST   /api/jobs/preferences       Set user job preferences
GET    /api/jobs/preferences       Get current preferences
POST   /api/jobs/digest            Trigger email digest manually
```

### Applications
```
POST   /api/applications/                        Create new application entry
GET    /api/applications/                        List all applications
PATCH  /api/applications/{id}/status             Update application status
```

---

## 🧪 Running Tests

```bash
cd backend
pytest -q
```

---

## 🗺️ Roadmap

- [x] JWT authentication system
- [x] Resume upload with safety validation
- [x] Semantic matching engine (keyword + embedding)
- [x] Tailored resume generation with version history
- [x] Job scraping from India-focused job boards
- [x] Automated email digest with APScheduler
- [x] Application tracker (CRUD)
- [ ] LinkedIn Jobs integration (API-compliant)
- [ ] Naukri integration (API-compliant)
- [ ] Auto job application form filling
- [ ] React-based frontend (replacing Streamlit)
- [ ] ATS integrations for enterprise workflows

---

## 🔒 Security Highlights

- All uploaded files are validated by **extension**, **MIME type**, and **file signature** before processing
- JWT tokens are stateless and expire on timeout
- Ownership checks enforced on all resume/application resources
- Raw resume text is never logged in production
- Password hashing with bcrypt

---

## 💡 What I Learned Building This

- Designing a **multi-service architecture** with clean separation between API, service, and data layers
- Implementing **dual-mode semantic search** (keyword + dense vector embeddings) for ranking
- Handling **background scheduling** (APScheduler) with per-user timezone-aware preferences
- Writing **production-grade file validation** beyond just extension checking
- Structuring a **FastAPI project** for real-world maintainability with Alembic migrations

---

## 👨‍💻 About

Built by a CS student passionate about building AI-powered tools that solve real problems.

This project was built to demonstrate full-stack engineering skills across backend APIs, NLP, database design, scheduling systems, and frontend development — all production-ready.

> ⭐ If you found this project interesting, feel free to star it!

---

*Note: Auto-fill for direct job applications is intentionally disabled in V1 pending platform policy review.*
