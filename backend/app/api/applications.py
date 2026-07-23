"""Minimal application tracking APIs for V1."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import Application, JobDescription, Resume, ResumeVersion, User
from app.utils.auth import get_current_user_optional
from app.utils.config import settings

router = APIRouter()
VALID_APPLICATION_STATUSES = {"pending", "applied"}


def _serialize_application(
    application: Application,
    job: JobDescription | None = None,
    version: ResumeVersion | None = None,
) -> dict:
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


@router.post("/")
def create_application(
    request: CreateApplicationRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if request.status not in VALID_APPLICATION_STATUSES:
        raise HTTPException(status_code=400, detail="status must be pending or applied")

    version = db.query(ResumeVersion).filter(ResumeVersion.id == request.resume_version_id).first()
    if not version:
        raise HTTPException(status_code=404, detail="Resume version not found")

    job = db.query(JobDescription).filter(JobDescription.id == request.job_description_id).first()
    if not job:
        raise HTTPException(status_code=404, detail="Job description not found")

    if settings.auth_enabled and current_user:
        resume = db.query(Resume).filter(Resume.id == version.resume_id).first()
        if not resume or resume.user_id != current_user.id:
            raise HTTPException(status_code=403, detail="Not allowed for this resume version")

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
    raise HTTPException(status_code=503, detail="Autofill is on hold. Current V1 supports scrape + top-match email only.")


@router.patch("/{application_id}/status")
def update_application_status(
    application_id: int,
    request: UpdateStatusRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    if request.status not in VALID_APPLICATION_STATUSES:
        raise HTTPException(status_code=400, detail="status must be pending or applied")

    application = db.query(Application).filter(Application.id == application_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")
    if settings.auth_enabled and current_user and application.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not allowed for this application")

    application.status = request.status
    application.notes = request.notes
    application.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(application)

    job = db.query(JobDescription).filter(JobDescription.id == application.job_description_id).first()
    version = db.query(ResumeVersion).filter(ResumeVersion.id == application.resume_version_id).first()
    return _serialize_application(application, job=job, version=version)


@router.get("/")
def list_applications(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    query = db.query(Application)
    if settings.auth_enabled and current_user:
        query = query.filter(Application.user_id == current_user.id)

    rows = query.order_by(Application.updated_at.desc()).all()
    job_ids = {row.job_description_id for row in rows}
    version_ids = {row.resume_version_id for row in rows}
    jobs = {job.id: job for job in db.query(JobDescription).filter(JobDescription.id.in_(job_ids)).all()} if job_ids else {}
    versions = {version.id: version for version in db.query(ResumeVersion).filter(ResumeVersion.id.in_(version_ids)).all()} if version_ids else {}
    return [_serialize_application(row, job=jobs.get(row.job_description_id), version=versions.get(row.resume_version_id)) for row in rows]
