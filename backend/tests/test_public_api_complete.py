from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import public_api
from app.database import Base, get_db
from app.models.api_key import APIKey
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
    app.include_router(public_api.router, prefix="/api/public", tags=["public"])

    client = TestClient(app)
    client.db = session
    return client


def test_whoami_missing_api_key():
    client = _build_test_client()
    res = client.get("/api/public/whoami")
    assert res.status_code == 401
    assert "Missing API key" in res.json()["detail"]


def test_whoami_invalid_api_key():
    client = _build_test_client()
    res = client.get("/api/public/whoami", headers={"X-API-Key": "ch_invalid_fake_token"})
    assert res.status_code == 401
    assert "Invalid or revoked API key" in res.json()["detail"]


def test_create_api_key_and_whoami_roundtrip():
    client = _build_test_client()

    # 1. Create a key with read and write scopes
    create_res = client.post(
        "/api/public/keys",
        json={"name": "Production Metric Reader", "scopes": ["read", "write"]},
    )
    assert create_res.status_code == 200
    created = create_res.json()
    assert created["name"] == "Production Metric Reader"
    assert "read" in created["scopes"]
    assert "write" in created["scopes"]
    assert created["revoked"] is False
    plain_key = created["plain_text_key"]
    assert plain_key.startswith("ch_")

    # 2. Call /whoami with the active API key
    whoami_res = client.get("/api/public/whoami", headers={"X-API-Key": plain_key})
    assert whoami_res.status_code == 200
    whoami_data = whoami_res.json()
    assert whoami_data["key_id"] is not None and len(str(whoami_data["key_id"])) > 0
    assert "read" in whoami_data["scopes"]


def test_whoami_missing_read_scope_returns_403():
    client = _build_test_client()

    # Create a write-only API key
    create_res = client.post(
        "/api/public/keys",
        json={"name": "Write-Only Automation Ingest", "scopes": ["write"]},
    )
    assert create_res.status_code == 200
    plain_key = create_res.json()["plain_text_key"]

    # Calling /whoami requires 'read' scope
    res = client.get("/api/public/whoami", headers={"X-API-Key": plain_key})
    assert res.status_code == 403
    assert "Missing read scope" in res.json()["detail"]


def test_whoami_rejects_revoked_api_key():
    client = _build_test_client()

    create_res = client.post(
        "/api/public/keys",
        json={"name": "Ephemeral Key", "scopes": ["read"]},
    )
    key_id = create_res.json()["api_key_id"]
    plain_key = create_res.json()["plain_text_key"]

    # Works before revocation
    pre_res = client.get("/api/public/whoami", headers={"X-API-Key": plain_key})
    assert pre_res.status_code == 200

    # Revoke key
    revoke_res = client.post(f"/api/public/keys/{key_id}/revoke")
    assert revoke_res.status_code == 200
    assert revoke_res.json()["revoked"] is True

    # Reject after revocation
    post_res = client.get("/api/public/whoami", headers={"X-API-Key": plain_key})
    assert post_res.status_code == 401
    assert "Invalid or revoked API key" in post_res.json()["detail"]


def test_list_api_keys():
    client = _build_test_client()

    client.post("/api/public/keys", json={"name": "Key Alpha", "scopes": ["read"]})
    client.post("/api/public/keys", json={"name": "Key Beta", "scopes": ["read", "write"]})

    res = client.get("/api/public/keys")
    assert res.status_code == 200
    keys = res.json()
    assert len(keys) >= 2
    names = [k["name"] for k in keys]
    assert "Key Alpha" in names
    assert "Key Beta" in names
