"""Automation orchestration for login-triggered and scheduled scrape/match/email flows."""

from __future__ import annotations

from datetime import datetime

from sqlalchemy.orm import Session

from app.models import JobPosting, Resume, ResumeVersion, User, UserPreference
from app.services.email_service import EmailService
from app.services.job_scraper_service import JobScraperService, ScrapedJob, SOURCES
from app.services.matcher_service import ResumeMatcherService
from app.utils.config import settings


class AutomationService:
    def __init__(self) -> None:
        self.scraper = JobScraperService()
        self.matcher = ResumeMatcherService(
            embedding_model_name=settings.embedding_model_name,
            embedding_dimensions=settings.embedding_dimensions,
        )
        self.emailer = EmailService()

    @staticmethod
    def _embedding_invalid(vector: list[float] | None) -> bool:
        return vector is None or len(vector) != settings.embedding_dimensions

    @staticmethod
    def _parse_csv(csv_value: str | None) -> list[str]:
        return [x.strip() for x in (csv_value or "").split(",") if x.strip()]

    def _effective_sources(self, pref: UserPreference | None) -> list[str]:
        if pref and pref.selected_sources_csv:
            requested = self._parse_csv(pref.selected_sources_csv)
            selected = [source for source in requested if source in SOURCES]
            if selected:
                return selected
        return list(SOURCES.keys())

    def _upsert_jobs(self, db: Session, scraped: list[ScrapedJob]) -> list[JobPosting]:
        rows: list[JobPosting] = []
        for item in scraped:
            row = db.query(JobPosting).filter(JobPosting.url == item.url).first()
            embedding = self.matcher.embed_text(f"{item.title}\n{item.description or ''}")
            if not row:
                row = JobPosting(
                    source=item.source,
                    company=item.company,
                    title=item.title,
                    location=item.location,
                    url=item.url,
                    description=item.description,
                    embedding=embedding,
                    embedding_vector=embedding,
                    scraped_at=item.scraped_at,
                )
                db.add(row)
                db.flush()
            else:
                row.source = item.source
                row.company = item.company
                row.title = item.title
                row.location = item.location
                row.description = item.description
                row.embedding = embedding
                row.embedding_vector = embedding
                row.scraped_at = datetime.utcnow()
            rows.append(row)
        return rows

    def _rank_jobs(
        self,
        jobs: list[JobPosting],
        resume_embedding: list[float] | None,
        keywords: list[str],
    ) -> list[JobPosting]:
        ranked: list[JobPosting] = []
        for job in jobs:
            title = (job.title or "").lower()
            description = (job.description or "").lower()
            weighted_hits = 0.0
            for kw in keywords:
                kw_l = kw.lower().strip()
                if not kw_l:
                    continue
                if kw_l in title:
                    weighted_hits += 2.0
                elif kw_l in description:
                    weighted_hits += 1.0
            keyword_score = min(100.0, weighted_hits * 18.0) if keywords else 0.0

            semantic_score = 0.0
            if resume_embedding and job.embedding and len(resume_embedding) == len(job.embedding):
                similarity = self.matcher.cosine_similarity(resume_embedding, job.embedding)
                semantic_score = max(0.0, ((similarity + 1.0) / 2.0) * 100.0)

            recency_score = 50.0
            if job.scraped_at:
                hours_old = max(0.0, (datetime.utcnow() - job.scraped_at).total_seconds() / 3600.0)
                recency_score = max(10.0, 100.0 - (hours_old * 2.5))
                if hours_old <= 24:
                    recency_score = min(100.0, recency_score + 8.0)

            # If there are no user keywords, avoid over-penalizing role-compatible results.
            if not keywords and any(token in title for token in ("engineer", "developer", "analyst", "intern", "sde")):
                keyword_score = max(keyword_score, 35.0)

            job.score = round((0.58 * semantic_score) + (0.30 * keyword_score) + (0.12 * recency_score), 2)
            ranked.append(job)

        return sorted(ranked, key=lambda row: (row.score or 0.0), reverse=True)

    @staticmethod
    def _render_digest_html(ranked_jobs: list[JobPosting], top_n: int = 20) -> str:
        if not ranked_jobs:
            return "<html><body><h3>No matching jobs found in latest run.</h3></body></html>"

        items = []
        for job in ranked_jobs[:top_n]:
            items.append(
                "<li>"
                f"<b>{job.title}</b> - {job.company} ({job.source}) "
                f"[score: {job.score}] "
                f"<a href=\"{job.url}\">Open Application</a>"
                "</li>"
            )

        return (
            "<html><body>"
            "<h3>Your top matched jobs</h3>"
            "<p>These jobs are ranked with embedding similarity + keyword relevance.</p>"
            "<ul>"
            + "".join(items)
            + "</ul>"
            "</body></html>"
        )

    def run_user_automation(self, db: Session, user_id: str, trigger: str) -> dict:
        user = db.query(User).filter(User.id == user_id).first()
        if not user:
            return {"status": "skipped", "reason": "user_not_found"}

        pref = db.query(UserPreference).filter(UserPreference.user_id == user_id).first()
        if trigger == "login" and pref and not pref.auto_scrape_on_login:
            return {"status": "skipped", "reason": "auto_scrape_on_login_disabled"}

        resume = (
            db.query(Resume)
            .filter(Resume.user_id == user_id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        if not resume:
            return {"status": "skipped", "reason": "no_resume"}

        version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume.id)
            .order_by(ResumeVersion.version_no.desc())
            .first()
        )
        if not version:
            return {"status": "skipped", "reason": "no_resume_version"}

        if self._embedding_invalid(version.embedding):
            resume_context = self.matcher.build_resume_context(
                version.content_text,
                parsed_summary=resume.parsed_summary,
            )
            version.embedding = self.matcher.embed_text(resume_context)
        if self._embedding_invalid(version.embedding_vector):
            version.embedding_vector = version.embedding

        keywords = self._parse_csv(pref.keywords_csv if pref else None)
        sources = self._effective_sources(pref)
        posted_within_hours = (
            settings.default_scrape_posted_within_hours
            if settings.default_scrape_posted_within_hours > 0
            else None
        )
        scraped_jobs = self.scraper.scrape_sources(
            source_keys=sources,
            keywords=keywords,
            max_post_age_hours=posted_within_hours,
        )
        stored_jobs = self._upsert_jobs(db, scraped_jobs)
        ranked_jobs = self._rank_jobs(stored_jobs, version.embedding, keywords)

        sent_to = None
        email_error = None
        recipient = (pref.preferred_email if pref and pref.preferred_email else user.email).strip()
        should_send_mail = settings.automation_email_enabled and (bool(pref.auto_email_after_scrape) if pref else True)
        if should_send_mail and self.emailer.is_configured() and recipient:
            html = self._render_digest_html(ranked_jobs)
            try:
                self.emailer.send_html_email(
                    to_email=recipient,
                    subject="Top matched jobs for your resume",
                    html_body=html,
                )
                sent_to = recipient
            except Exception as exc:  # pragma: no cover - SMTP/network provider variance
                email_error = str(exc)

        db.commit()

        return {
            "status": "ok",
            "jobs_scraped": len(stored_jobs),
            "top_matches": [
                {
                    "job_id": row.id,
                    "title": row.title,
                    "company": row.company,
                    "url": row.url,
                    "score": row.score,
                }
                for row in ranked_jobs[:10]
            ],
            "sent_to": sent_to,
            "email_error": email_error,
        }

    @staticmethod
    def build_application_autofill(
        parsed_summary: dict,
        resume_version: ResumeVersion,
        job: JobPosting,
    ) -> dict:
        skills = parsed_summary.get("skills", []) if isinstance(parsed_summary, dict) else []
        sections = parsed_summary.get("sections", {}) if isinstance(parsed_summary, dict) else {}
        experience_lines = sections.get("experience", []) if isinstance(sections, dict) else []

        return {
            "full_name": "Candidate",
            "email": "",
            "phone": "",
            "target_role": job.title,
            "target_company": job.company,
            "location_preference": job.location or "India",
            "skills": skills,
            "experience_highlights": experience_lines[:5],
            "resume_version_id": resume_version.id,
            "resume_excerpt": resume_version.content_text[:1800],
            "job_url": job.url,
            "job_source": job.source,
            "review_required": True,
            "instructions": "Validate all fields before submitting to employer portal.",
        }
