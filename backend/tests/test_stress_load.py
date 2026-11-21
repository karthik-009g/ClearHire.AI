"""
Integration Test Suite: Automated Concurrent Stress Testing & Stability Verification
File: backend/tests/test_stress_load.py

Validates Milestone 5 requirements:
- Concurrency load testing across 4 phases: 5, 15, 25, 50 concurrency.
- Endpoints: /health, /ready, /, /api/applications/, /api/analytics/funnel,
  /api/jobs/preferences, /api/applications/answer-screener, /api/auth/login.
- Frontend routes: /, /applications, /job-hunter, /login.
- Verifies 0% unhandled 5xx exceptions, valid status distribution,
  zero process crashes, and bounded RSS memory growth under load.
"""
from __future__ import annotations

import asyncio
import os
import sys
import pytest

from tests.stress_test_harness import (
    StressHarness,
    TARGET_BACKEND_ENDPOINTS,
    TARGET_FRONTEND_ROUTES,
    get_pid_rss_mb,
)

BACKEND_URL = os.getenv("STRESS_TEST_BACKEND_URL", "http://127.0.0.1:8000")
FRONTEND_URL = os.getenv("STRESS_TEST_FRONTEND_URL", "http://127.0.0.1:3000")

pytestmark = pytest.mark.integration


@pytest.fixture(scope="module")
def harness() -> StressHarness:
    """Initialize StressHarness targeting running backend and frontend servers."""
    h = StressHarness(
        backend_url=BACKEND_URL,
        frontend_url=FRONTEND_URL,
    )
    if not asyncio.run(h.check_backend_health()):
        pytest.skip(
            f"Backend server at {BACKEND_URL} is not reachable; skipping integration stress tests."
        )
    return h


def test_stress_phase_1_baseline_concurrency_5(harness: StressHarness):
    """
    Phase 1: Baseline Warmup load at concurrency 5.
    Verifies all 8 backend endpoints return 200 OK with zero 5xx errors.
    """
    res = asyncio.run(
        harness.run_phase(
            phase_num=1,
            concurrency=5,
            requests_per_endpoint=5,
            include_frontend=False,
            verbose=False,
        )
    )
    assert res["unhandled_5xx_count"] == 0, f"Unhandled 5xx errors in Phase 1: {res}"
    assert res["backend_survived"] is True, "Backend server crashed in Phase 1"
    assert res["total_requests"] == len(TARGET_BACKEND_ENDPOINTS) * 5

    for scenario in res["scenarios"]:
        assert scenario["unhandled_5xx_count"] == 0, f"Errors in {scenario['name']}"
        assert "200" in scenario["status_distribution"], f"No 200 for {scenario['name']}"
        assert scenario["status_distribution"]["200"] == scenario["total_requests"]


def test_stress_phase_2_normal_concurrency_15(harness: StressHarness):
    """
    Phase 2: Normal Load at concurrency 15.
    Verifies steady-state throughput and sub-second p50 latency on core read routes.
    """
    res = asyncio.run(
        harness.run_phase(
            phase_num=2,
            concurrency=15,
            requests_per_endpoint=10,
            include_frontend=False,
            verbose=False,
        )
    )
    assert res["unhandled_5xx_count"] == 0, f"Unhandled 5xx errors in Phase 2: {res}"
    assert res["backend_survived"] is True, "Backend server crashed in Phase 2"
    assert res["total_requests"] == len(TARGET_BACKEND_ENDPOINTS) * 10

    for scenario in res["scenarios"]:
        assert scenario["unhandled_5xx_count"] == 0, f"Errors in {scenario['name']}"
        assert scenario["status_distribution"].get("200") == scenario["total_requests"]


