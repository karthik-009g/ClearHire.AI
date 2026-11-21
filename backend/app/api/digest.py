"""Morning Alert Digest & Funnel Analytics APIs."""

from __future__ import annotations

from typing import Any
from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, EmailStr, Field, field_validator
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, DigestLog, JobDescription, User, UserPreference
from app.services.notification_digest_service import NotificationDigestService
from app.utils.auth import get_current_user_optional
from app.utils.config import settings

router = APIRouter()
analytics_router = APIRouter()
digest_service = NotificationDigestService()


class SendDigestRequest(BaseModel):
    channels: list[str] = Field(default_factory=lambda: ["email"])
    email: EmailStr | None = None
    telegram_chat_id: str | None = None
    whatsapp_number: str | None = None

    @field_validator("channels")
    @classmethod
    def validate_channels(cls, channels: list[str]) -> list[str]:
        allowed = {"email", "telegram", "whatsapp"}
        normalized = list(dict.fromkeys(channel.strip().lower() for channel in channels if channel.strip()))
        if not normalized or any(channel not in allowed for channel in normalized):
            raise ValueError("Choose one or more supported channels: email, telegram, whatsapp")
        return normalized


def _require_user_when_auth_enabled(current_user: User | None) -> None:
    if settings.auth_enabled and current_user is None:
        raise HTTPException(status_code=401, detail="Sign in to access your application data")


@router.get("/preview")
def preview_morning_digest(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_user_when_auth_enabled(current_user)
    query = (
        db.query(Application, JobDescription)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
    )
    if settings.auth_enabled and current_user:
        query = query.filter(Application.user_id == current_user.id)
    results = query.order_by(Application.updated_at.desc()).all()

    apps = [app for app, _ in results]
    jmap = {job.id: job for _, job in results if job is not None}

    pref_query = db.query(UserPreference)
    if settings.auth_enabled and current_user:
        pref_query = pref_query.filter(UserPreference.user_id == current_user.id)
    pref = pref_query.first()

    candidate_name = "Candidate"
    if current_user and getattr(current_user, "email", None):
        candidate_name = current_user.email.split("@")[0].capitalize()

    payload = digest_service.build_morning_digest(
        candidate_name=candidate_name,
        preferences=pref,
        applications=apps,
        jobs_map=jmap,
    )
    return payload


@router.post("/send")
def send_morning_digest(
    request: SendDigestRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_user_when_auth_enabled(current_user)
    query = (
        db.query(Application, JobDescription)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
    )
    if settings.auth_enabled and current_user:
        query = query.filter(Application.user_id == current_user.id)
    results = query.order_by(Application.updated_at.desc()).all()

    apps = [app for app, _ in results]
    jmap = {job.id: job for _, job in results if job is not None}

    pref_query = db.query(UserPreference)
    if settings.auth_enabled and current_user:
        pref_query = pref_query.filter(UserPreference.user_id == current_user.id)
    pref = pref_query.first()

    candidate_name = "Candidate"
    if current_user and getattr(current_user, "email", None):
        candidate_name = current_user.email.split("@")[0].capitalize()

    payload = digest_service.build_morning_digest(
        candidate_name=candidate_name,
        preferences=pref,
        applications=apps,
        jobs_map=jmap,
    )

    recipient_info = {
        "email": request.email or getattr(pref, "preferred_email", None) or (current_user.email if current_user else None),
        "telegram_chat_id": request.telegram_chat_id or getattr(pref, "telegram_chat_id", None),
        "whatsapp_number": request.whatsapp_number or getattr(pref, "whatsapp_number", None),
    }

    user_id = current_user.id if current_user else None
    results = digest_service.dispatch_digest(
        digest=payload,
        channels=request.channels,
        recipient_info=recipient_info,
        user_id=user_id,
        db_session=db,
    )
    return {
        "dispatched": results,
        "digest_summary": {
            "jobs_count": len(payload.top_jobs),
            "alerts_count": len(payload.ghosting_alerts),
            "email_subject": payload.email_subject,
        },
    }


@router.get("/history")
def get_digest_history(
    limit: int = 20,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_user_when_auth_enabled(current_user)
    query = db.query(DigestLog)
    if settings.auth_enabled and current_user:
        query = query.filter(DigestLog.user_id == current_user.id)
    logs = query.order_by(DigestLog.created_at.desc()).limit(limit).all()
    return logs


@analytics_router.get("/funnel")
def get_recruitment_funnel_analytics(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    _require_user_when_auth_enabled(current_user)
    query = (
        db.query(Application, JobDescription)
        .outerjoin(JobDescription, Application.job_description_id == JobDescription.id)
    )
    if settings.auth_enabled and current_user:
        query = query.filter(Application.user_id == current_user.id)
    results = query.order_by(Application.updated_at.desc()).all()

    apps = [app for app, _ in results]
    jmap = {job.id: job for _, job in results if job is not None}

    metrics = digest_service.compute_funnel_analytics(apps, jmap)
    return metrics
