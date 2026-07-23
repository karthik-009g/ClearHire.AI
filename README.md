# ClearHire.AI

# 🚀 ClearHire.ai — AI-Powered Job Application Assistant

> **A full-stack AI product built to help candidates land jobs smarter — not harder.**

[![Python](https://img.shields.io/badge/Python-3.11+-3776AB?style=flat\&logo=python\&logoColor=white)](https://python.org)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.100+-009688?style=flat\&logo=fastapi\&logoColor=white)](https://fastapi.tiangolo.com)
[![PostgreSQL](https://img.shields.io/badge/PostgreSQL-14+-336791?style=flat\&logo=postgresql\&logoColor=white)](https://postgresql.org)
[![Next.js](https://img.shields.io/badge/Next.js-Frontend-000000?style=flat\&logo=nextdotjs\&logoColor=white)](https://nextjs.org)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ED?style=flat\&logo=docker\&logoColor=white)](https://docker.com)
[![Status](https://img.shields.io/badge/Status-Active%20Development-brightgreen?style=flat)]()

---

## 📌 What Is This Project?
  
**ClearHire.ai** is a modular **AI Career Engine** that automates and optimizes the job search workflow using intelligent pipelines.

Instead of manually:

* analyzing job descriptions
* tailoring resumes
* searching for relevant jobs

ClearHire builds a **connected AI system** that performs these tasks end-to-end.

---

## 🧠 System Architecture (Core Idea)

ClearHire is designed as a **multi-module AI pipeline**, not a single script:

```
Resume → Resume Intelligence → JD Analysis → Job Matching → Insights
```

Each module operates independently but shares context across the system.

---

## ⚙️ Core Modules

### 🧭 Mission Control (Dashboard)

Central control layer of the system.

* Tracks resume readiness
* Displays match results
* Monitors skill gaps
* Provides system-wide overview

---

### 📄 ResMat.ai (Resume Intelligence Engine)

* Upload and parse resume (PDF/DOCX)
* Extract structured skills
* Generate embeddings
* Maintain resume context across modules

👉 Feeds data into JD Analyzer

---

### 🔍 JD Analyzer

* Input job description + company
* Compute:

  * Match Score
  * Keyword Score
  * Embedding Similarity
* Generate:

  * Target tech stack
  * Skill gap analysis
  * Market signals

---

### 🎯 Job Hunter

* Searches jobs from sources (LinkedIn, Naukri)
* Ranks jobs using resume context
* Outputs prioritized job opportunities

Features:

* Resume-aware ranking
* Skill-based filtering
* Time-based filtering

---

### 🧪 Student Lab

* Tracks learning path
* Suggests improvements
* Aligns skills with target roles

---

## 🧠 Matching Logic

Hybrid scoring system:

* **Keyword Match → explicit skill overlap**
* **Embedding Similarity → semantic understanding**

Final score combines both:

```
Match Score = weighted(keyword_score, embedding_score)
```

---

## 🖥️ Application Flow

1. Upload Resume → ResMat.ai
2. Analyze JD → JD Analyzer
3. Compute Match → Skill Gap + Score
4. Search Jobs → Job Hunter
5. Track Insights → Mission Control

---

## 🛠️ Tech Stack

### Backend

* FastAPI
* PostgreSQL
* SQLAlchemy

### AI / NLP

* Sentence Transformers
* Keyword extraction
* Resume parsing

### Frontend

* Next.js (React) web dashboard

### DevOps

* Docker support
* PowerShell automation scripts

---

## ▶️ Running the Application

### Start full system (Windows)

```powershell
./app.ps1
```

### Stop system

```powershell
./app.ps1 -Action stop
```

These scripts automate backend + frontend startup.

---

## 📁 Project Structure

```
clearhire-ai/
├── backend/
├── frontend/
├── docs/
├── deployment/
```

---

## Current Status

* Resume upload, PDF/DOCX parsing, skill extraction, version history, and 30-day retention
* Explainable JD matching with keyword gaps and embedding similarity
* ATS-focused one-page resume tailoring and apply-ready ZIP export
* Job discovery, resume-aware ranking, and pending/applied application tracking
* Authenticated multi-module UI system

---

## Future Work

The V1 product scope is complete. Future work is intentionally outside V1:

* [ ] Opt-in assisted application workflows (never autonomous submission)
* [ ] Additional compliant job sources and richer job metadata
* [ ] Optional LLM-assisted rewriting with explicit user review
* [ ] Deployment automation and production observability

---

## Boundaries

* Applications are tracked, but ClearHire does not submit them automatically.
* Job discovery depends on the availability and terms of the configured sources.
* Tailoring preserves the candidate's supplied experience and does not invent claims.

---

## 💡 Engineering Highlights

* Modular AI pipeline design
* Hybrid semantic + keyword matching
* Cross-module shared state (resume → JD → jobs)
* Production-style backend architecture

---

## 👨‍💻 About

Built as a full-stack AI system focusing on:

* LLM systems
* semantic search
* agent-based workflows

> ⭐ Star the repo if you find it useful

---

*Note: Auto-application is planned but not included in current version.*
