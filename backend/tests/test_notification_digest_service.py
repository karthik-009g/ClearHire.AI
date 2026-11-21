from __future__ import annotations

from datetime import datetime, timedelta
from types import SimpleNamespace
import pytest
from app.models.jobs import DigestLog, JobPosting, UserPreference
from app.models.resume import Application, JobDescription
from app.services.direct_ats_service import DirectAtsService
from app.services.notification_digest_service import NotificationDigestService


@pytest.fixture(autouse=True)
def prevent_live_ats_requests(monkeypatch):
    monkeypatch.setattr(DirectAtsService, "get_direct_jobs", lambda self, *args, **kwargs: [])


def test_compute_funnel_analytics_zero_apps():
    service = NotificationDigestService()
    metrics = service.compute_funnel_analytics([])
    assert metrics.total_tracked == 0
    assert metrics.screen_conversion_rate == 0.0
    assert metrics.offer_rate == 0.0


def test_compute_funnel_analytics_with_diverse_pipeline():
    service = NotificationDigestService()
    now = datetime.utcnow()

    apps = [
        Application(id=1, status="applied", updated_at=now - timedelta(days=2)),
        Application(id=2, status="screening", updated_at=now - timedelta(days=5)),
        Application(id=3, status="interviewing", updated_at=now - timedelta(days=8)),
        Application(id=4, status="offer", updated_at=now - timedelta(days=12)),
        Application(id=5, status="applied", updated_at=now - timedelta(days=16)),  # Over 14d -> ghosted
        Application(id=6, status="ghosted", updated_at=now - timedelta(days=20)),
        Application(id=7, status="draft", updated_at=now),
    ]

    metrics = service.compute_funnel_analytics(apps)
    assert metrics.total_tracked == 7
    assert metrics.saved == 1
    assert metrics.applied == 6  # 6 made it to applied or beyond
    assert metrics.screening == 3  # screening, interviewing, offer
    assert metrics.interviewing == 2  # interviewing, offer
    assert metrics.offer == 1
    assert metrics.ghosted == 2  # app 5 (16d applied) + app 6 (ghosted)
    assert metrics.screen_conversion_rate == 50.0  # 3/6
    assert metrics.offer_rate == round(1 / 6 * 100, 1)


def test_build_morning_digest_payload(monkeypatch):
    service = NotificationDigestService()
    public_job = SimpleNamespace(
        source="greenhouse_razorpay",
        ats_type="greenhouse",
        title="Senior Backend Engineer",
        company="Razorpay",
        location="Bengaluru, India",
        url="https://boards.greenhouse.io/razorpay/jobs/123",
        salary_range=None,
    )
    monkeypatch.setattr(service.direct_ats, "get_direct_jobs", lambda **kwargs: [public_job])
    pref = UserPreference(
        target_role="Backend Engineer",
        target_companies_csv="Razorpay, Postman",
        preferred_email="arjun@example.com",
    )
    now = datetime.utcnow()
    job = JobDescription(id=10, title="Senior Backend Engineer", company="Razorpay", jd_text="Backend Go APIs")
    jmap = {10: job}

    apps = [
        Application(id=1, job_description_id=10, status="applied", updated_at=now - timedelta(days=16)),
    ]

    digest = service.build_morning_digest(
        candidate_name="Arjun",
        preferences=pref,
        applications=apps,
        jobs_map=jmap,
    )

    assert digest.candidate_name == "Arjun"
    assert digest.target_role == "Backend Engineer"
    assert len(digest.top_jobs) >= 1
    assert all(j.ghosting_risk == "unknown" for j in digest.top_jobs)
    assert len(digest.ghosting_alerts) == 1
    assert digest.ghosting_alerts[0].company == "Razorpay"
    assert digest.ghosting_alerts[0].days_elapsed >= 15

    # Check multi-channel output formatting
    assert "*ClearHire.AI Morning Briefing*" in digest.telegram_text
    assert "Arjun" in digest.telegram_text
    assert "*ClearHire.AI Morning Digest*" in digest.whatsapp_text
    assert "<!DOCTYPE html>" in digest.email_html
    assert "Morning Recruitment Briefing" in digest.email_html


def test_dispatch_digest_simulated_and_logging():
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from sqlalchemy.pool import StaticPool
    from app.database import Base

    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    TestingSession = sessionmaker(bind=engine)
    Base.metadata.create_all(bind=engine)
    db = TestingSession()

    service = NotificationDigestService()
    digest = service.build_morning_digest(candidate_name="Neha")

    results = service.dispatch_digest(
        digest=digest,
        channels=["email", "telegram", "whatsapp"],
        recipient_info={
            "email": "neha@example.com",
            "telegram_chat_id": "@neha_dev",
            "whatsapp_number": "+919876543210",
        },
        user_id="user-neha-123",
        db_session=db,
    )

    assert len(results) == 3
    assert all(r.status in {"sent", "simulated"} for r in results)

    # Verify database persistence in DigestLog
    logs = db.query(DigestLog).all()
    assert len(logs) == 3
    channels_logged = {l.channel for l in logs}
    assert channels_logged == {"email", "telegram", "whatsapp"}
    assert logs[0].metrics_snapshot is not None
