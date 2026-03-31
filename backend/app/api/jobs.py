"""Jobs scraping, matching, preferences, and email digest APIs."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.api.schemas.jobs import (
    DigestRequest,
    DigestResponse,
    JobItem,
    PreferencesRequest,
    PreferencesResponse,
    ScrapeJobsRequest,
    ScrapeJobsResponse,
)
from app.database import get_db
from app.models import JobPosting, Resume, ResumeVersion, User, UserPreference
from app.services.automation_service import AutomationService
from app.services.email_service import EmailService
from app.services.job_scraper_service import JobScraperService, SOURCES
from app.services.matcher_service import ResumeMatcherService
from app.services.scheduler_service import sync_user_schedule
from app.utils.auth import get_current_user_optional
from app.utils.config import settings

router = APIRouter()

scraper = JobScraperService()
emailer = EmailService()
automation = AutomationService()
matcher = ResumeMatcherService(embedding_model_name=settings.embedding_model_name)


def _effective_sources(sources: list[str]) -> list[str]:
    if sources:
        return [s for s in sources if s in SOURCES]
    return list(SOURCES.keys())


def _parse_csv(csv_value: str | None) -> list[str]:
    return [x.strip() for x in (csv_value or "").split(",") if x.strip()]


def _owner_filter(query, model_user_id_col, current_user: User | None):
    if settings.auth_enabled and current_user:
        return query.filter(model_user_id_col == current_user.id)
    return query


def _resolve_resume_with_owner_check(db: Session, resume_id: str | None, current_user: User | None) -> tuple[Resume | None, ResumeVersion | None]:
    if not resume_id:
        return None, None

    resume = db.query(Resume).filter(Resume.id == resume_id).first()
    if not resume:
        return None, None

    if settings.auth_enabled and current_user and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )
    return resume, version


def _to_job_item(row: JobPosting) -> JobItem:
    return JobItem(
        id=row.id,
        source=row.source,
        company=row.company,
        title=row.title,
        location=row.location,
        url=row.url,
        score=row.score,
    )


def _to_preferences_response(pref: UserPreference) -> PreferencesResponse:
    return PreferencesResponse(
        preferred_email=pref.preferred_email,
        target_role=pref.target_role,
        locations=_parse_csv(pref.locations_csv),
        keywords=_parse_csv(pref.keywords_csv),
        selected_sources=_parse_csv(pref.selected_sources_csv),
        auto_schedule_enabled=pref.auto_schedule_enabled,
        schedule_time=pref.schedule_time,
        schedule_timezone=pref.schedule_timezone,
        auto_scrape_on_login=pref.auto_scrape_on_login,
        auto_email_after_scrape=pref.auto_email_after_scrape,
    )


@router.post("/scrape", response_model=ScrapeJobsResponse)
def scrape_jobs(
    request: ScrapeJobsRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    source_keys = _effective_sources(request.sources)
    jobs = scraper.scrape_sources(source_keys=source_keys, keywords=request.keywords)

    pref_query = db.query(UserPreference)
    pref_query = _owner_filter(pref_query, UserPreference.user_id, current_user)
    pref = pref_query.first()

    resume, resume_version = _resolve_resume_with_owner_check(db, request.resume_id, current_user)
    resume_embedding = None
    if resume_version:
        if not resume_version.embedding:
            resume_version.embedding = matcher.embed_text(resume_version.content_text)
        resume_embedding = resume_version.embedding

    persisted: list[JobPosting] = []
    for item in jobs:
        existing = db.query(JobPosting).filter(JobPosting.url == item.url).first()
        embedding = matcher.embed_text(f"{item.title}\n{item.description or ''}")
        if existing:
            existing.title = item.title
            existing.company = item.company
            existing.location = item.location
            existing.source = item.source
            existing.description = item.description
            existing.embedding = embedding
            existing.scraped_at = datetime.utcnow()
            persisted.append(existing)
            continue

        row = JobPosting(
            source=item.source,
            company=item.company,
            title=item.title,
            location=item.location,
            url=item.url,
            description=item.description,
            embedding=embedding,
            scraped_at=item.scraped_at,
        )
        db.add(row)
        persisted.append(row)

    ranked = automation._rank_jobs(persisted, resume_embedding, request.keywords) if persisted else []
    sent_to = None
    if request.send_email and pref and pref.preferred_email:
        if not emailer.is_configured():
            raise HTTPException(status_code=400, detail="SMTP not configured")
        html = automation._render_digest_html(ranked)
        emailer.send_html_email(
            to_email=pref.preferred_email,
            subject="Top matched jobs for your resume",
            html_body=html,
        )
        sent_to = pref.preferred_email

    db.commit()

    latest = (
        db.query(JobPosting)
        .order_by(JobPosting.scraped_at.desc())
        .limit(max(len(persisted), 1))
        .all()
    )

    return ScrapeJobsResponse(
        scraped_count=len(persisted),
        jobs=[_to_job_item(j) for j in latest],
        top_matches=[_to_job_item(j) for j in ranked[:10]],
        mail_sent_to=sent_to,
    )


@router.post("/preferences", response_model=PreferencesResponse)
def upsert_preferences(
    request: PreferencesRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if settings.auth_enabled and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    query = db.query(UserPreference)
    query = _owner_filter(query, UserPreference.user_id, current_user)
    pref = query.first()

    if not pref:
        pref = UserPreference(
            user_id=current_user.id if current_user else None,
            preferred_email=request.preferred_email,
            target_role=request.target_role,
            locations_csv=",".join(request.locations),
            keywords_csv=",".join(request.keywords),
            selected_sources_csv=",".join(_effective_sources(request.selected_sources)),
            auto_schedule_enabled=request.auto_schedule_enabled,
            schedule_time=request.schedule_time,
            schedule_timezone=request.schedule_timezone,
            auto_scrape_on_login=request.auto_scrape_on_login,
            auto_email_after_scrape=request.auto_email_after_scrape,
        )
        db.add(pref)
    else:
        pref.preferred_email = request.preferred_email
        pref.target_role = request.target_role
        pref.locations_csv = ",".join(request.locations)
        pref.keywords_csv = ",".join(request.keywords)
        pref.selected_sources_csv = ",".join(_effective_sources(request.selected_sources))
        pref.auto_schedule_enabled = request.auto_schedule_enabled
        pref.schedule_time = request.schedule_time
        pref.schedule_timezone = request.schedule_timezone
        pref.auto_scrape_on_login = request.auto_scrape_on_login
        pref.auto_email_after_scrape = request.auto_email_after_scrape
        pref.updated_at = datetime.utcnow()

    db.commit()

    if current_user:
        sync_user_schedule(
            user_id=current_user.id,
            enabled=pref.auto_schedule_enabled,
            schedule_time=pref.schedule_time,
            timezone_name=pref.schedule_timezone,
        )

    return _to_preferences_response(pref)


@router.get("/preferences", response_model=PreferencesResponse)
def get_preferences(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if settings.auth_enabled and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    query = db.query(UserPreference)
    query = _owner_filter(query, UserPreference.user_id, current_user)
    pref = query.first()
    if not pref:
        raise HTTPException(status_code=404, detail="Preferences not set")

    return _to_preferences_response(pref)


@router.post("/digest", response_model=DigestResponse)
def send_matched_jobs_digest(
    request: DigestRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and current_user and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    latest_version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )
    if not latest_version:
        raise HTTPException(status_code=404, detail="Resume version missing")

    pref_query = db.query(UserPreference)
    pref_query = _owner_filter(pref_query, UserPreference.user_id, current_user)
    pref = pref_query.first()

    keywords = []
    if pref and pref.keywords_csv:
        keywords = [k.strip() for k in pref.keywords_csv.split(",") if k.strip()]

    if not latest_version.embedding:
        latest_version.embedding = matcher.embed_text(latest_version.content_text)

    source_keys = _effective_sources(request.sources)
    scraped = scraper.scrape_sources(source_keys=source_keys, keywords=keywords)

    saved_jobs: list[JobPosting] = []
    for item in scraped:
        row = db.query(JobPosting).filter(JobPosting.url == item.url).first()
        embedding = matcher.embed_text(f"{item.title}\n{item.description or ''}")
        if not row:
            row = JobPosting(
                source=item.source,
                company=item.company,
                title=item.title,
                location=item.location,
                url=item.url,
                description=item.description,
                embedding=embedding,
                scraped_at=item.scraped_at,
            )
            db.add(row)
            db.flush()
        else:
            row.embedding = embedding
            row.description = item.description
            row.scraped_at = datetime.utcnow()
        saved_jobs.append(row)

    ranked = automation._rank_jobs(saved_jobs, latest_version.embedding, keywords=keywords)
    recipient = request.preferred_email or (pref.preferred_email if pref else None)
    if not recipient:
        raise HTTPException(status_code=400, detail="Provide preferred_email or save preferences first")

    html = automation._render_digest_html(ranked)
    if not emailer.is_configured():
        raise HTTPException(status_code=400, detail="SMTP not configured")

    emailer.send_html_email(
        to_email=recipient,
        subject="Your matched jobs digest (India portals)",
        html_body=html,
    )

    db.commit()

    return DigestResponse(
        sent_to=recipient,
        jobs_count=len(ranked),
        top_titles=[j.title for j in ranked[:10]],
    )
