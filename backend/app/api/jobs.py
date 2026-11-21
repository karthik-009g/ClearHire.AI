"""Jobs scraping, matching, preferences, and email digest APIs."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session

from app.api.schemas.jobs import (
    DigestRequest,
    DigestResponse,
    JobItem,
    PreferencesRequest,
    PreferencesResponse,
    ScrapeJobsRequest,
    ScrapeJobsResponse,
    VerifyJobUrlRequest,
    VerifyJobUrlResponse,
)
from app.database import get_db
from app.models import JobPosting, Resume, ResumeVersion, User, UserPreference
from app.services.authenticity_service import AuthenticityService
from app.services.automation_service import AutomationService
from app.services.direct_ats_service import DirectAtsService
from app.services.email_service import EmailService
from app.services.job_scraper_service import JobScraperService, SOURCES
from app.services.liveness_service import (
    filter_live_jobs_concurrently,
    get_company_fallback_career_url,
    verify_job_url,
)
from app.services.location_service import india_or_remote_only, matches_locations
from app.services.matcher_service import ResumeMatcherService
from app.services.scheduler_service import sync_user_schedule
from app.utils.auth import get_current_user_optional
from app.utils.config import settings

router = APIRouter()

scraper = JobScraperService()
emailer = EmailService()
automation = AutomationService()
authenticity = AuthenticityService()
direct_ats = DirectAtsService()
matcher = ResumeMatcherService(
    embedding_model_name=settings.embedding_model_name,
    embedding_dimensions=settings.embedding_dimensions,
    load_embedding_model=settings.embedding_load_local_model,
)


def _embedding_invalid(vector: list[float] | None) -> bool:
    return vector is None or len(vector) != settings.embedding_dimensions


def _effective_sources(sources: list[str]) -> list[str]:
    # An omitted selection must not fan out across every configured web source.
    # Direct ATS retrieval is handled separately by DirectAtsService.
    selected = list(dict.fromkeys(s for s in sources if s == "direct_ats" or s in SOURCES))
    return selected or ["direct_ats"]


def _is_detected_staffing_agency(job: JobPosting) -> bool:
    signals = getattr(job, "ghosting_signals", None)
    return isinstance(signals, dict) and signals.get("is_staffing_agency") is True


def _effective_posted_within_hours(requested: int | None, pref: UserPreference | None = None) -> int | None:
    if requested is not None:
        return requested
    if pref and pref.max_post_age_days > 0:
        return pref.max_post_age_days * 24
    return settings.default_scrape_posted_within_hours if settings.default_scrape_posted_within_hours > 0 else None


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
        description=row.description,
        scraped_at=(row.scraped_at.replace(tzinfo=timezone.utc) if row.scraped_at and row.scraped_at.tzinfo is None else row.scraped_at),
        posted_at=(row.posted_at.replace(tzinfo=timezone.utc) if row.posted_at and row.posted_at.tzinfo is None else row.posted_at),
        score=getattr(row, "ranking_score", None),
        score_components=getattr(row, "score_components", None),
        score_weights=getattr(row, "score_weights", None),
        score_availability=getattr(row, "score_availability", None),
        score_formula=getattr(row, "score_formula", None),
        source_type=getattr(row, "source_type", "job_board") or "job_board",
        ghosting_risk=getattr(row, "ghosting_risk", "medium") or "medium",
        authenticity_score=getattr(row, "authenticity_score", 50.0) if getattr(row, "authenticity_score", None) is not None else 50.0,
        is_direct_employer=getattr(row, "is_direct_employer", False) if getattr(row, "is_direct_employer", None) is not None else False,
        is_evergreen=getattr(row, "is_evergreen", False) or False,
        applicant_count_estimate=getattr(row, "applicant_count_estimate", None),
        ats_provider=getattr(row, "ats_provider", None),
        ghosting_signals=getattr(row, "ghosting_signals", None),
        is_expired=getattr(row, "is_expired", False) or False,
        fallback_career_url=get_company_fallback_career_url(row.company, row.url),
        liveness_verified=True,
    )


def _to_preferences_response(pref: UserPreference) -> PreferencesResponse:
    return PreferencesResponse(
        preferred_email=pref.preferred_email,
        target_role=pref.target_role,
        locations=_parse_csv(pref.locations_csv),
        keywords=_parse_csv(pref.keywords_csv),
        selected_sources=_effective_sources(_parse_csv(pref.selected_sources_csv)),
        target_companies=_parse_csv(getattr(pref, "target_companies_csv", None)),
        exclude_staffing_agencies=getattr(pref, "exclude_staffing_agencies", True) if getattr(pref, "exclude_staffing_agencies", None) is not None else True,
        max_ghosting_risk=getattr(pref, "max_ghosting_risk", "medium_and_low") or "medium_and_low",
        direct_portals_only=getattr(pref, "direct_portals_only", False) or False,
        max_post_age_days=getattr(pref, "max_post_age_days", 3) or 3,
        notice_period_days=getattr(pref, "notice_period_days", None),
        serving_notice=getattr(pref, "serving_notice", False) or False,
        current_ctc_lpa=getattr(pref, "current_ctc_lpa", None),
        expected_ctc_lpa=getattr(pref, "expected_ctc_lpa", None),
        work_mode=getattr(pref, "work_mode", None),
        auto_schedule_enabled=pref.auto_schedule_enabled,
        schedule_time=pref.schedule_time,
        schedule_timezone=pref.schedule_timezone,
        auto_scrape_on_login=pref.auto_scrape_on_login,
        auto_email_after_scrape=pref.auto_email_after_scrape,
    )


def _default_preferences_response(current_user: User | None) -> PreferencesResponse:
    preferred_email = ""
    if current_user and getattr(current_user, "email", None):
        preferred_email = current_user.email

    default_sources = ["direct_ats"]

    return PreferencesResponse(
        preferred_email=preferred_email,
        target_role="Software Engineer",
        locations=[],
        keywords=[],
        selected_sources=default_sources,
        target_companies=[],
        exclude_staffing_agencies=True,
        max_ghosting_risk="medium_and_low",
        direct_portals_only=False,
        max_post_age_days=3,
        notice_period_days=None,
        serving_notice=False,
        current_ctc_lpa=None,
        expected_ctc_lpa=None,
        work_mode=None,
        auto_schedule_enabled=False,
        schedule_time="09:00",
        schedule_timezone=settings.default_schedule_timezone,
        auto_scrape_on_login=False,
        auto_email_after_scrape=False,
    )



@router.post("/scrape", response_model=ScrapeJobsResponse)
def scrape_jobs(
    request: ScrapeJobsRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if settings.auth_enabled and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    pref_query = db.query(UserPreference)
    pref_query = _owner_filter(pref_query, UserPreference.user_id, current_user)
    pref = pref_query.first()

    source_keys = _effective_sources(request.sources)
    posted_within_hours = _effective_posted_within_hours(request.posted_within_hours, pref)
    requested_locations = request.locations if request.locations is not None else (_parse_csv(pref.locations_csv) if pref else [])
    requested_companies = request.target_companies if request.target_companies is not None else (_parse_csv(pref.target_companies_csv) if pref else [])
    jobs = scraper.scrape_sources(
        source_keys=source_keys,
        keywords=request.keywords,
        max_post_age_hours=posted_within_hours,
    )

    # If direct_portals_only is requested or in user preferences, fetch from DirectAtsService
    if request.direct_portals_only or (pref and pref.direct_portals_only) or "direct_ats" in source_keys:
        direct_jobs = direct_ats.fetch_all_direct_jobs(
            target_companies=requested_companies,
            keywords=request.keywords,
            india_or_remote_only=india_or_remote_only(requested_locations),
            max_jobs=40,
        )
        if posted_within_hours is not None:
            cutoff = datetime.now(timezone.utc) - timedelta(hours=posted_within_hours)
            recent_or_undated = []
            for item in direct_jobs:
                posted_at = getattr(item, "posted_at", None)
                if posted_at is None:
                    recent_or_undated.append(item)
                    continue
                if posted_at.tzinfo is None:
                    posted_at = posted_at.replace(tzinfo=timezone.utc)
                if posted_at >= cutoff:
                    recent_or_undated.append(item)
            direct_jobs = recent_or_undated
        jobs = direct_jobs + jobs

    unique_jobs = {}
    for item in jobs:
        if item.url:
            unique_jobs.setdefault(item.url, item)
    jobs = list(unique_jobs.values())

    # Filter out dead links, 404s, and expired requisitions
    jobs = filter_live_jobs_concurrently(jobs)

    resume, resume_version = _resolve_resume_with_owner_check(db, request.resume_id, current_user)
    resume_embedding = None
    if resume_version:
        if _embedding_invalid(resume_version.embedding):
            resume_context = matcher.build_resume_context(
                resume_version.content_text,
                parsed_summary=resume.parsed_summary if resume else None,
            )
            resume_version.embedding = matcher.embed_text(resume_context)
        if _embedding_invalid(resume_version.embedding_vector):
            resume_version.embedding_vector = resume_version.embedding
        resume_embedding = resume_version.embedding

    persisted: list[JobPosting] = []
    if jobs:
        urls = [item.url for item in jobs if item.url]
        existing_jobs_map = {
            jp.url: jp
            for jp in db.query(JobPosting).filter(JobPosting.url.in_(urls)).all()
        } if urls else {}

        texts = [f"{item.title}\n{item.description or ''}" for item in jobs]
        embeddings = matcher.embed_texts_batch(texts)

        for item, embedding in zip(jobs, embeddings):
            analysis = authenticity.analyze(
                title=item.title,
                company=item.company,
                url=item.url,
                description=item.description,
                source=item.source,
                posted_at=getattr(item, "posted_at", None),
            )

            existing = existing_jobs_map.get(item.url)
            if existing:
                existing.title = item.title
                existing.company = item.company
                existing.location = item.location
                existing.source = item.source
                existing.description = item.description
                if getattr(item, "posted_at", None) is not None:
                    existing.posted_at = item.posted_at
                existing.embedding = embedding
                existing.embedding_vector = embedding
                existing.scraped_at = datetime.utcnow()
                existing.source_type = analysis.source_type
                existing.ghosting_risk = analysis.ghosting_risk
                existing.authenticity_score = analysis.authenticity_score
                existing.is_direct_employer = analysis.is_direct_employer
                existing.is_evergreen = analysis.is_evergreen
                existing.ats_provider = analysis.ats_provider
                existing.ghosting_signals = analysis.ghosting_signals
                persisted.append(existing)
            else:
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
                persisted.append(row)

    def _passes_candidate_filter(j: JobPosting) -> bool:
        if (request.direct_portals_only or (pref and pref.direct_portals_only)) and j.source_type not in ("direct_ats", "company_career_page", "curated_startup"):
            return False
        exclude_agencies = request.exclude_staffing_agencies if request.exclude_staffing_agencies is not None else (pref.exclude_staffing_agencies if pref else True)
        if exclude_agencies and _is_detected_staffing_agency(j):
            return False
        risk_filter = request.max_ghosting_risk or (pref.max_ghosting_risk if pref else "medium_and_low")
        if risk_filter == "low_only" and j.ghosting_risk != "low":
            return False
        if risk_filter == "medium_and_low" and j.ghosting_risk not in ("low", "medium"):
            return False
        if not matches_locations(j.location, requested_locations):
            return False
        return True

    # Preserve candidate filters. An empty match is better than silently returning jobs they excluded.
    eligible_jobs = [j for j in persisted if _passes_candidate_filter(j)]

    ranked = automation._rank_jobs(eligible_jobs, resume_embedding, request.keywords) if eligible_jobs else []
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

    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        # Concurrency race-condition recovery: another concurrent thread/process inserted
        # a job with the same unique URL. Re-query existing committed records and return smoothly.
        urls = [item.url for item in jobs if item.url]
        if urls:
            persisted = db.query(JobPosting).filter(JobPosting.url.in_(urls)).all()
            eligible_jobs = [j for j in persisted if _passes_candidate_filter(j)]
            ranked = automation._rank_jobs(eligible_jobs, resume_embedding, request.keywords) if eligible_jobs else []

    latest = sorted(eligible_jobs, key=lambda row: row.scraped_at or datetime.min, reverse=True)

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
            target_companies_csv=",".join(request.target_companies),
            exclude_staffing_agencies=request.exclude_staffing_agencies,
            max_ghosting_risk=request.max_ghosting_risk,
            direct_portals_only=request.direct_portals_only,
            max_post_age_days=request.max_post_age_days,
            notice_period_days=request.notice_period_days,
            serving_notice=request.serving_notice,
            current_ctc_lpa=request.current_ctc_lpa,
            expected_ctc_lpa=request.expected_ctc_lpa,
            work_mode=request.work_mode,
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
        pref.target_companies_csv = ",".join(request.target_companies)
        pref.exclude_staffing_agencies = request.exclude_staffing_agencies
        pref.max_ghosting_risk = request.max_ghosting_risk
        pref.direct_portals_only = request.direct_portals_only
        pref.max_post_age_days = request.max_post_age_days
        pref.notice_period_days = request.notice_period_days
        pref.serving_notice = request.serving_notice
        pref.current_ctc_lpa = request.current_ctc_lpa
        pref.expected_ctc_lpa = request.expected_ctc_lpa
        pref.work_mode = request.work_mode
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
        return _default_preferences_response(current_user)

    return _to_preferences_response(pref)


@router.post("/digest", response_model=DigestResponse)
def send_matched_jobs_digest(
    request: DigestRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if settings.auth_enabled and not current_user:
        raise HTTPException(status_code=401, detail="Authentication required")

    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and resume.user_id != current_user.id:
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

    if _embedding_invalid(latest_version.embedding):
        resume_context = matcher.build_resume_context(
            latest_version.content_text,
            parsed_summary=resume.parsed_summary,
        )
        latest_version.embedding = matcher.embed_text(resume_context)
    if _embedding_invalid(latest_version.embedding_vector):
        latest_version.embedding_vector = latest_version.embedding

    selected_source_names = _parse_csv(pref.selected_sources_csv if pref else None)
    source_keys = _effective_sources(selected_source_names)
    posted_within_hours = _effective_posted_within_hours(None, pref)
    requested_locations = _parse_csv(pref.locations_csv if pref else None)
    scraped = scraper.scrape_sources(
        source_keys=source_keys,
        keywords=keywords,
        max_post_age_hours=posted_within_hours,
    )
    if pref and (pref.direct_portals_only or "direct_ats" in selected_source_names):
        direct_jobs = direct_ats.fetch_all_direct_jobs(
            target_companies=_parse_csv(pref.target_companies_csv),
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
        scraped = direct_jobs + scraped

    saved_jobs = automation._upsert_jobs(db, scraped)
    eligible_jobs = [job for job in saved_jobs if matches_locations(job.location, requested_locations)]
    if pref and pref.direct_portals_only:
        eligible_jobs = [job for job in eligible_jobs if job.source_type in ("direct_ats", "company_career_page", "curated_startup")]
    if pref and pref.exclude_staffing_agencies:
        eligible_jobs = [job for job in eligible_jobs if not _is_detected_staffing_agency(job)]
    if pref and pref.max_ghosting_risk == "low_only":
        eligible_jobs = [job for job in eligible_jobs if job.ghosting_risk == "low"]
    elif pref and pref.max_ghosting_risk == "medium_and_low":
        eligible_jobs = [job for job in eligible_jobs if job.ghosting_risk in ("low", "medium")]
    ranked = automation._rank_jobs(eligible_jobs, latest_version.embedding, keywords=keywords)
    recipient = (request.target_email if getattr(request, "target_email", None) else None) or (pref.preferred_email if pref else None)
    if not recipient:
        raise HTTPException(status_code=400, detail="Provide target_email or save preferences first")

    html = automation._render_digest_html(ranked)
    if not emailer.is_configured():
        raise HTTPException(status_code=400, detail="SMTP not configured")

    emailer.send_html_email(
        to_email=recipient,
        subject="Your matched jobs digest",
        html_body=html,
    )

    try:
        db.commit()
    except IntegrityError:
        db.rollback()

    return DigestResponse(
        recipient=recipient,
        sent=True,
        job_count=len(ranked),
        top_matches=[_to_job_item(j) for j in ranked[:10]],
        sent_to=recipient,
        jobs_count=len(ranked),
        top_titles=[j.title for j in ranked[:10]],
    )


@router.post("/verify-url", response_model=VerifyJobUrlResponse)
def verify_job_url_endpoint(request: VerifyJobUrlRequest):
    """Real-time liveness verification for a job requisition link."""
    result = verify_job_url(request.url)
    fallback = get_company_fallback_career_url(request.company, request.url)
    return VerifyJobUrlResponse(
        url=request.url,
        is_live=result.get("is_live", True),
        is_expired=result.get("is_expired", False),
        status_code=result.get("status_code", 200),
        reason=result.get("reason", "ok"),
        final_url=result.get("final_url", request.url),
        fallback_career_url=fallback,
    )

