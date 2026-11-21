from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import applications
from app.database import Base, get_db
from app.models.jobs import UserPreference
from app.services.screener_answer_service import ScreenerAnswerService
from app.utils.config import settings


def test_screener_service_intent_detection():
    service = ScreenerAnswerService()

    assert service._detect_intent("What is your current notice period and when can you join?") == "notice_period"
    assert service._detect_intent("What is your expected salary/CTC for this position?") == "compensation"
    assert service._detect_intent("Are you willing to work from our Bangalore office in a hybrid model?") == "work_mode_location"
    assert service._detect_intent("Why do you want to join Razorpay?") == "motivation"
    assert service._detect_intent("Are you legally authorized to work in India?") == "work_authorization"
    assert service._detect_intent("Describe a complex architecture challenge involving microservices.") == "technical_experience"


def test_screener_service_notice_period_answer():
    service = ScreenerAnswerService()

    pref = UserPreference(
        preferred_email="candidate@clearhire.ai",
        notice_period_days=30,
        serving_notice=True,
    )

    result = service.answer_question(
        question="What is your notice period?",
        company="Razorpay",
        role="Senior Backend Engineer",
        preferences=pref,
    )

    assert result.detected_intent == "notice_period"
    assert "30 days" in result.answer
    assert "serving" in result.answer.lower()
    assert "Razorpay" in result.answer
    assert result.confidence_score >= 0.90


def test_screener_service_compensation_answer():
    service = ScreenerAnswerService()

    pref = UserPreference(
        preferred_email="candidate@clearhire.ai",
        current_ctc_lpa=25.0,
        expected_ctc_lpa=38.0,
    )

    result = service.answer_question(
        question="What are your compensation expectations (CTC in LPA)?",
        company="Postman",
        role="Staff Engineer",
        preferences=pref,
    )

    assert result.detected_intent == "compensation"
    assert "25" in result.answer
    assert "38" in result.answer
    assert "Postman" in result.answer


def test_screener_service_motivation_answer():
    service = ScreenerAnswerService()

    parsed = {"skills": ["Python", "FastAPI", "PostgreSQL", "Docker", "AWS"]}

    result = service.answer_question(
        question="Why do you want to join our engineering team?",
        company="CRED",
        role="Backend Lead",
        parsed_summary=parsed,
    )

    assert result.detected_intent == "motivation"
    assert "CRED" in result.answer
    assert "Backend Lead" in result.answer
    assert any(s in result.answer for s in ["Python", "FastAPI", "PostgreSQL"])


def test_answer_screener_api_endpoint():
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
    app.include_router(applications.router, prefix="/api/applications", tags=["applications"])

    client = TestClient(app)

    response = client.post(
        "/api/applications/answer-screener",
        json={
            "question": "Why do you want to work at Swiggy?",
            "company": "Swiggy",
            "role": "SDE-2 Backend",
            "max_words": 100,
        },
    )

    assert response.status_code == 200
    data = response.json()
    assert "answer" in data
    assert data["detected_intent"] == "motivation"
    assert "Swiggy" in data["answer"]
    assert len(data["grounded_facts"]) >= 1
