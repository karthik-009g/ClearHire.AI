import sys
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from app import main as main_module
from app.main import app


def test_health_and_readiness_endpoints_include_request_id(monkeypatch):
    monkeypatch.setattr(main_module, "is_database_available", lambda: True)
    client = TestClient(app)

    response = client.get("/health", headers={"X-Request-ID": "phase4-health-check"})
    assert response.status_code == 200
    payload = response.json()
    assert payload["status"] == "healthy"
    assert payload["request_id"] == "phase4-health-check"
    assert response.headers["x-request-id"] == "phase4-health-check"

    readiness = client.get("/ready")
    assert readiness.status_code == 200
    readiness_payload = readiness.json()
    assert readiness_payload["status"] == "ready"
    assert "checks" in readiness_payload


def test_readiness_returns_unavailable_when_database_is_down(monkeypatch):
    monkeypatch.setattr(main_module, "is_database_available", lambda: False)
    client = TestClient(app)

    response = client.get("/ready")
    assert response.status_code == 503
    assert response.json()["checks"]["database"] == "unavailable"


def test_invalid_request_id_is_replaced():
    client = TestClient(app)

    response = client.get("/health", headers={"X-Request-ID": "bad id"})
    assert response.status_code == 200
    assert response.headers["x-request-id"] != "bad id"
    assert len(response.headers["x-request-id"]) == 36


def test_metrics_endpoint_uses_prometheus_format():
    client = TestClient(app)
    client.get("/health")

    response = client.get("/metrics")
    assert response.status_code == 200
    assert "text/plain" in response.headers["content-type"]
    assert "clearhire_http_requests_total" in response.text


def test_sqlalchemy_error_handler_returns_controlled_503():
    from sqlalchemy.exc import OperationalError

    @app.get("/test-db-error-route")
    async def failing_db_route():
        raise OperationalError("SELECT 1", {}, Exception("Connection refused"))

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-db-error-route", headers={"X-Request-ID": "test-sql-err-123"})
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "database_unavailable"
    assert "temporarily unavailable" in payload["detail"]
    assert payload["request_id"] == "test-sql-err-123"
    assert response.headers["x-request-id"] == "test-sql-err-123"


def test_timeout_error_handler_returns_controlled_503():
    @app.get("/test-timeout-route")
    async def timeout_route():
        raise TimeoutError("Upstream service timed out")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-timeout-route", headers={"X-Request-ID": "test-timeout-123"})
    assert response.status_code == 503
    payload = response.json()
    assert payload["error"] == "operation_timeout"
    assert "timed out" in payload["detail"]
    assert payload["request_id"] == "test-timeout-123"
    assert response.headers["x-request-id"] == "test-timeout-123"


def test_unhandled_exception_returns_controlled_500():
    @app.get("/test-crash-route")
    async def crash_route():
        raise RuntimeError("Unexpected pipeline failure")

    client = TestClient(app, raise_server_exceptions=False)
    response = client.get("/test-crash-route", headers={"X-Request-ID": "test-crash-123"})
    assert response.status_code == 500
    payload = response.json()
    assert payload["error"] == "internal_server_error"
    assert "internal server error occurred" in payload["detail"]
    assert payload["request_id"] == "test-crash-123"
    assert response.headers["x-request-id"] == "test-crash-123"
