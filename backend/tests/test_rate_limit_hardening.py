from __future__ import annotations

import pytest
from fastapi import HTTPException

from app.utils.rate_limit import RateLimiter, _RATE_STORE


def test_in_memory_limit_exceeded_and_reset_window():
    _RATE_STORE.clear()
    limiter = RateLimiter(redis_url=None)

    limiter.check("user:test", 2, window_seconds=60)
    limiter.check("user:test", 2, window_seconds=60)

    with pytest.raises(HTTPException) as exc:
        limiter.check("user:test", 2, window_seconds=60)

    assert exc.value.status_code == 429
    assert exc.value.detail["limit"] == 2
    assert exc.value.detail["error"] == "rate_limit_exceeded"

    _RATE_STORE.clear()
    limiter.check("user:test", 2, window_seconds=60)
    limiter.check("user:test", 2, window_seconds=60)
    assert len(_RATE_STORE["user:test"]) == 2


def test_rate_limiter_thread_safety_under_concurrent_load():
    import concurrent.futures

    _RATE_STORE.clear()
    limiter = RateLimiter(redis_url=None)

    total_threads = 20
    limit = 10

    def worker():
        try:
            limiter.check("user:concurrent", limit=limit, window_seconds=60)
            return True
        except HTTPException:
            return False

    with concurrent.futures.ThreadPoolExecutor(max_workers=total_threads) as executor:
        futures = [executor.submit(worker) for _ in range(total_threads)]
        results = [f.result() for f in futures]

    success_count = sum(1 for r in results if r is True)
    blocked_count = sum(1 for r in results if r is False)

    assert success_count == limit
    assert blocked_count == total_threads - limit
    assert len(_RATE_STORE["user:concurrent"]) == limit
