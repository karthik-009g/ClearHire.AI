from __future__ import annotations

from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.api import auth
from app.database import Base, get_db
from app.utils.config import settings


def _build_auth_client() -> TestClient:
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
    app.include_router(auth.router, prefix="/api/auth", tags=["auth"])
    return TestClient(app)


def test_auth_disabled_returns_400(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", False)
    client = _build_auth_client()

    response = client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert response.status_code == 400


def test_auth_register_login_me_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(auth, "run_on_login", lambda user_id: None)
    client = _build_auth_client()

    register = client.post("/api/auth/register", json={"email": "user@example.com", "password": "password123"})
    assert register.status_code == 200

    login = client.post("/api/auth/login", json={"email": "user@example.com", "password": "password123"})
    assert login.status_code == 200
    token = login.json()["access_token"]

    me = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me.status_code == 200
    assert me.json()["email"] == "user@example.com"

    update = client.patch(
        "/api/auth/me",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "full_name": "Test User",
            "headline": "Backend Engineer",
            "location": "Bengaluru",
            "phone": "+91-9000000000",
            "bio": "Building reliable APIs.",
            "profile_image_data_url": "data:image/png;base64,dGVzdA==",
        },
    )
    assert update.status_code == 200
    profile = update.json()
    assert profile["full_name"] == "Test User"
    assert profile["headline"] == "Backend Engineer"
    assert profile["location"] == "Bengaluru"
    assert profile["phone"] == "+91-9000000000"

    deletion = client.delete(
        "/api/auth/account",
        headers={"Authorization": f"Bearer {token}"},
        params={"confirm": "DELETE"},
    )
    assert deletion.status_code == 200
    assert deletion.json()["deleted"] is True

    me_after_delete = client.get("/api/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert me_after_delete.status_code == 401


def test_auth_password_mismatch_returns_401_and_preserves_hash(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(auth, "run_on_login", lambda user_id: None)
    client = _build_auth_client()

    reg = client.post("/api/auth/register", json={"email": "alice@example.com", "password": "OriginalSecret123!"})
    assert reg.status_code == 200

    # Attacker tries to log in with wrong password
    bad_login = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "WrongAttackerPassword!"})
    assert bad_login.status_code == 401
    assert bad_login.json()["detail"] == "Invalid email or password"

    # Verify original password still works (hash was not overwritten)
    good_login = client.post("/api/auth/login", json={"email": "alice@example.com", "password": "OriginalSecret123!"})
    assert good_login.status_code == 200
    assert "access_token" in good_login.json()


def test_auth_unregistered_user_returns_401_when_auto_provision_disabled(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_auto_provision_users", False)
    client = _build_auth_client()

    login = client.post("/api/auth/login", json={"email": "unknown@example.com", "password": "AnyPassword123!"})
    assert login.status_code == 401
    assert login.json()["detail"] == "Invalid email or password"


def test_auth_auto_provision_when_enabled(monkeypatch):
    monkeypatch.setattr(settings, "auth_enabled", True)
    monkeypatch.setattr(settings, "auth_auto_provision_users", True)
    monkeypatch.setattr(auth, "run_on_login", lambda user_id: None)
    client = _build_auth_client()

    login = client.post("/api/auth/login", json={"email": "newuser@example.com", "password": "AutoPassword123!"})
    assert login.status_code == 200
    assert "access_token" in login.json()

