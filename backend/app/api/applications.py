"""Minimal application tracking APIs for V1."""

from __future__ import annotations

from datetime import datetime
from urllib.parse import quote_plus

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
import requests
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, JobDescription, Resume, ResumeVersion, User, UserPreference
from app.models import ApplicationSubmissionLog
from app.utils.auth import get_current_user_optional
from app.utils.config import settings
from app.models import JobPosting
from app.services.automation_service import AutomationService
from app.services.ats_integration_service import ATSIntegrationService
from app.services.browser_autofill_service import BrowserAutofillService
from app.services.direct_ats_service import DirectAtsService
from app.services.interview_prep_service import InterviewPrepService
from app.services.n8n_workflow_service import N8NWorkflowService
from app.services.recruiter_outreach_service import RecruiterOutreachService
from app.services.screener_answer_service import ScreenerAnswerService
from app.services.liveness_service import get_company_fallback_career_url
from app.utils.rate_limit import check_rate_limit

automation = AutomationService()
screener_service = ScreenerAnswerService()
outreach_service = RecruiterOutreachService()
direct_ats_service = DirectAtsService()
interview_prep_service = InterviewPrepService()

router = APIRouter()
CREATABLE_APPLICATION_STATUSES = {"draft", "pending", "review_required", "bookmarked"}
EDITABLE_APPLICATION_STATUSES = {
    "draft", "pending", "review_required", "bookmarked",
    "screening", "interviewing", "offer", "rejected", "ghosted",
}
ALLOWED_STATUS_TRANSITIONS = {
    "bookmarked": {"draft", "pending", "review_required", "applied"},
    "draft": {"pending", "review_required", "bookmarked"},
    "pending": {"draft", "review_required", "bookmarked"},
    "review_required": {"pending", "draft"},
    "reviewed": {"applied", "pending"},
    "applied": {"screening", "interviewing", "offer", "rejected", "ghosted"},
    "screening": {"interviewing", "offer", "rejected", "ghosted", "applied"},
    "interviewing": {"offer", "rejected", "ghosted", "screening"},
    "offer": {"interviewing", "rejected"},
    "rejected": {"applied", "screening"},
    "ghosted": {"screening", "interviewing", "applied", "rejected"},
}
browser_autofill = BrowserAutofillService()
ats_integration = ATSIntegrationService()
n8n_workflows = N8NWorkflowService()


def _require_current_user(current_user: User | None) -> None:
    if settings.auth_enabled and current_user is None:
        raise HTTPException(status_code=401, detail="Authentication required")


def _ensure_owner(user_id: str | None, current_user: User | None) -> None:
    _require_current_user(current_user)
    if settings.auth_enabled and current_user is not None and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this application")


def _ensure_resume_owner(user_id: str | None, current_user: User | None) -> None:
    _require_current_user(current_user)
    if settings.auth_enabled and current_user is not None and user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")


def _serialize_application(
    application: Application,
    job: JobDescription | None = None,
    version: ResumeVersion | None = None,
) -> dict:
    updated_at = application.updated_at or datetime.utcnow()
    days_since_update = (datetime.utcnow() - updated_at).days
    is_ghosted = application.status == "ghosted" or (
        application.status in {"applied", "screening"} and days_since_update >= 14
    )
    return {
        "id": application.id,
        "job_description_id": application.job_description_id,
        "job_title": job.title if job else None,
        "job_company": job.company if job else None,
        "resume_version_id": application.resume_version_id,
        "resume_version_no": version.version_no if version else None,
        "status": application.status,
        "application_url": application.application_url,
        "autofill_payload": application.autofill_payload,
        "notes": application.notes,
        "updated_at": application.updated_at,
        "days_since_update": days_since_update,
        "is_ghosted": is_ghosted,
    }


class CreateApplicationRequest(BaseModel):
    job_description_id: int
    resume_version_id: int
    status: str = "pending"
    application_url: str | None = None
    autofill_payload: dict | None = None
    notes: str | None = None


class UpdateStatusRequest(BaseModel):
    status: str
    notes: str | None = None


class PrepareAutofillRequest(BaseModel):
    resume_id: str
    job_posting_id: int
    notes: str | None = None
    persist: bool = False
    force: bool = False


class SubmitApplicationRequest(BaseModel):
    application_url: str | None = None
    confirm_reviewed: bool = False
    external_confirmation: bool = False


