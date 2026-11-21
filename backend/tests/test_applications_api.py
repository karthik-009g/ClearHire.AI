from __future__ import annotations

import io

from fastapi import FastAPI
from fastapi.testclient import TestClient
from docx import Document
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import applications, resumes
from app.database import Base, get_db
from app.models import JobPosting
from app.services import parser_service as parser_module
from app.utils.config import settings


def _build_docx_bytes(text: str = "Sample resume") -> bytes:
    buffer = io.BytesIO()
    document = Document()
    document.add_paragraph(text)
    document.save(buffer)
    return buffer.getvalue()


def _build_test_client() -> TestClient:
    settings.auth_enabled = False
    engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    # Use a shared session instance so tests can inspect/modify DB easily
    shared_session = TestingSessionLocal()

    app = FastAPI()

    def override_get_db():
        try:
            yield shared_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])

    client = TestClient(app)
    client.db = shared_session
    return client


def test_autofill_persist_submit_and_regenerate(monkeypatch):
    client = _build_test_client()

    # Make parser deterministic
    monkeypatch.setattr(parser_module.ResumeParserService, "extract_text", lambda self, file_bytes, ext: "Skills\nPython")
    monkeypatch.setattr(
        parser_module.ResumeParserService,
        "parse_resume",
        lambda self, text: {
            "skills": ["python"],
            "experience_years_estimate": 2,
            "projects_count_estimate": 1,
            "sections": {"skills": ["Python"], "experience": ["2 years"], "projects": []},
            "autofill_readiness": {"ready": True, "missing_required_fields": []},
        },
    )

    upload = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.docx",
                io.BytesIO(_build_docx_bytes("Python backend experience")),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert upload.status_code == 200
    resume_id = upload.json()["resume_id"]

    match = client.post(
        "/api/resumes/match",
        json={
            "resume_id": resume_id,
            "jd_text": "Need Python and API experience",
            "title": "Software Engineer",
            "company": "TestCo",
            "source": "manual",
        },
    )
    assert match.status_code == 200
    job_posting_id = match.json()["job_description_id"]

    # Persist autofill as draft
    settings.rate_limit_applications_per_hour = 10
    # Create a JobPosting row for the posting id expected by the autofill API
    jp = JobPosting(source="manual", company="TestCo", title="Software Engineer", location=None, url="http://example.test/job/1", description="", embedding=None, embedding_vector=None)
    client.db.add(jp)
    client.db.commit()
    client.db.refresh(jp)
    autofill = client.post("/api/applications/autofill", json={"resume_id": resume_id, "job_posting_id": jp.id, "persist": True})
    assert autofill.status_code == 200
    app_obj = autofill.json()["application"]
    app_id = app_obj["id"]

    # The API records a user-confirmed external submission; it never submits to the employer.
    review = client.post(f"/api/applications/{app_id}/review", json={"confirm_fields_reviewed": True})
    assert review.status_code == 200
    assert review.json()["status"] == "reviewed"
    missing_confirmation = client.post(
        f"/api/applications/{app_id}/submit",
        json={"application_url": "https://apply.example.com/123", "confirm_reviewed": True},
    )
    assert missing_confirmation.status_code == 400
    assert missing_confirmation.json()["detail"]["error"] == "submission_confirmation_required"
    submit = client.post(
        f"/api/applications/{app_id}/submit",
        json={
            "application_url": "https://apply.example.com/123",
            "confirm_reviewed": True,
            "external_confirmation": True,
        },
    )
    assert submit.status_code == 200
    assert submit.json()["status"] == "applied"
    assert submit.json()["application_url"] == "https://apply.example.com/123"

    # Regenerate autofill
    regen = client.patch(f"/api/applications/{app_id}/autofill", json={"regenerate": True})
    assert regen.status_code == 200
    assert regen.json()["autofill_payload"] is not None


def test_application_helpers_are_fill_only_and_n8n_disabled():
    client = _build_test_client()
    from app.models import Application, JobDescription, ResumeVersion

    job = JobDescription(title="Engineer", company="TestCo", jd_text="Python")
    client.db.add(job)
    client.db.flush()
    version = ResumeVersion(resume_id="resume-x", version_no=1, content_text="Python", embedding=None)
    client.db.add(version)
    client.db.flush()
    application = Application(
        job_description_id=job.id,
        resume_version_id=version.id,
        status="pending",
        application_url="https://boards.greenhouse.io/test/jobs/1",
        autofill_payload={"email": "candidate@example.com", "review_required": True},
    )
    client.db.add(application)
    client.db.commit()
    client.db.refresh(application)

    plan = client.get(f"/api/applications/{application.id}/browser-autofill-plan")
    assert plan.status_code == 200
    assert plan.json()["browser_autofill_plan"]["policy"]["never_submit"] is True
    ats = client.get(f"/api/applications/{application.id}/ats-compatibility")
    assert ats.status_code == 200
    assert ats.json()["ats_compatibility"]["ats"] == "Greenhouse"
    event = client.post(
        f"/api/applications/{application.id}/workflow/n8n",
        json={"event_type": "application_reviewed"},
    )
    assert event.status_code == 200
    assert event.json()["workflow"]["status"] == "disabled"


