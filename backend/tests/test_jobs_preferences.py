from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import jobs
from app.database import Base, get_db
from app.utils.config import settings


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
    app.include_router(jobs.router, prefix="/api/jobs", tags=["jobs"])

    return TestClient(app)


def test_get_preferences_returns_defaults_when_missing():
    client = _build_test_client()

    response = client.get("/api/jobs/preferences")

    assert response.status_code == 200
    payload = response.json()
    assert payload["target_role"] == "Software Engineer"
    assert payload["schedule_time"] == "09:00"
    assert payload["schedule_timezone"] == settings.default_schedule_timezone
    assert payload["auto_schedule_enabled"] is False
    assert isinstance(payload["selected_sources"], list)
    assert len(payload["selected_sources"]) >= 1
    assert payload["exclude_staffing_agencies"] is True
    assert payload["max_ghosting_risk"] == "medium_and_low"
    assert payload["direct_portals_only"] is False


def test_upsert_and_get_preferences_with_indian_market_fields():
    client = _build_test_client()

    request_data = {
        "preferred_email": "candidate@clearhire.ai",
        "target_role": "Lead Backend Engineer",
        "locations": ["Bengaluru", "Hyderabad", "Remote"],
        "keywords": ["Python", "FastAPI", "Distributed Systems"],
        "selected_sources": ["naukri", "linkedin"],
        "target_companies": ["Razorpay", "Postman", "CRED", "Swiggy"],
        "exclude_staffing_agencies": True,
        "max_ghosting_risk": "low_only",
        "direct_portals_only": True,
        "max_post_age_days": 3,
        "notice_period_days": 30,
        "serving_notice": True,
        "current_ctc_lpa": 28.0,
        "expected_ctc_lpa": 42.0,
        "work_mode": "hybrid",
        "auto_schedule_enabled": True,
        "schedule_time": "08:30",
        "schedule_timezone": "Asia/Kolkata",
        "auto_scrape_on_login": True,
        "auto_email_after_scrape": True,
    }

    post_resp = client.post("/api/jobs/preferences", json=request_data)
    assert post_resp.status_code == 200
    post_payload = post_resp.json()
    assert post_payload["target_role"] == "Lead Backend Engineer"
    assert post_payload["target_companies"] == ["Razorpay", "Postman", "CRED", "Swiggy"]
    assert post_payload["exclude_staffing_agencies"] is True
    assert post_payload["max_ghosting_risk"] == "low_only"
    assert post_payload["direct_portals_only"] is True
    assert post_payload["notice_period_days"] == 30
    assert post_payload["serving_notice"] is True
    assert post_payload["current_ctc_lpa"] == 28.0
    assert post_payload["expected_ctc_lpa"] == 42.0
    assert post_payload["work_mode"] == "hybrid"

    get_resp = client.get("/api/jobs/preferences")
    assert get_resp.status_code == 200
    get_payload = get_resp.json()
    assert get_payload["target_role"] == "Lead Backend Engineer"
    assert get_payload["target_companies"] == ["Razorpay", "Postman", "CRED", "Swiggy"]
    assert get_payload["serving_notice"] is True
    assert get_payload["current_ctc_lpa"] == 28.0
    assert get_payload["expected_ctc_lpa"] == 42.0

