from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import applications
from app.database import Base, get_db
from app.models import Application, JobDescription, Resume, ResumeVersion, UserPreference
from app.utils.config import settings


def _build_test_client() -> TestClient:
    settings.auth_enabled = False

    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSession = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)
    session = TestingSession()

    app = FastAPI()

    def override_get_db():
        try:
            yield session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])

    client = TestClient(app)
    client.db = session
    return client


def test_interview_prep_application_not_found():
    client = _build_test_client()
    res = client.get("/api/applications/9999/interview-prep")
    assert res.status_code == 404
    assert "Application not found" in res.json()["detail"]


def test_interview_prep_missing_job_or_version():
    client = _build_test_client()

    # Application references non-existent job and version
    app_record = Application(
        job_description_id=123,
        resume_version_id=456,
        status="pending",
    )
    client.db.add(app_record)
    client.db.commit()

    res = client.get(f"/api/applications/{app_record.id}/interview-prep")
    assert res.status_code == 409
    assert "missing its saved job or resume version" in res.json()["detail"]


def test_interview_prep_missing_resume_record():
    client = _build_test_client()

    job = JobDescription(
        title="Senior Python Engineer",
        company="Razorpay",
        jd_text="Build scalable payments infrastructure using Python and FastAPI.",
    )
    # ResumeVersion referencing non-existent resume ID
    version = ResumeVersion(
        resume_id="non-existent-resume-id",
        version_no=1,
        content_text="Experienced Python backend developer with FastAPI.",
    )
    client.db.add(job)
    client.db.add(version)
    client.db.commit()

    app_record = Application(
        job_description_id=job.id,
        resume_version_id=version.id,
        status="pending",
    )
    client.db.add(app_record)
    client.db.commit()

    res = client.get(f"/api/applications/{app_record.id}/interview-prep")
    assert res.status_code == 409
    assert "resume record is no longer available" in res.json()["detail"]


def test_interview_prep_success_grounded_pack():
    client = _build_test_client()

    resume = Resume(
        id="resume-prep-001",
        original_filename="sarah_resume.pdf",
        stored_path="resumes/sarah_resume.pdf",
        content_hash="hash_prep_001",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={"name": "Sarah Chen", "skills": ["Python", "FastAPI", "Distributed Systems"]},
    )
    job = JobDescription(
        title="Principal Platform Architect",
        company="Swiggy",
        jd_text="We are seeking a Principal Platform Architect with strong Python, FastAPI, Microservices, and Distributed Systems experience to lead food delivery routing infrastructure.",
    )
    client.db.add(resume)
    client.db.add(job)
    client.db.commit()

    version = ResumeVersion(
        resume_id=resume.id,
        version_no=2,
        content_text="Sarah Chen\nArchitected distributed routing pipelines processing 2M requests/sec using Python, FastAPI, Kafka, and PostgreSQL.",
    )
    client.db.add(version)
    client.db.commit()

    app_record = Application(
        job_description_id=job.id,
        resume_version_id=version.id,
        status="interviewing",
        notes="First technical round scheduled",
    )
    client.db.add(app_record)
    client.db.commit()

    res = client.get(f"/api/applications/{app_record.id}/interview-prep")
    assert res.status_code == 200
    pack = res.json()

    assert pack["application_context"]["role"] == "Principal Platform Architect"
    assert pack["application_context"]["company"] == "Swiggy"
    assert pack["application_context"]["resume_version"] == 2
    assert "technical_questions" in pack
    assert "behavioral_questions" in pack
    assert "recruiter_screen_india" in pack
    assert "practice_steps" in pack


def test_interview_prep_auth_required_when_enabled():
    client = _build_test_client()
    settings.auth_enabled = True
    try:
        res = client.get("/api/applications/1/interview-prep")
        assert res.status_code == 401
    finally:
        settings.auth_enabled = False