class ReviewApplicationRequest(BaseModel):
    autofill_payload: dict | None = None
    notes: str | None = None
    confirm_fields_reviewed: bool = False


class N8NEventRequest(BaseModel):
    event_type: str


class AnswerScreenerRequest(BaseModel):
    question: str
    company: str | None = None
    role: str | None = None
    resume_id: str | None = None
    max_words: int = 150


class AnswerScreenerResponse(BaseModel):
    answer: str
    detected_intent: str
    confidence_score: float
    grounded_facts: list[str]


class OutreachRequest(BaseModel):
    company: str | None = None
    role: str | None = None
    job_url: str | None = None
    candidate_name: str | None = None
    resume_id: str | None = None


class OutreachResponse(BaseModel):
    application_id: int | None = None
    target_company: str
    target_role: str
    hiring_manager_inmail: str
    linkedin_connection_note: str
    follow_up_email: str
    grounded_highlights: list[str]
    linkedin_recruiter_search_url: str


@router.post("/answer-screener", response_model=AnswerScreenerResponse)
def answer_screener_question(
    request: AnswerScreenerRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    resume_text = None
    parsed_summary = None

    if request.resume_id:
        resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        if settings.auth_enabled:
            if current_user is None:
                raise HTTPException(status_code=401, detail="Authentication required to use this resume")
            if resume.user_id != current_user.id:
                raise HTTPException(status_code=403, detail="Not allowed for this resume")
        parsed_summary = resume.parsed_summary
        latest_version = (
            db.query(ResumeVersion)
            .filter(ResumeVersion.resume_id == resume.id)
            .order_by(ResumeVersion.version_no.desc())
            .first()
        )
        if latest_version:
            resume_text = latest_version.content_text
    elif current_user:
        resume = (
            db.query(Resume)
            .filter(Resume.user_id == current_user.id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        if resume:
            parsed_summary = resume.parsed_summary
            latest_version = (
                db.query(ResumeVersion)
                .filter(ResumeVersion.resume_id == resume.id)
                .order_by(ResumeVersion.version_no.desc())
                .first()
            )
            if latest_version:
                resume_text = latest_version.content_text

    pref = None
    if current_user is not None:
        pref = db.query(UserPreference).filter(UserPreference.user_id == current_user.id).first()
    elif not settings.auth_enabled:
        pref = db.query(UserPreference).first()

    result = screener_service.answer_question(
        question=request.question,
        company=request.company,
        role=request.role,
        resume_text=resume_text,
        parsed_summary=parsed_summary,
        preferences=pref,
        max_words=request.max_words,
    )

    return AnswerScreenerResponse(
        answer=result.answer,
        detected_intent=result.detected_intent,
        confidence_score=result.confidence_score,
        grounded_facts=result.grounded_facts,
    )


@router.post("/")
def create_application(
    request: CreateApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_current_user(current_user)
    if request.status not in CREATABLE_APPLICATION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_initial_status",
                "allowed_statuses": sorted(CREATABLE_APPLICATION_STATUSES),
            },
        )

    version = db.query(ResumeVersion).filter(ResumeVersion.id == request.resume_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found")

    job = db.query(JobDescription).filter(JobDescription.id == request.job_description_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found")

    if settings.auth_enabled:
        resume = db.query(Resume).filter(Resume.id == version.resume_id).first()
        if not resume or resume.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed for this resume version")

    # Rate limit per-user (or global anonymous key)
    user_key = f"user:{current_user.id}" if current_user else "anon"
    check_rate_limit(user_key, limit=getattr(settings, "rate_limit_applications_per_hour", 10), window_seconds=3600)

    application = Application(
        user_id=current_user.id if current_user else None,
        job_description_id=request.job_description_id,
        resume_version_id=request.resume_version_id,
        status=request.status,
        application_url=request.application_url,
        autofill_payload=request.autofill_payload,
        notes=request.notes,
        updated_at=datetime.utcnow(),
    )
    db.add(application)
    db.commit()
    db.refresh(application)

    return _serialize_application(application, job=job, version=version)


@router.post("/autofill")
def prepare_application_autofill(
    request: PrepareAutofillRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_current_user(current_user)
    resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
    if not resume:
        raise HTTPException(status_code=404, detail="Resume not found")
    if settings.auth_enabled and resume.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this resume")

    version = (
        db.query(ResumeVersion)
        .filter(ResumeVersion.resume_id == resume.id)
        .order_by(ResumeVersion.version_no.desc())
        .first()
    )
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found")

    job = db.query(JobPosting).filter(JobPosting.id == request.job_posting_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job posting not found")

    payload = automation.build_application_autofill(resume.parsed_summary, version, job)
    readiness = None
    if isinstance(resume.parsed_summary, dict):
        readiness = resume.parsed_summary.get("autofill_readiness")
    incomplete = bool(readiness and not readiness.get("ready"))

    pref_query = db.query(UserPreference)
    if current_user is not None:
        pref_query = pref_query.filter(UserPreference.user_id == current_user.id)
    elif not settings.auth_enabled:
        pref_query = pref_query.filter(UserPreference.user_id.is_(None))
    pref = pref_query.order_by(UserPreference.updated_at.desc()).first()
    candidate_preferences = {
        "notice_period_days": pref.notice_period_days if pref else None,
        "serving_notice": pref.serving_notice if pref and pref.notice_period_days is not None else None,
        "current_ctc_lpa": pref.current_ctc_lpa if pref else None,
        "expected_ctc_lpa": pref.expected_ctc_lpa if pref else None,
        "work_mode": pref.work_mode if pref else None,
        "target_role": pref.target_role if pref else None,
        "locations": [value.strip() for value in (pref.locations_csv or "").split(",") if value.strip()] if pref else [],
        "timezone": pref.schedule_timezone if pref else None,
    }

    if request.persist:
        if incomplete and not request.force:
            missing = readiness.get("missing_required_fields", []) if isinstance(readiness, dict) else []
            raise HTTPException(status_code=400, detail={"error": "autofill_not_ready", "missing_required_fields": missing})

        existing_query = db.query(Application).filter(Application.application_url == job.url)
        if current_user is not None:
            existing_query = existing_query.filter(Application.user_id == current_user.id)
        else:
            existing_query = existing_query.filter(Application.user_id.is_(None))
        existing = existing_query.order_by(Application.updated_at.desc()).first()
        if existing:
            existing_job = db.query(JobDescription).filter(JobDescription.id == existing.job_description_id).first()
            existing_version = db.query(ResumeVersion).filter(ResumeVersion.id == existing.resume_version_id).first()
            existing_readiness = (existing.autofill_payload or {}).get("autofill_readiness", readiness)
            return {
                "application": _serialize_application(existing, job=existing_job, version=existing_version),
                "autofill": existing.autofill_payload or payload,
                "autofill_readiness": existing_readiness,
                "candidate_preferences": candidate_preferences,
                "already_tracked": True,
            }

        user_key = f"user:{current_user.id}" if current_user else "anon"
        check_rate_limit(user_key, limit=getattr(settings, "rate_limit_applications_per_hour", 10), window_seconds=3600)

        jd = (
            db.query(JobDescription)
            .filter(
                JobDescription.title == job.title,
                JobDescription.company == job.company,
                JobDescription.jd_text == (job.description or ""),
            )
            .first()
        )
        if not jd:
            jd = JobDescription(title=job.title, company=job.company, jd_text=job.description or "")
            db.add(jd)
            db.flush()

        application = Application(
            user_id=current_user.id if current_user else None,
            job_description_id=jd.id,
            resume_version_id=version.id,
            status="review_required" if incomplete else "pending",
            application_url=job.url,
            autofill_payload=payload,
            notes=request.notes,
            updated_at=datetime.utcnow(),
        )
        db.add(application)
        db.commit()
        db.refresh(application)
        return {
            "application": _serialize_application(application, job=jd, version=version),
            "autofill": payload,
            "autofill_readiness": readiness,
            "candidate_preferences": candidate_preferences,
            "already_tracked": False,
        }

    return {
        "autofill": payload,
        "autofill_readiness": readiness,
        "candidate_preferences": candidate_preferences,
        "notes": request.notes,
    }


@router.patch("/{application_id}/status")
def update_application_status(
    application_id: int,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)

    if request.status == "applied":
        raise HTTPException(
            status_code=400,
            detail={"error": "submission_confirmation_required"},
        )
    if request.status == "reviewed":
        raise HTTPException(
            status_code=400,
            detail={"error": "review_confirmation_required"},
        )
    if request.status not in EDITABLE_APPLICATION_STATUSES:
        raise HTTPException(
            status_code=400,
            detail={
                "error": "invalid_status",
                "allowed_statuses": sorted(EDITABLE_APPLICATION_STATUSES | {"reviewed", "applied"}),
            },
        )
    if request.status != application.status and request.status not in ALLOWED_STATUS_TRANSITIONS.get(application.status, set()):
        raise HTTPException(
            status_code=409,
            detail={
                "error": "invalid_status_transition",
                "current_status": application.status,
                "requested_status": request.status,
            },
        )

    application.status = request.status
    application.notes = request.notes
    application.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(application)

    row = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
        .filter(Application.id == application.id)
        .first()
    )
    if row:
        app_obj, job, version = row
        return _serialize_application(app_obj, job=job, version=version)
    return _serialize_application(application, job=None, version=None)


@router.post("/{application_id}/review")
def review_application(
    application_id: int,
    request: ReviewApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)
    if application.status not in {"pending", "review_required", "reviewed"}:
        raise HTTPException(
            status_code=409,
            detail={"error": "application_not_reviewable", "status": application.status},
        )
    if not request.confirm_fields_reviewed:
        raise HTTPException(status_code=400, detail={"error": "review_confirmation_required"})

    if request.autofill_payload is not None:
        application.autofill_payload = request.autofill_payload
    if request.notes is not None:
        application.notes = request.notes
    application.status = "reviewed"
    application.updated_at = datetime.utcnow()
    db.add(
        ApplicationSubmissionLog(
            application_id=application.id,
            user_id=current_user.id if current_user else None,
            action="review_confirmed",
            detail={"confirm_fields_reviewed": True},
        )
    )
    db.commit()
    db.refresh(application)

    row = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
        .filter(Application.id == application.id)
        .first()
    )
    if row:
        app_obj, job, version = row
        return _serialize_application(app_obj, job=job, version=version)
    return _serialize_application(application, job=None, version=None)


@router.get("/")
def list_applications(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_current_user(current_user)
    query = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
    )
    if settings.auth_enabled:
        query = query.filter(Application.user_id == current_user.id)

    results = query.order_by(Application.updated_at.desc()).all()
    return [_serialize_application(app, job=job, version=version) for app, job, version in results]


@router.get("/{application_id}/interview-prep")
def get_application_interview_prep(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    """Build a grounded interview pack from the exact resume version used for this application."""
    _require_current_user(current_user)
    row = (
        db.query(Application, JobDescription, ResumeVersion, Resume)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
        .outerjoin(Resume, ResumeVersion.resume_id == Resume.id)
        .filter(Application.id == application_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    application, job, version, resume = row
    _ensure_owner(application.user_id, current_user)

    if not job or not version:
        raise HTTPException(status_code=409, detail="Application is missing its saved job or resume version")
    if not resume:
        raise HTTPException(status_code=409, detail="Application resume record is no longer available")
    _ensure_resume_owner(resume.user_id, current_user)

    preference = None
    if current_user:
        preference = (
            db.query(UserPreference)
            .filter(UserPreference.user_id == current_user.id)
            .order_by(UserPreference.updated_at.desc())
            .first()
        )

    return interview_prep_service.build_pack(
        role=job.title,
        company=job.company,
        job_description=job.jd_text,
        resume_text=version.content_text,
        resume_version=version.version_no,
        preferences=preference,
    )


@router.get("/ghosting-alerts")
def get_ghosting_alerts(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_current_user(current_user)
    query = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
    )
    if settings.auth_enabled:
        query = query.filter(Application.user_id == current_user.id)

    results = query.order_by(Application.updated_at.desc()).all()
    rows = [app for app, _, _ in results]
    jobs = {job.id: job for _, job, _ in results if job is not None}
    versions = {version.id: version for _, _, version in results if version is not None}

    ghosted_apps = []
    total_applied = 0
    now = datetime.utcnow()

    for app in rows:
        if app.status in {"applied", "screening", "interviewing", "offer", "rejected", "ghosted"}:
            total_applied += 1

        up_time = app.updated_at or now
        days = (now - up_time).days
        if app.status == "ghosted" or (app.status in {"applied", "screening"} and days >= 14):
            ghosted_apps.append(
                _serialize_application(app, job=jobs.get(app.job_description_id), version=versions.get(app.resume_version_id))
            )

    ghosting_rate = round((len(ghosted_apps) / total_applied * 100), 1) if total_applied > 0 else 0.0

    alternatives = []
    try:
        direct_jobs = direct_ats_service.get_direct_jobs()
        for dj in direct_jobs:
            alternatives.append({
                "title": dj.title,
                "company": dj.company,
                "location": dj.location,
                "url": dj.url,
                "source": dj.source,
                "ats_type": getattr(dj, "ats_type", dj.source),
                "availability_note": "Direct employer requisition from live verified ATS board.",
                "salary_range": getattr(dj, "salary_range", None),
                "fallback_career_url": get_company_fallback_career_url(dj.company, dj.url),
                "is_expired": False,
            })
            if len(alternatives) >= 5:
                break
    except Exception:
        alternatives = []

    return {
        "total_applications": len(rows),
        "applied_count": total_applied,
        "ghosted_count": len(ghosted_apps),
        "ghosting_rate_percent": ghosting_rate,
        "ghosting_threshold_days": 14,
        "ghosted_applications": ghosted_apps,
        "recommended_alternatives": alternatives,
    }


@router.post("/outreach", response_model=OutreachResponse)
def generate_custom_outreach(
    request: OutreachRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_current_user(current_user)
    company = request.company or "the team"
    role = request.role or "Software Engineer"

    parsed_summary = None
    if request.resume_id:
        resume = db.query(Resume).filter(Resume.id == request.resume_id).first()
        if not resume:
            raise HTTPException(status_code=404, detail="Resume not found")
        _ensure_resume_owner(resume.user_id, current_user)
        parsed_summary = resume.parsed_summary
    elif current_user:
        resume = (
            db.query(Resume)
            .filter(Resume.user_id == current_user.id)
            .order_by(Resume.created_at.desc())
            .first()
        )
        if resume:
            parsed_summary = resume.parsed_summary

    pref_query = db.query(UserPreference)
    if settings.auth_enabled:
        pref_query = pref_query.filter(UserPreference.user_id == current_user.id)
    pref = pref_query.first()

    candidate_name = request.candidate_name or "Candidate"
    if candidate_name == "Candidate" and current_user and getattr(current_user, "email", None):
        candidate_name = current_user.email.split("@")[0].capitalize()

    pkg = outreach_service.generate_outreach(
        company=company,
        role=role,
        job_url=request.job_url,
        candidate_name=candidate_name,
        parsed_summary=parsed_summary,
        preferences=pref,
    )

    recruiter_query = f"{company} technical recruiter talent acquisition"
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(recruiter_query)}"

    return OutreachResponse(
        application_id=None,
        target_company=company,
        target_role=role,
        hiring_manager_inmail=pkg.hiring_manager_inmail,
        linkedin_connection_note=pkg.linkedin_connection_note,
        follow_up_email=pkg.follow_up_email,
        grounded_highlights=pkg.grounded_highlights,
        linkedin_recruiter_search_url=search_url,
    )


@router.post("/{application_id}/outreach", response_model=OutreachResponse)
def generate_application_outreach(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)

    job = db.query(JobDescription).filter(JobDescription.id == application.job_description_id).first()
    company = job.company if job and job.company else "the team"
    role = job.title if job and job.title else "Software Engineer"

    parsed_summary = None
    if application.resume_version_id:
        version = db.query(ResumeVersion).filter(ResumeVersion.id == application.resume_version_id).first()
        if version:
            resume = db.query(Resume).filter(Resume.id == version.resume_id).first()
            if resume:
                parsed_summary = resume.parsed_summary

    _require_current_user(current_user)
    pref_query = db.query(UserPreference)
    if settings.auth_enabled:
        pref_query = pref_query.filter(UserPreference.user_id == current_user.id)
    pref = pref_query.first()

    candidate_name = "Candidate"
    if current_user and getattr(current_user, "email", None):
        candidate_name = current_user.email.split("@")[0].capitalize()

    pkg = outreach_service.generate_outreach(
        company=company,
        role=role,
        job_url=application.application_url,
        candidate_name=candidate_name,
        parsed_summary=parsed_summary,
        preferences=pref,
    )

    recruiter_query = f"{company} technical recruiter talent acquisition"
    search_url = f"https://www.linkedin.com/search/results/people/?keywords={quote_plus(recruiter_query)}"

    return OutreachResponse(
        application_id=application.id,
        target_company=company,
        target_role=role,
        hiring_manager_inmail=pkg.hiring_manager_inmail,
        linkedin_connection_note=pkg.linkedin_connection_note,
        follow_up_email=pkg.follow_up_email,
        grounded_highlights=pkg.grounded_highlights,
        linkedin_recruiter_search_url=search_url,
    )


@router.post("/{application_id}/submit")
def submit_application(
    application_id: int,
    request: SubmitApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)

    if application.status != "reviewed":
        raise HTTPException(status_code=409, detail={"error": "application_not_reviewed"})
    if not request.confirm_reviewed or not request.external_confirmation:
        raise HTTPException(status_code=400, detail={"error": "submission_confirmation_required"})

    log_detail = {
        "provided_url": request.application_url is not None,
        "external_submission_confirmed": request.external_confirmation,
    }
    application.application_url = request.application_url
    application.status = "applied"
    application.updated_at = datetime.utcnow()
    db.add(application)
    log = ApplicationSubmissionLog(application_id=application.id, user_id=current_user.id if current_user else None, action="submit_success", detail=log_detail)
    db.add(log)
    db.commit()
    db.refresh(application)

    row = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
        .filter(Application.id == application.id)
        .first()
    )
    if row:
        app_obj, job, version = row
        return _serialize_application(app_obj, job=job, version=version)
    return _serialize_application(application, job=None, version=None)


@router.get("/{application_id}/browser-autofill-plan")
def get_browser_autofill_plan(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)
    return {"browser_autofill_plan": browser_autofill.build_plan(application.autofill_payload)}


@router.get("/{application_id}/ats-compatibility")
def get_ats_compatibility(
    application_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)
    return {"ats_compatibility": ats_integration.detect(application.application_url)}


@router.post("/{application_id}/workflow/n8n")
def trigger_n8n_workflow(
    application_id: int,
    request: N8NEventRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    row = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
        .filter(Application.id == application_id)
        .first()
    )
    if not row:
        raise HTTPException(status_code=404, detail="Application not found")
    application, job, version = row
    _ensure_owner(application.user_id, current_user)
    try:
        payload = n8n_workflows.build_application_event(request.event_type, application, job, version)
        result = n8n_workflows.dispatch(payload)
    except ValueError as exc:
        raise HTTPException(status_code=400, detail={"error": "unsupported_event_type"}) from exc
    except requests.RequestException as exc:
        raise HTTPException(status_code=502, detail={"error": "workflow_dispatch_failed"}) from exc
    return {"workflow": result}


class UpdateAutofillRequest(BaseModel):
    autofill_payload: dict | None = None
    notes: str | None = None
    regenerate: bool = False


@router.patch("/{application_id}/autofill")
def update_autofill(
    application_id: int,
    request: UpdateAutofillRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    _ensure_owner(application.user_id, current_user)

    if request.regenerate:
        # Rebuild payload from stored resume version and job description
        version = db.query(ResumeVersion).filter(ResumeVersion.id == application.resume_version_id).first()
        jd = db.query(JobDescription).filter(JobDescription.id == application.job_description_id).first()
        resume = db.query(Resume).filter(Resume.id == version.resume_id).first() if version else None
        if not version or not jd or not resume:
            raise HTTPException(status_code=400, detail="Cannot regenerate: missing resume or job info")

        # Create a lightweight JobPosting-like object for automation helper
        job_like = type("JobLike", (), {
            "title": jd.title,
            "company": jd.company,
            "location": None,
            "url": None,
            "source": "converted",
        })()

        payload = automation.build_application_autofill(resume.parsed_summary, version, job_like)
        application.autofill_payload = payload
    elif request.autofill_payload is not None:
        application.autofill_payload = request.autofill_payload
    else:
        raise HTTPException(status_code=400, detail="Nothing to update")

    if request.notes is not None:
        application.notes = request.notes
    application.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(application)

    row = (
        db.query(Application, JobDescription, ResumeVersion)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
        .outerjoin(ResumeVersion, Application.resume_version_id == ResumeVersion.id)
        .filter(Application.id == application.id)
        .first()
    )
    if row:
        app_obj, job, version = row
        return _serialize_application(app_obj, job=job, version=version)
    return _serialize_application(application, job=None, version=None)
