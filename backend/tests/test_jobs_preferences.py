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
