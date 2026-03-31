from __future__ import annotations

import io

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import resumes
from app.database import Base, get_db
from app.utils.config import settings


def _build_client() -> TestClient:
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
    return TestClient(app)


def test_rejects_disguised_docx_payload():
    client = _build_client()
    response = client.post(
        "/api/resumes/upload",
        files={
            "file": (
                "resume.docx",
                io.BytesIO(b"MZ fake executable payload"),
                "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            )
        },
    )
    assert response.status_code == 400
    assert "invalid or unsafe" in response.text.lower()
