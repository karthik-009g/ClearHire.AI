# V1 Technical Architecture

## Goal
Ship a low-cost production-ready V1 of an agentic job application assistant with explainable resume/JD matching.

## Core Components
- Frontend: Next.js web app for upload, matching view, and job tracker.
- Backend: FastAPI app for parsing, matching, generation, and persistence.
- Database: PostgreSQL for users (optional), resumes, resume versions, jobs, and application tracking.
- File storage:
  - V1: local filesystem volume.
  - V2: S3-compatible object storage.

## Functional Flow
1. User uploads resume (PDF/DOCX).
2. Backend validates file type and size.
3. Parser extracts structured text blocks (skills, experience, projects).
4. User provides/picks job description.
5. Matcher computes:
   - explainable keyword overlap score
   - embedding similarity score
   - combined weighted score and missing keyword set
6. Tailoring engine creates controlled resume edits and optional cover letter.
7. System stores resume version and generated apply-ready package.
8. Job tracker updates status (pending/applied).

## Data Model (V1)
- users (optional in V1): id, email, created_at.
- resumes: id, user_id, original_file_path, parsed_summary_json, created_at, expires_at.
- resume_versions: id, resume_id, version_no, content_json_or_text, created_at.
- job_descriptions: id, source, title, company, jd_text, created_at.
- matches: id, resume_id, job_id, keyword_score, embedding_score, total_score, gaps_json, created_at.
- applications: id, job_id, resume_version_id, status, notes, updated_at.

## Security Baseline (V1)
- HTTPS at ingress.
- File validation and hard size limit.
- Basic request validation and sanitization.
- Do not log raw resume text or full JD payloads.
- Add retention cleanup for files/data older than 30 days.

## Performance Targets
- Parse + score target under 5 seconds for typical resumes.
- No background queue required in V1.
- Optional basic rate limiting if abuse appears.

## Deployment Shape
- Single Docker image for backend service.
- Managed Postgres (Railway/Render/Supabase alternative if needed).
- Frontend static/server deployment on same provider family.
- Low-cost budget mode under $20/month.

## V2 Hooks (Not in V1)
- n8n workflow automation.
- S3 file storage.
- LLM-based rewriting.
- Optional ATS integrations.
