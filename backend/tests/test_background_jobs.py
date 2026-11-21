from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import background_jobs
from app.database import Base, get_db


def _build_client():
    engine = create_engine("sqlite://", connect_args={"check_same_thread": False}, poolclass=StaticPool)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.create_all(bind=engine)

    app = FastAPI()

    def override_get_db():
        db = SessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    app.include_router(background_jobs.router, prefix="/api/jobs")
    return TestClient(app)


def test_enqueue_and_status_round_trip():
    client = _build_client()
    response = client.post("/api/jobs/enqueue", json={"name": "resume_cleanup", "payload": {"resume_id": "r1"}})
    assert response.status_code == 200
    job_id = response.json()["job_id"]

    status = client.get(f"/api/jobs/{job_id}")
    assert status.status_code == 200
    assert status.json()["status"] in {"queued", "running", "completed", "failed"}
    assert status.json()["job_id"] == job_id
