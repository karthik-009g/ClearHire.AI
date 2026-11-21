from __future__ import annotations

from datetime import datetime, timezone
import io
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import resumes
from app.database import Base, get_db
from app.models import Resume, ResumeVersion, User
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
    app.include_router(resumes.router, prefix="/api/resumes", tags=["resumes"])

    client = TestClient(app)
    client.db = session
    return client


def test_list_resume_versions():
    client = _build_test_client()

    # 1. Non-existent resume returns 404
    res_missing = client.get("/api/resumes/non-existent-id/versions")
    assert res_missing.status_code == 404
    assert "Resume not found" in res_missing.json()["detail"]

    # 2. Add resume with multiple versions
    resume = Resume(
        id="resume-vers-101",
        original_filename="sarah_chen_resume.pdf",
        stored_path="resumes/sarah_chen_resume.pdf",
        content_hash="hash101",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={"name": "Sarah Chen", "skills": ["Python", "FastAPI"]},
    )
    v1 = ResumeVersion(
        resume_id="resume-vers-101",
        version_no=1,
        content_text="Sarah Chen v1 resume text",
    )
    v2 = ResumeVersion(
        resume_id="resume-vers-101",
        version_no=2,
        content_text="Sarah Chen v2 tailored resume text",
    )
    client.db.add(resume)
    client.db.add(v1)
    client.db.add(v2)
    client.db.commit()

    # 3. Retrieve versions
    res = client.get("/api/resumes/resume-vers-101/versions")
    assert res.status_code == 200
    payload = res.json()
    assert payload["resume_id"] == "resume-vers-101"
    assert len(payload["versions"]) == 2
    version_numbers = [v["version_no"] for v in payload["versions"]]
    assert version_numbers == [1, 2]


def test_list_resume_versions_auth_ownership():
    client = _build_test_client()

    resume = Resume(
        id="resume-auth-test",
        user_id="user-owner-1",
        original_filename="resume.pdf",
        stored_path="resumes/resume.pdf",
        content_hash="hash_auth",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={},
    )
    client.db.add(resume)
    client.db.commit()

    settings.auth_enabled = True
    try:
        # Without auth user, _ensure_resume_owner raises 401
        res = client.get("/api/resumes/resume-auth-test/versions")
        assert res.status_code == 401
    finally:
        settings.auth_enabled = False


def test_download_resume_file(monkeypatch):
    client = _build_test_client()

    # 1. 404 for non-existent resume
    missing_res = client.get("/api/resumes/missing-resume-id/download")
    assert missing_res.status_code == 404

    # 2. Resume with missing stored path
    resume_no_path = Resume(
        id="resume-no-path",
        original_filename="test.pdf",
        stored_path="",
        content_hash="hash_nopath",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={},
    )
    client.db.add(resume_no_path)
    client.db.commit()

    no_path_res = client.get("/api/resumes/resume-no-path/download")
    assert no_path_res.status_code == 404
    assert "No stored file found" in no_path_res.json()["detail"]

    # 3. Resume with valid file on storage provider
    sample_pdf_bytes = b"%PDF-1.4 sample resume binary content"
    resume_with_file = Resume(
        id="resume-valid-file",
        original_filename="sarah_chen_lead.pdf",
        stored_path="resumes/sarah_chen_lead.pdf",
        content_hash="hash_valid_file",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={},
    )
    client.db.add(resume_with_file)
    client.db.commit()

    monkeypatch.setattr(resumes.storage, "get_file", lambda path: sample_pdf_bytes)

    valid_res = client.get("/api/resumes/resume-valid-file/download")
    assert valid_res.status_code == 200
    assert valid_res.content == sample_pdf_bytes
    assert valid_res.headers["content-type"] == "application/pdf"
    assert 'attachment; filename="sarah_chen_lead.pdf"' in valid_res.headers["content-disposition"]

    # 4. Storage provider raises FileNotFoundError
    def _raise_missing(path):
        raise FileNotFoundError(f"File not found: {path}")

    monkeypatch.setattr(resumes.storage, "get_file", _raise_missing)
    storage_missing_res = client.get("/api/resumes/resume-valid-file/download")
    assert storage_missing_res.status_code == 404
    assert "could not be found" in storage_missing_res.json()["detail"]


def test_cleanup_expired_resumes(monkeypatch):
    client = _build_test_client()

    monkeypatch.setattr(resumes, "cleanup_expired_resumes", lambda db, storage, user_id=None: (3, 2))

    res = client.post("/api/resumes/cleanup-expired")
    assert res.status_code == 200
    payload = res.json()
    assert payload["deleted_records"] == 3
    assert payload["deleted_files"] == 2


def test_export_version_pdf(monkeypatch):
    client = _build_test_client()

    # 1. Missing resume returns 404
    missing_res = client.get("/api/resumes/missing-resume/versions/1/export-pdf")
    assert missing_res.status_code == 404

    # 2. Existing resume, missing version returns 404
    resume = Resume(
        id="resume-pdf-test",
        original_filename="resume.pdf",
        stored_path="resumes/resume.pdf",
        content_hash="hash_pdf",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={
            "name": "Sarah Chen",
            "contact": {
                "email": "sarah.chen@alum.mit.edu",
                "phone": "+1-555-0199",
                "linkedin": "linkedin.com/in/sarahchen",
            },
        },
    )
    client.db.add(resume)
    client.db.commit()

    missing_ver_res = client.get("/api/resumes/resume-pdf-test/versions/1/export-pdf")
    assert missing_ver_res.status_code == 404
    assert "Resume version not found" in missing_ver_res.json()["detail"]

    # 3. Add version and export PDF
    version = ResumeVersion(
        resume_id="resume-pdf-test",
        version_no=1,
        content_text="Sarah Chen - Principal Systems Architect with expertise in distributed platforms.",
    )
    client.db.add(version)
    client.db.commit()

    fake_pdf_bytes = b"%PDF-1.4 simulated ats formatted pdf"
    monkeypatch.setattr(resumes.PdfGeneratorService, "generate_ats_pdf", lambda self, **kwargs: fake_pdf_bytes)

    export_res = client.get("/api/resumes/resume-pdf-test/versions/1/export-pdf")
    assert export_res.status_code == 200
    assert export_res.content == fake_pdf_bytes
    assert export_res.headers["content-type"] == "application/pdf"
    assert 'filename="resume_resume-pdf-test_v1.pdf"' in export_res.headers["content-disposition"]
    assert "inline" in export_res.headers["content-disposition"]