def test_rate_limit_for_persist(monkeypatch):
    client = _build_test_client()
    # Clear in-memory rate limiter to ensure test isolation
    from app.utils.rate_limit import _RATE_STORE
    _RATE_STORE.clear()
    monkeypatch.setattr(parser_module.ResumeParserService, "extract_text", lambda self, file_bytes, ext: "Skills\nPython")
    monkeypatch.setattr(
        parser_module.ResumeParserService,
        "parse_resume",
        lambda self, text: {"skills": ["python"], "experience_years_estimate": 1, "projects_count_estimate": 0, "sections": {}, "autofill_readiness": {"ready": True, "missing_required_fields": []}},
    )

    upload = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.docx",
                io.BytesIO(_build_docx_bytes("Python resume")),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    resume_id = upload.json()["resume_id"]

    match = client.post(
        "/api/resumes/match",
        json={
            "resume_id": resume_id,
            "jd_text": "Need Python",
            "title": "Engineer",
            "company": "X",
            "source": "manual",
        },
    )
    job_posting_id = match.json().get("job_description_id")

    # Set low rate limit
    settings.rate_limit_applications_per_hour = 1

    # Ensure a JobPosting exists for autofill
    jp = JobPosting(source="manual", company="X", title="Engineer", location=None, url="http://example.test/job/2", description="", embedding=None, embedding_vector=None)
    client.db.add(jp)
    client.db.commit()
    client.db.refresh(jp)

    first = client.post("/api/applications/autofill", json={"resume_id": resume_id, "job_posting_id": jp.id, "persist": True})
    assert first.status_code == 200

    another_job = JobPosting(source="manual", company="Y", title="Data Engineer", location=None, url="http://example.test/job/3", description="", embedding=None, embedding_vector=None)
    client.db.add(another_job)
    client.db.commit()
    client.db.refresh(another_job)
    second = client.post("/api/applications/autofill", json={"resume_id": resume_id, "job_posting_id": another_job.id, "persist": True})
    assert second.status_code == 429


def test_kanban_status_transitions_and_outreach():
    from datetime import datetime, timedelta
    from app.models import Application, JobDescription, ResumeVersion

    client = _build_test_client()
    settings.rate_limit_applications_per_hour = 50

    job = JobDescription(title="Staff Backend Engineer", company="Razorpay", jd_text="Go, Kubernetes, Payments")
    client.db.add(job)
    client.db.flush()

    version = ResumeVersion(resume_id="resume-kanban", version_no=1, content_text="Go and distributed systems", embedding=None)
    client.db.add(version)
    client.db.flush()

    app = Application(
        job_description_id=job.id,
        resume_version_id=version.id,
        status="applied",
        application_url="https://boards.greenhouse.io/razorpay/jobs/101",
    )
    client.db.add(app)
    client.db.commit()
    client.db.refresh(app)

    # 1. Advance to screening
    to_screen = client.patch(f"/api/applications/{app.id}/status", json={"status": "screening"})
    assert to_screen.status_code == 200
    assert to_screen.json()["status"] == "screening"

    # 2. Advance to interviewing
    to_interview = client.patch(f"/api/applications/{app.id}/status", json={"status": "interviewing"})
    assert to_interview.status_code == 200
    assert to_interview.json()["status"] == "interviewing"

    # 3. Advance to offer
    to_offer = client.patch(f"/api/applications/{app.id}/status", json={"status": "offer"})
    assert to_offer.status_code == 200
    assert to_offer.json()["status"] == "offer"

    # 4. Generate outreach for this application
    outreach = client.post(f"/api/applications/{app.id}/outreach")
    assert outreach.status_code == 200
    res = outreach.json()
    assert res["target_company"] == "Razorpay"
    assert res["target_role"] == "Staff Backend Engineer"
    assert "Razorpay" in res["hiring_manager_inmail"]
    assert len(res["linkedin_connection_note"]) <= 300
    assert "linkedin.com/search" in res["linkedin_recruiter_search_url"]

    # 5. Generic outreach endpoint
    gen_outreach = client.post(
        "/api/applications/outreach",
        json={"company": "Postman", "role": "Tech Lead", "candidate_name": "Divya"},
    )
    assert gen_outreach.status_code == 200
    gen_res = gen_outreach.json()
    assert gen_res["target_company"] == "Postman"
    assert "Divya" in gen_res["hiring_manager_inmail"]


def test_ghosting_alerts_and_aged_applications():
    from datetime import datetime, timedelta
    from app.models import Application, JobDescription, ResumeVersion

    client = _build_test_client()

    job = JobDescription(title="Frontend Developer", company="Zepto", jd_text="React")
    client.db.add(job)
    client.db.flush()

    version = ResumeVersion(resume_id="resume-ghost", version_no=1, content_text="React", embedding=None)
    client.db.add(version)
    client.db.flush()

    # Create an application applied 20 days ago
    aged_date = datetime.utcnow() - timedelta(days=20)
    app = Application(
        job_description_id=job.id,
        resume_version_id=version.id,
        status="applied",
        application_url="https://jobs.ashbyhq.com/zepto/1",
        updated_at=aged_date,
    )
    client.db.add(app)
    client.db.commit()

    alerts = client.get("/api/applications/ghosting-alerts")
    assert alerts.status_code == 200
    data = alerts.json()
    assert data["total_applications"] >= 1
    assert data["ghosted_count"] >= 1
    assert data["ghosting_rate_percent"] > 0
    assert len(data["ghosted_applications"]) >= 1
    assert data["ghosted_applications"][0]["is_ghosted"] is True
    assert data["ghosted_applications"][0]["days_since_update"] >= 19
    # Fresh direct ATS recommendations present
    assert isinstance(data["recommended_alternatives"], list)

