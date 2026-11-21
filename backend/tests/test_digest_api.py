from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import digest
from app.database import Base, get_db
from app.models import Application, DigestLog, JobDescription, UserPreference
from app.utils.config import settings


@pytest.fixture(autouse=True)
def prevent_live_ats_requests(monkeypatch):
    monkeypatch.setattr(digest.digest_service.direct_ats, "get_direct_jobs", lambda *args, **kwargs: [])


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
    app.include_router(digest.router, prefix="/api/digest", tags=["digest"])
    app.include_router(digest.analytics_router, prefix="/api/analytics", tags=["analytics"])

    client = TestClient(app)
    client.db = session
    return client


def test_preview_morning_digest_endpoint(monkeypatch):
    public_job = SimpleNamespace(
        source="lever_postman",
        ats_type="lever",
        title="Staff Engineer",
        company="Postman",
        location="Remote",
        url="https://jobs.lever.co/postman/active-job",
        salary_range=None,
    )
    monkeypatch.setattr(digest.digest_service.direct_ats, "get_direct_jobs", lambda *args, **kwargs: [public_job])
    client = _build_test_client()

    # Seed an application
    now = datetime.utcnow()
    job = JobDescription(title="Staff Engineer", company="Postman", jd_text="APIs")
    client.db.add(job)
    client.db.flush()

    app = Application(
        job_description_id=job.id,
        resume_version_id=1,
        status="applied",
        application_url="https://jobs.lever.co/postman/1",
        updated_at=now - timedelta(days=15),
    )
    client.db.add(app)
    client.db.commit()

    resp = client.get("/api/digest/preview")
    assert resp.status_code == 200
    data = resp.json()
    assert "top_jobs" in data
    assert len(data["top_jobs"]) >= 1
    assert "ghosting_alerts" in data
    assert len(data["ghosting_alerts"]) >= 1
    assert "Postman" in data["ghosting_alerts"][0]["company"]
    assert "funnel_metrics" in data
    assert data["funnel_metrics"]["applied"] >= 1
    assert "telegram_text" in data
    assert "whatsapp_text" in data
    assert "email_html" in data


def test_send_and_history_digest_endpoints():
    client = _build_test_client()

    # 1. Trigger send
    send_resp = client.post(
        "/api/digest/send",
        json={
            "channels": ["email", "telegram"],
            "email": "test@clearhire.ai",
            "telegram_chat_id": "@testcandidate",
        },
    )
    assert send_resp.status_code == 200
    data = send_resp.json()
    assert "dispatched" in data
    assert len(data["dispatched"]) == 2
    assert "digest_summary" in data

    # 2. Check history
    hist_resp = client.get("/api/digest/history")
    assert hist_resp.status_code == 200
    history = hist_resp.json()
    assert len(history) == 2
    channels = {h["channel"] for h in history}
    assert channels == {"email", "telegram"}


def test_recruitment_funnel_analytics_endpoint():
    client = _build_test_client()

    now = datetime.utcnow()
    # Add pipeline data: 1 applied, 1 screening, 1 offer
    for status in ["applied", "screening", "offer"]:
        job = JobDescription(title=f"Engineer {status}", company=f"Company {status}", jd_text="Engineering role description")
        client.db.add(job)
        client.db.flush()
        app = Application(
            job_description_id=job.id,
            resume_version_id=1,
            status=status,
            updated_at=now - timedelta(days=3),
        )
        client.db.add(app)
    client.db.commit()

    funnel_resp = client.get("/api/analytics/funnel")
    assert funnel_resp.status_code == 200
    metrics = funnel_resp.json()
    assert metrics["total_tracked"] == 3
    assert metrics["applied"] == 3
    assert metrics["screening"] == 2  # screening, offer
    assert metrics["offer"] == 1
    assert metrics["screen_conversion_rate"] > 0
    assert metrics["offer_rate"] > 0
