# V1 Execution Plan

## Phase 1 - Backend Foundation
- Implement Postgres models for resumes, versions, jobs, matches, applications.
- Add file upload endpoint with validation:
  - extensions: pdf, docx
  - size <= 10 MB
- Add parser services for PDF and DOCX.
- Add 30-day retention cleanup command/script.

## Phase 2 - Matching Engine
- Implement keyword overlap extractor and weighted scoring.
- Implement embedding similarity module.
- Define transparent score formula and explanation payload.
- Persist score breakdown and gaps in matches table.

## Phase 3 - Tailored Output
- Controlled resume tailoring service (non-LLM deterministic template edits for V1).
- Optional cover letter generator (template-driven).
- Build apply-ready package output bundle.

## Phase 4 - Web Experience
- Upload page with parser preview.
- JD input and match result page.
- Tailored output preview + download.
- Job tracking page with pending/applied states.

## Phase 5 - Quality and Release
- Unit tests:
  - parser modules
  - matcher score logic
- Manual test checklist for end-to-end user journeys.
- Dockerize and deploy to Render or Railway.
- Dev and Prod environments.

## Definition of Done (V1)
- Resume upload and parse working for PDF/DOCX.
- JD-resume score with explainable components available in UI.
- Tailored resume output generated in controlled style.
- Job tracking state update works.
- Retention cleanup for 30 days enforced.
- No raw resume text in application logs.
