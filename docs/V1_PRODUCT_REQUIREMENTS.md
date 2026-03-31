# Agentic Job Application Assistant - V1 Product Requirements

## 1. Product Scope
- Product type: Agentic assistant for job applications, not a full auto-apply bot.
- Interface: Web app only (no public API in V1).
- Primary user: Candidate.
- Deployment model: Single-user first, designed for later SaaS expansion.

### V1 Features
- Resume upload: PDF and DOCX.
- Resume parsing: skills, experience, projects.
- Job discovery: basic scraping and/or available job APIs.
- JD-resume matching: score plus gap explanation.
- Tailored resume generation: controlled edits (no aggressive rewriting).
- Optional cover letter generation.
- Apply-ready package export.
- Job tracking states: applied, pending.

## 2. Users and Access
- User roles in V1: none (candidate only).
- Expected load:
  - Launch: 5-20 concurrent users.
  - 6 months: up to 100 users.
- Authentication: optional in V1 to accelerate delivery.
- Multi-tenancy: not required in V1.

## 3. AI and Analysis Strategy
- V1 approach: hybrid matching.
  - Rule-based ATS heuristics (explainable).
  - Embedding similarity for semantic JD matching.
- Language support: English only.
- Scoring requirement: explainable and transparent (not black-box).
- Rewrite modes: not required in V1.
- V2 direction: optional LLM-powered rewriting.

## 4. Data and Storage
- Database: PostgreSQL.
- Resume storage: required.
- Retention: 30 days.
- Version history: required.
- Audit logs: minimal basic tracking.
- File storage:
  - V1: local disk.
  - V2+: migrate to S3.

## 5. Security and Compliance (V1)
- Treat resume and profile data as real PII.
- Mention GDPR and DPDP considerations in architecture and docs.
- Encryption in transit: HTTPS required.
- Encryption at rest: optional in V1.
- Upload safety:
  - File type validation.
  - Size limit <= 10 MB.
- Logging safety: do not log raw resume text.

## 6. Infrastructure and DevOps
- Hosting preference: Render or Railway for low-cost launch.
- Packaging: Dockerized app.
- Region: no strict geo constraint.
- SLA: best-effort uptime.
- Budget target: < $20/month at initial stage.

## 7. Performance and Reliability
- Upload size target: 5-10 MB.
- Analysis latency target: < 5 seconds per resume/JD pair.
- Async jobs: not required in V1.
- Rate limiting: optional basic control.
- Caching: not required in V1.

## 8. Integrations
- n8n: excluded from V1, reconsider in V2.
- ATS integrations: excluded in V1.
- Storage integrations (Drive/S3): optional later.
- Email notifications: optional V2.
- Webhooks: not required in V1.

## 9. Observability and Ops
- Logging: basic structured logs.
- Alerting: not required in V1.
- Analytics: minimal usage tracking.
- Feature flags: not required.
- Runbooks: not required.

## 10. QA and Release
- Testing strategy:
  - Basic unit tests for parser and matcher.
  - Manual scenario testing.
- CI/CD: optional GitHub Actions.
- Environments: dev and prod only.
- Rollback: manual redeploy.
- API versioning: not required in V1.