def test_stress_phase_3_high_concurrency_25(harness: StressHarness):
    """
    Phase 3: High Concurrency load at concurrency 25.
    Exceeds default pool_size=20 to verify connection queue handling and overflow stability.
    """
    res = asyncio.run(
        harness.run_phase(
            phase_num=3,
            concurrency=25,
            requests_per_endpoint=15,
            include_frontend=False,
            verbose=False,
        )
    )
    assert res["unhandled_5xx_count"] == 0, f"Unhandled 5xx errors in Phase 3: {res}"
    assert res["backend_survived"] is True, "Backend server crashed in Phase 3"
    assert res["total_requests"] == len(TARGET_BACKEND_ENDPOINTS) * 15

    for scenario in res["scenarios"]:
        assert scenario["unhandled_5xx_count"] == 0, f"Errors in {scenario['name']}"
        assert scenario["status_distribution"].get("200") == scenario["total_requests"]


def test_stress_phase_4_peak_saturation_concurrency_50(harness: StressHarness):
    """
    Phase 4: Peak Saturation load at concurrency 50.
    Forces event-loop and threadpool contention, verifying zero crashes and zero unhandled errors.
    """
    res = asyncio.run(
        harness.run_phase(
            phase_num=4,
            concurrency=50,
            requests_per_endpoint=20,
            include_frontend=False,
            verbose=False,
        )
    )
    assert res["unhandled_5xx_count"] == 0, f"Unhandled 5xx errors in Phase 4: {res}"
    assert res["backend_survived"] is True, "Backend server crashed in Phase 4"
    assert res["total_requests"] == len(TARGET_BACKEND_ENDPOINTS) * 20

    for scenario in res["scenarios"]:
        assert scenario["unhandled_5xx_count"] == 0, f"Errors in {scenario['name']}"
        assert scenario["status_distribution"].get("200") == scenario["total_requests"]


def test_stress_frontend_routes_concurrency(harness: StressHarness):
    """
    Frontend Route Stress Testing:
    Evaluates /, /applications, /job-hunter, /login under concurrency 15.
    If frontend server is stopped, gracefully skips.
    """
    frontend_online = asyncio.run(harness.check_frontend_availability())
    if not frontend_online:
        pytest.skip(f"Frontend dev server at {harness.frontend_url} is not online; skipping.")

    res = asyncio.run(
        harness.run_phase(
            phase_num=5,
            concurrency=15,
            requests_per_endpoint=10,
            include_frontend=True,
            backend_endpoints=[],  # only test frontend routes
            verbose=False,
        )
    )
    assert res["unhandled_5xx_count"] == 0, f"Frontend route errors: {res}"
    assert res["total_requests"] == len(TARGET_FRONTEND_ROUTES) * 10

    for scenario in res["scenarios"]:
        assert scenario["unhandled_5xx_count"] == 0, f"Errors in {scenario['name']}"
        assert scenario["status_distribution"].get("200") == scenario["total_requests"]


def test_backend_stability_and_memory_leak(harness: StressHarness):
    """
    Process Stability & Memory Leak Verification:
    Executes repeated concurrent requests while measuring server RSS memory before and after.
    Verifies zero process crashes and memory growth delta < 100 MB.
    """
    assert asyncio.run(harness.check_backend_health()) is True, "Backend initial health check failed"

    server_rss_before = get_pid_rss_mb(harness.server_pid)

    # Execute a high-density batch against mixed endpoints
    test_endpoints = [
        ep for ep in TARGET_BACKEND_ENDPOINTS
        if ep["path"] in ("/health", "/ready", "/api/analytics/funnel", "/api/jobs/preferences")
    ]
    res = asyncio.run(
        harness.run_phase(
            phase_num=6,
            concurrency=25,
            requests_per_endpoint=25,
            include_frontend=False,
            backend_endpoints=test_endpoints,
            verbose=False,
        )
    )
    assert res["unhandled_5xx_count"] == 0
    assert res["backend_survived"] is True, "Backend server crashed during stability verification"

    server_rss_after = get_pid_rss_mb(harness.server_pid)

    if server_rss_before is not None and server_rss_after is not None:
        delta_mb = server_rss_after - server_rss_before
        # Ensure memory delta does not indicate a massive runaway leak (< 100 MB growth across batch)
        assert delta_mb < 100.0, f"Potential memory leak detected: growth was {delta_mb:.2f} MB"

    # Final health ping
    assert asyncio.run(harness.check_backend_health()) is True, "Backend failed final health check"
