from __future__ import annotations

from datetime import datetime, timezone
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import jobs
from app.database import Base, get_db
from app.models import JobPosting, Resume, ResumeVersion, User, UserPreference
from app.services.job_scraper_service import ScrapedJob
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
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

    client = TestClient(app)
    client.db = session
    return client


def test_scrape_jobs_endpoint_with_mocked_sources(monkeypatch):
    client = _build_test_client()

    sample_jobs = [
        ScrapedJob(
            source="swiggy",
            company="Swiggy",
            title="Senior Backend Engineer - Python/FastAPI",
            url="https://careers.swiggy.com/jobs/101",
            location="Bengaluru, Karnataka, India",
            description="Build scalable high-throughput backend services using Python, FastAPI, Kafka, and PostgreSQL.",
            scraped_at=datetime.now(timezone.utc),
            posted_at=datetime.now(timezone.utc),
            posted_text="1 day ago",
        ),
        ScrapedJob(
            source="microsoft",
            company="Microsoft",
            title="Software Development Engineer 2",
            url="https://jobs.careers.microsoft.com/global/en/search/202",
            location="Hyderabad, Telangana, India",
            description="Design and implement distributed cloud infrastructure on Azure with Python and C++.",
            scraped_at=datetime.now(timezone.utc),
            posted_at=datetime.now(timezone.utc),
            posted_text="2 days ago",
        ),
    ]

    monkeypatch.setattr(jobs.scraper, "scrape_sources", lambda *args, **kwargs: sample_jobs)
    monkeypatch.setattr(jobs.direct_ats, "fetch_all_direct_jobs", lambda *args, **kwargs: [])

    response = client.post(
        "/api/jobs/scrape",
        json={
            "sources": ["swiggy", "microsoft"],
            "keywords": ["Python", "Backend"],
            "locations": ["Bengaluru", "Hyderabad"],
            "direct_portals_only": False,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scraped_count"] >= 2
    assert len(payload["jobs"]) >= 2
    companies = [j["company"] for j in payload["jobs"]]
    assert "Swiggy" in companies
    assert "Microsoft" in companies


def test_scrape_jobs_direct_portals_only(monkeypatch):
    client = _build_test_client()

    direct_ats_jobs = [
        ScrapedJob(
            source="direct_ats",
            company="Postman",
            title="Staff Platform Engineer",
            url="https://jobs.lever.co/postman/direct-303",
            location="Bengaluru, India",
            description="Direct career portal posting for high-scale API platform development.",
            scraped_at=datetime.now(timezone.utc),
            posted_at=datetime.now(timezone.utc),
            posted_text="Just now",
        )
    ]

    monkeypatch.setattr(jobs.scraper, "scrape_sources", lambda *args, **kwargs: [])
    monkeypatch.setattr(jobs.direct_ats, "fetch_all_direct_jobs", lambda *args, **kwargs: direct_ats_jobs)

    response = client.post(
        "/api/jobs/scrape",
        json={
            "direct_portals_only": True,
            "keywords": ["Platform"],
            "locations": ["Bengaluru"],
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["scraped_count"] == 1
    assert payload["jobs"][0]["company"] == "Postman"
    assert payload["jobs"][0]["title"] == "Staff Platform Engineer"


def test_scrape_jobs_requires_auth_when_enabled(monkeypatch):
    client = _build_test_client()
    settings.auth_enabled = True
    try:
        response = client.post("/api/jobs/scrape", json={"keywords": ["Python"]})
        assert response.status_code == 401
        assert "Authentication required" in response.json()["detail"]
    finally:
        settings.auth_enabled = False


def test_jobs_preferences_get_default_and_post_custom():
    client = _build_test_client()

    # 1. GET default preferences
    get_res = client.get("/api/jobs/preferences")
    assert get_res.status_code == 200
    defaults = get_res.json()
    assert defaults["target_role"] == "Software Engineer"
    assert defaults["direct_portals_only"] is False

    # 2. POST update preferences
    update_payload = {
        "preferred_email": "candidate.lead@clearhire.ai",
        "target_role": "Principal Software Engineer",
        "locations": ["Bengaluru", "Hyderabad", "Pune"],
        "keywords": ["Python", "FastAPI", "Distributed Systems", "PostgreSQL"],
        "selected_sources": ["linkedin", "swiggy", "direct_ats"],
        "target_companies": ["Swiggy", "Postman", "Razorpay", "BrowserStack"],
        "exclude_staffing_agencies": True,
        "max_ghosting_risk": "medium_and_low",
        "direct_portals_only": True,
        "max_post_age_days": 2,
        "notice_period_days": 30,
        "serving_notice": True,
        "current_ctc_lpa": 38.0,
        "expected_ctc_lpa": 52.0,
        "work_mode": "Hybrid",
        "auto_schedule_enabled": True,
        "schedule_time": "08:30",
        "schedule_timezone": "Asia/Kolkata",
        "auto_scrape_on_login": True,
        "auto_email_after_scrape": True,
    }

    post_res = client.post("/api/jobs/preferences", json=update_payload)
    assert post_res.status_code == 200
    saved = post_res.json()
    assert saved["preferred_email"] == "candidate.lead@clearhire.ai"
    assert saved["target_role"] == "Principal Software Engineer"
    assert saved["serving_notice"] is True
    assert saved["notice_period_days"] == 30
    assert saved["current_ctc_lpa"] == 38.0
    assert saved["expected_ctc_lpa"] == 52.0
    assert saved["direct_portals_only"] is True

    # 3. GET verify persistence
    get_verify = client.get("/api/jobs/preferences")
    assert get_verify.status_code == 200
    persisted = get_verify.json()
    assert persisted["preferred_email"] == "candidate.lead@clearhire.ai"
    assert persisted["target_role"] == "Principal Software Engineer"
    assert "Bengaluru" in persisted["locations"]
    assert "Razorpay" in persisted["target_companies"]


def test_jobs_preferences_validation_error():
    client = _build_test_client()
    # Invalid email address should fail Pydantic validation (422)
    response = client.post(
        "/api/jobs/preferences",
        json={
            "preferred_email": "not-an-email",
            "target_role": "Backend Engineer",
        },
    )
    assert response.status_code == 422


def test_jobs_digest_endpoint(monkeypatch):
    client = _build_test_client()

    # 1. Non-existent resume returns 404
    missing_res = client.post("/api/jobs/digest", json={"resume_id": "non-existent-uuid"})
    assert missing_res.status_code == 404
    assert "Resume not found" in missing_res.json()["detail"]

    # 2. Setup database resume and version
    resume = Resume(
        id="resume-digest-001",
        original_filename="test_resume.pdf",
        stored_path="resumes/test_resume.pdf",
        content_hash="abc123hash",
        expires_at=datetime.now(timezone.utc),
        parsed_summary={"skills": ["Python", "FastAPI", "SQL"]},
    )
    version = ResumeVersion(
        resume_id="resume-digest-001",
        version_no=1,
        content_text="Experienced Python FastAPI backend developer with PostgreSQL experience.",
        embedding=[0.05] * settings.embedding_dimensions,
        embedding_vector=[0.05] * settings.embedding_dimensions,
    )
    client.db.add(resume)
    client.db.add(version)
    client.db.commit()

    sample_jobs = [
        ScrapedJob(
            source="direct_ats",
            company="Razorpay",
            title="Senior Backend Engineer",
            url="https://jobs.lever.co/razorpay/404",
            location="Bengaluru, India",
            description="Python FastAPI backend role for payments infrastructure.",
            scraped_at=datetime.now(timezone.utc),
            posted_at=datetime.now(timezone.utc),
        )
    ]
    monkeypatch.setattr(jobs.scraper, "scrape_sources", lambda *args, **kwargs: sample_jobs)
    monkeypatch.setattr(jobs.emailer, "is_configured", lambda: True)
    monkeypatch.setattr(jobs.emailer, "send_html_email", lambda *args, **kwargs: None)

    response = client.post(
        "/api/jobs/digest",
        json={
            "resume_id": "resume-digest-001",
            "target_email": "digest.recipient@clearhire.ai",
            "top_n": 5,
        },
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["recipient"] == "digest.recipient@clearhire.ai"
    assert payload["sent"] is True
    assert payload["job_count"] >= 1
