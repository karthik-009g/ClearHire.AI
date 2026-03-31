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

    app = FastAPI()

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])

    return TestClient(app)


def test_resume_upload_match_and_tailor_flow(monkeypatch):
    client = _build_test_client()

    monkeypatch.setattr(parser_module.ResumeParserService, "extract_text", lambda self, file_bytes, ext: "Skills\nPython\nExperience\n3 years")
    monkeypatch.setattr(
        parser_module.ResumeParserService,
        "parse_resume",
        lambda self, text: {
            "skills": ["python"],
            "experience_years_estimate": 3,
            "projects_count_estimate": 1,
            "sections": {"skills": ["Python"], "experience": ["3 years"], "projects": []},
        },
    )

    upload = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.docx",
                io.BytesIO(_build_docx_bytes("Skills and experience")),
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
            "jd_text": "Looking for Python FastAPI and PostgreSQL skills with strong API delivery.",
            "title": "Backend Engineer",
            "company": "Acme",
            "source": "manual",
        },
    )
    assert match.status_code == 200
    assert "total_score" in match.json()

    tailor = client.post(
        "/api/resumes/tailor",
        json={
            "resume_id": resume_id,
            "source_version_no": 1,
            "jd_text": "Need Python, FastAPI, PostgreSQL and Kubernetes experience for backend role.",
            "role": "Backend Engineer",
            "company": "Acme",
            "include_cover_letter": True,
            "candidate_name": "Alex",
        },
    )
    assert tailor.status_code == 200
    data = tailor.json()
    assert data["version_no"] == 2
    assert data["based_on_version"] == 1
    assert "tailored_resume_text" in data
    assert data["cover_letter_text"] is not None

    package = client.post(
        "/api/resumes/package/tailor",
        json={
            "resume_id": resume_id,
            "source_version_no": 1,
            "jd_text": "Need Python FastAPI and backend delivery.",
            "role": "Backend Engineer",
            "company": "Acme",
            "include_cover_letter": True,
            "candidate_name": "Alex",
        },
    )
    assert package.status_code == 200
    assert package.headers["content-type"] == "application/zip"


def test_application_tracking_flow(monkeypatch):
    client = _build_test_client()

    monkeypatch.setattr(parser_module.ResumeParserService, "extract_text", lambda self, file_bytes, ext: "Skills\nPython")
    monkeypatch.setattr(
        parser_module.ResumeParserService,
        "parse_resume",
        lambda self, text: {
            "skills": ["python"],
            "experience_years_estimate": 1,
            "projects_count_estimate": 1,
            "sections": {"skills": ["Python"], "experience": [], "projects": []},
        },
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
            "jd_text": "Need Python and API experience with cloud deployment exposure.",
            "title": "Software Engineer",
            "company": "Beta Inc",
            "source": "manual",
        },
    )
    assert match.status_code == 200

    detail = client.get(f"/api/resumes/{resume_id}")
    assert detail.status_code == 200
    assert detail.json()["latest_version"] == 1

    create = client.post(
        "/api/applications/",
        json={
            "job_description_id": 1,
            "resume_version_id": 1,
            "status": "pending",
            "notes": "Ready to apply",
        },
    )
    assert create.status_code == 200
    app_id = create.json()["id"]

    update = client.patch(f"/api/applications/{app_id}/status", json={"status": "applied", "notes": "Submitted"})
    assert update.status_code == 200
    assert update.json()["status"] == "applied"

    listing = client.get("/api/applications/")
    assert listing.status_code == 200
    assert len(listing.json()) == 1
