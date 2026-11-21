"""Automation orchestration for login-triggered and scheduled scrape/match/email flows."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
import re

from sqlalchemy.orm import Session

from app.models import JobPosting, Resume, ResumeVersion, User, UserPreference
from app.services.authenticity_service import AuthenticityService
from app.services.email_service import EmailService
from app.services.job_scraper_service import JobScraperService, ScrapedJob, SOURCES
from app.services.direct_ats_service import DirectAtsService
from app.services.location_service import india_or_remote_only, matches_locations
from app.services.matcher_service import ResumeMatcherService
from app.utils.config import settings


def _is_detected_staffing_agency(job: JobPosting) -> bool:
    signals = getattr(job, "ghosting_signals", None)
    return isinstance(signals, dict) and signals.get("is_staffing_agency") is True


class AutomationService:
    def __init__(self) -> None:
        self.scraper = JobScraperService()
        self.direct_ats = DirectAtsService()
        self.authenticity = AuthenticityService()
        self.matcher = ResumeMatcherService(
            embedding_model_name=settings.embedding_model_name,
            embedding_dimensions=settings.embedding_dimensions,
            load_embedding_model=settings.embedding_load_local_model,
        )
        self.emailer = EmailService()

    @staticmethod
    def _embedding_invalid(vector: list[float] | None) -> bool:
        return vector is None or len(vector) != settings.embedding_dimensions

    @staticmethod
    def _parse_csv(csv_value: str | None) -> list[str]:
        return [x.strip() for x in (csv_value or "").split(",") if x.strip()]

    @staticmethod
    def _contains_keyword(text: str, keyword: str) -> bool:
        phrase = re.escape(keyword.strip().casefold()).replace(r"\ ", r"\s+")
        return bool(phrase and re.search(rf"(?<!\w){phrase}(?!\w)", text.casefold()))

    def _effective_sources(self, pref: UserPreference | None) -> list[str]:
        if pref and pref.selected_sources_csv:
            requested = self._parse_csv(pref.selected_sources_csv)
            selected = list(dict.fromkeys(source for source in requested if source == "direct_ats" or source in SOURCES))
            return selected or ["direct_ats"]
        return ["direct_ats"]

    def _upsert_jobs(self, db: Session, scraped: list[ScrapedJob]) -> list[JobPosting]:
        rows: list[JobPosting] = []
        if not scraped:
            return rows

        urls = [item.url for item in scraped if item.url]
        existing_map = {
            jp.url: jp
            for jp in db.query(JobPosting).filter(JobPosting.url.in_(urls)).all()
        } if urls else {}

        unique_scraped = {}
        for item in scraped:
            if item.url:
                unique_scraped.setdefault(item.url, item)
        scraped = list(unique_scraped.values())
        texts = [f"{item.title}\n{item.description or ''}" for item in scraped]
        embeddings = self.matcher.embed_texts_batch(texts)

        for item, embedding in zip(scraped, embeddings):
            analysis = self.authenticity.analyze(
                title=item.title,
                company=item.company,
                url=item.url,
                description=item.description,
                source=item.source,
                posted_at=getattr(item, "posted_at", None),
            )

            row = existing_map.get(item.url)
            if not row:
                row = JobPosting(
                    source=item.source,
                    company=item.company,
                    title=item.title,
                    location=item.location,
                    url=item.url,
                    description=item.description,
                    posted_at=getattr(item, "posted_at", None),
                    embedding=embedding,
                    embedding_vector=embedding,
                    scraped_at=item.scraped_at,
                    source_type=analysis.source_type,
                    ghosting_risk=analysis.ghosting_risk,
                    authenticity_score=analysis.authenticity_score,
                    is_direct_employer=analysis.is_direct_employer,
                    is_evergreen=analysis.is_evergreen,
                    ats_provider=analysis.ats_provider,
                    ghosting_signals=analysis.ghosting_signals,
                )
                db.add(row)
            else:
                row.source = item.source
                row.company = item.company
                row.title = item.title
                row.location = item.location
                row.description = item.description
                if getattr(item, "posted_at", None) is not None:
                    row.posted_at = item.posted_at
                row.embedding = embedding
                row.embedding_vector = embedding
                row.scraped_at = datetime.utcnow()
                row.source_type = analysis.source_type
                row.ghosting_risk = analysis.ghosting_risk
                row.authenticity_score = analysis.authenticity_score
                row.is_direct_employer = analysis.is_direct_employer
                row.is_evergreen = analysis.is_evergreen
                row.ats_provider = analysis.ats_provider
                row.ghosting_signals = analysis.ghosting_signals
            rows.append(row)
        db.flush()
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
            normalized_keywords = list(dict.fromkeys(kw.strip().casefold() for kw in keywords if kw.strip()))
            for kw in normalized_keywords:
                if self._contains_keyword(title, kw):
                    weighted_hits += 2.0
                elif self._contains_keyword(description, kw):
                    weighted_hits += 1.0
            keyword_score = min(100.0, weighted_hits * 18.0) if keywords else 0.0

            semantic_score = 0.0
            if resume_embedding and job.embedding and len(resume_embedding) == len(job.embedding):
                similarity = self.matcher.cosine_similarity(resume_embedding, job.embedding)
                semantic_score = max(0.0, ((similarity + 1.0) / 2.0) * 100.0)

            posting_recency_score = 50.0
            if job.posted_at:
                now_utc = datetime.now(timezone.utc)
                posted_dt = job.posted_at if getattr(job.posted_at, "tzinfo", None) else job.posted_at.replace(tzinfo=timezone.utc)
                hours_old = max(0.0, (now_utc - posted_dt).total_seconds() / 3600.0)
                posting_recency_score = max(10.0, 100.0 - (hours_old * 2.5))
                if hours_old <= 24:
                    posting_recency_score = min(100.0, posting_recency_score + 8.0)

            # If there are no user keywords, avoid over-penalizing role-compatible results.
            if not keywords and any(self._contains_keyword(title, token) for token in ("engineer", "developer", "analyst", "intern", "sde")):
                keyword_score = max(keyword_score, 35.0)

            auth_score = getattr(job, "authenticity_score", 50.0) if getattr(job, "authenticity_score", None) is not None else 50.0

            weights = {
                "semantic_similarity": 50.0,
                "keyword_overlap": 25.0,
                "posting_recency": 10.0,
                "listing_source_signals": 15.0,
            }
            job.score_components = {
                "semantic_similarity": round(semantic_score, 2),
                "keyword_overlap": round(keyword_score, 2),
                "posting_recency": round(posting_recency_score, 2),
                "listing_source_signals": round(auth_score, 2),
            }
            job.score_weights = weights
            job.score_availability = {
                "semantic_similarity": bool(resume_embedding and job.embedding and len(resume_embedding) == len(job.embedding)),
                "keyword_overlap": bool(normalized_keywords),
                "posting_recency": job.posted_at is not None,
                "listing_source_signals": getattr(job, "authenticity_score", None) is not None,
            }
            job.score_formula = "50% semantic similarity + 25% keyword overlap + 10% source-reported date recency + 15% heuristic listing-source signals; unknown source dates receive a neutral recency score"
            job.ranking_score = round(sum(job.score_components[key] * weight / 100.0 for key, weight in weights.items()), 2)
            ranked.append(job)

        return sorted(ranked, key=lambda row: (getattr(row, "ranking_score", 0.0) or 0.0), reverse=True)

    @staticmethod
    def _render_digest_html(ranked_jobs: list[JobPosting], top_n: int = 20) -> str:
        if not ranked_jobs:
            return "<html><body><h3>No matching jobs found in latest run.</h3></body></html>"

        items = []
        for job in ranked_jobs[:top_n]:
            risk = getattr(job, "ghosting_risk", "medium") or "medium"
            if risk == "low":
                badge = '<span style="color: #16a34a; font-weight: bold;">[🟢 Strong listing signals]</span>'
            elif risk == "high":
                badge = '<span style="color: #dc2626; font-weight: bold;">[🔴 Potential listing concern]</span>'
            else:
                badge = '<span style="color: #d97706;">[🟡 Mixed listing signals]</span>'

            ats_str = f" • ATS: {job.ats_provider.title()}" if getattr(job, "ats_provider", None) else ""
            items.append(
                "<li style='margin-bottom: 8px;'>"
                f"<b>{job.title}</b> - {job.company} ({job.source}{ats_str}) "
                f"{badge} "
                f"[Ranking score: {getattr(job, 'ranking_score', None)}] "
                f"<a href=\"{job.url}\" target=\"_blank\">Direct Apply</a>"
                "</li>"
            )

        return (
            "<html><body>"
            "<h3>ClearHire.AI — Your Top Matched Jobs</h3>"
            "<p>Ranking blends resume similarity, keyword overlap, source-reported dates, and listing heuristics. It is not a hiring or response probability.</p>"
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
        requested_locations = self._parse_csv(pref.locations_csv if pref else None)
        posted_within_hours = (
            pref.max_post_age_days * 24
            if pref and pref.max_post_age_days > 0
            else settings.default_scrape_posted_within_hours
            if settings.default_scrape_posted_within_hours > 0
            else None
        )
        scraped_jobs = self.scraper.scrape_sources(
            source_keys=sources,
            keywords=keywords,
            max_post_age_hours=posted_within_hours,
        )
        selected_source_names = sources
        if pref and (pref.direct_portals_only or "direct_ats" in selected_source_names):
            direct_jobs = self.direct_ats.fetch_all_direct_jobs(
                target_companies=self._parse_csv(pref.target_companies_csv),
                keywords=keywords,
                india_or_remote_only=india_or_remote_only(requested_locations),
                max_jobs=40,
            )
            if posted_within_hours is not None:
                cutoff = datetime.now(timezone.utc) - timedelta(hours=posted_within_hours)
                direct_jobs = [
                    item for item in direct_jobs
                    if not item.posted_at or (
                        (item.posted_at if item.posted_at.tzinfo else item.posted_at.replace(tzinfo=timezone.utc)) >= cutoff
                    )
                ]
            scraped_jobs = direct_jobs + scraped_jobs
        stored_jobs = self._upsert_jobs(db, scraped_jobs)
        eligible_jobs = [job for job in stored_jobs if matches_locations(job.location, requested_locations)]
        if pref and pref.direct_portals_only:
            eligible_jobs = [job for job in eligible_jobs if job.source_type in ("direct_ats", "company_career_page", "curated_startup")]
        if pref and pref.exclude_staffing_agencies:
            eligible_jobs = [job for job in eligible_jobs if not _is_detected_staffing_agency(job)]
        if pref and pref.max_ghosting_risk == "low_only":
            eligible_jobs = [job for job in eligible_jobs if job.ghosting_risk == "low"]
        elif pref and pref.max_ghosting_risk == "medium_and_low":
            eligible_jobs = [job for job in eligible_jobs if job.ghosting_risk in ("low", "medium")]
        ranked_jobs = self._rank_jobs(eligible_jobs, version.embedding, keywords)

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
                    "score": getattr(row, "ranking_score", None),
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
        # If an LLM provider is configured, prefer generating a structured autofill JSON.
        # Azure (optional placeholder): prefer Azure if configured (kept inert unless azure_api_base/key/deployment are set).
        if settings.llm_provider and settings.llm_provider.lower() == "azure" and settings.azure_api_base and settings.azure_api_key and settings.azure_deployment:
            try:
                import openai

                openai.api_type = "azure"
                openai.api_base = settings.azure_api_base
                openai.api_key = settings.azure_api_key
                # Use the configured deployment name as the engine/model
                messages = [
                    {"role": "system", "content": "You are a JSON generator. Respond only with JSON."},
                    {"role": "user", "content": (
                        "Convert resume and job posting data into a JSON autofill payload. "
                        "Respond ONLY with a single JSON object with keys: full_name, email, phone, target_role, target_company, "
                        "location_preference, skills, experience_highlights, resume_version_id, resume_excerpt, job_url, job_source, review_required, instructions. "
                        "Do not hallucinate facts; use empty strings or lists if unknown.\n\n"
                        f"Parsed summary:\n{parsed_summary}\n\nResume excerpt:\n{resume_version.content_text[:1800]}\n\n"
                        f"Job posting:\ntitle: {job.title}\ncompany: {job.company}\nlocation: {job.location}\nurl: {job.url}\nsource: {job.source}\n\n"
                        "Return compact JSON only."
                    )}
                ]

                completion = openai.ChatCompletion.create(engine=settings.azure_deployment, messages=messages, temperature=0.0, max_tokens=700)
                content = None
                if completion and getattr(completion, 'choices', None):
                    choice = completion.choices[0]
                    content = getattr(choice, 'message', {}).get('content') if isinstance(getattr(choice, 'message', None), dict) else None
                if not content and isinstance(completion, dict):
                    # fallback for some OpenAI client shapes
                    content = completion.get('choices', [{}])[0].get('message', {}).get('content')
                if content:
                    import json

                    try:
                        parsed = json.loads(content)
                        parsed.setdefault("resume_version_id", resume_version.id)
                        parsed.setdefault("resume_excerpt", resume_version.content_text[:1800])
                        parsed.setdefault("job_url", job.url)
                        parsed.setdefault("job_source", job.source)
                        parsed.setdefault("review_required", True)
                        return parsed
                    except Exception:
                        pass
            except Exception:
                pass

        if settings.llm_provider and settings.llm_provider.lower() == "groq" and settings.groq_api_key:
            try:
                from groq import Groq

                client = Groq(api_key=settings.groq_api_key)

                prompt = (
                    "You are a strict assistant that converts resume and job posting data into a JSON autofill payload. "
                    "Respond ONLY with a single JSON object with these keys:\n"
                    "full_name, email, phone, target_role, target_company, location_preference, skills, "
                    "experience_highlights, resume_version_id, resume_excerpt, job_url, job_source, review_required, instructions\n\n"
                    "Use the provided resume parsed summary and resume excerpt to populate fields. If a value is not present, use an empty string (for scalars) or empty list (for arrays). Do NOT hallucinate facts.\n\n"
                    f"Parsed summary JSON:\n{parsed_summary}\n\n"
                    f"Resume excerpt:\n{resume_version.content_text[:1800]}\n\n"
                    f"Job posting:\ntitle: {job.title}\ncompany: {job.company}\nlocation: {job.location}\nurl: {job.url}\nsource: {job.source}\n\n"
                    "Return compact JSON only."
                )

                completion = client.chat.completions.create(
                    model=settings.groq_model,
                    temperature=0.0,
                    max_tokens=700,
                    messages=[
                        {"role": "system", "content": "You are a JSON generator. Respond only with JSON."},
                        {"role": "user", "content": prompt},
                    ],
                )

                content = completion.choices[0].message.content
                if content:
                    # Attempt to parse the JSON response safely
                    import json

                    try:
                        parsed = json.loads(content)
                        # Ensure base keys exist
                        parsed.setdefault("resume_version_id", resume_version.id)
                        parsed.setdefault("resume_excerpt", resume_version.content_text[:1800])
                        parsed.setdefault("job_url", job.url)
                        parsed.setdefault("job_source", job.source)
                        parsed.setdefault("review_required", True)
                        return parsed
                    except Exception:
                        # Fall through to deterministic fallback on parse error
                        pass
            except Exception:
                # If LLM generation fails, gracefully fall back to deterministic payload.
                pass

        # Deterministic fallback (safe, review-required payload)
        return {
            "full_name": parsed_summary.get("candidate_name") or "",
            "email": (parsed_summary.get("contact") or {}).get("email", ""),
            "phone": (parsed_summary.get("contact") or {}).get("phone", ""),
            "target_role": job.title,
            "target_company": job.company,
            "location_preference": (parsed_summary.get("contact") or {}).get("location") or job.location or "",
            "skills": skills,
            "experience_highlights": experience_lines[:5],
            "resume_version_id": resume_version.id,
            "resume_excerpt": resume_version.content_text[:1800],
            "job_url": job.url,
            "job_source": job.source,
            "review_required": True,
            "instructions": "Validate all fields before submitting to employer portal.",
        }
