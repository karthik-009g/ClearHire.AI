from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import public_api
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
    app.include_router(public_api.router, prefix="/api/public")
    return TestClient(app)


def test_api_key_create_list_and_revoke():
    client = _build_client()
    res = client.post("/api/public/keys", json={"name": "integration", "scopes": ["read", "workflow"]})
    assert res.status_code == 200
    body = res.json()
    assert body["plain_text_key"].startswith("ch_")
    assert len(body["plain_text_key"]) > 20

    list_res = client.get("/api/public/keys")
    assert list_res.status_code == 200
    assert list_res.json()[0]["name"] == "integration"

    revoke_res = client.post(f"/api/public/keys/{body['api_key_id']}/revoke")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["revoked"] is True
