from __future__ import annotations

import threading
import time
from typing import Any

from fastapi import HTTPException

from app.utils.config import settings

_RATE_LOCK = threading.Lock()
_RATE_STORE: dict[str, list[float]] = {}


class RateLimiter:
    def __init__(self, redis_url: str | None = None):
        self.redis_url = redis_url or getattr(settings, "redis_url", None)
        self.redis_client = None
        if self.redis_url:
            try:
                import redis
                self.redis_client = redis.Redis.from_url(self.redis_url, decode_responses=False)
                self.redis_client.ping()
            except Exception:
                self.redis_client = None

    def _make_retry_detail(self, limit: int, window_seconds: int, retry_after_seconds: int) -> dict[str, Any]:
        return {
            "error": "rate_limit_exceeded",
            "limit": limit,
            "window_seconds": window_seconds,
            "retry_after_seconds": max(1, retry_after_seconds),
        }

    def check(self, key: str, limit: int, window_seconds: int = 3600) -> None:
        now = time.time()
        if self.redis_client is not None:
            window_key = f"rate_limit:{key}"
            cutoff = now - window_seconds
            self.redis_client.zremrangebyscore(window_key, 0, cutoff)
            count = self.redis_client.zcard(window_key)
            if count >= limit:
                earliest = self.redis_client.zrange(window_key, 0, 0, withscores=True)
                retry_after_seconds = 0
                if earliest:
                    retry_after_seconds = max(0, int(float(earliest[0][1]) + window_seconds - now))
                raise HTTPException(status_code=429, detail=self._make_retry_detail(limit, window_seconds, retry_after_seconds))
            self.redis_client.zadd(window_key, {str(now): now})
            self.redis_client.expire(window_key, window_seconds)
            return

        with _RATE_LOCK:
            entries = _RATE_STORE.get(key, [])
            entries = [t for t in entries if t >= now - window_seconds]
            if len(entries) >= limit:
                earliest = min(entries) if entries else now
                retry_after_seconds = max(0, int(window_seconds - (now - earliest)))
                raise HTTPException(status_code=429, detail=self._make_retry_detail(limit, window_seconds, retry_after_seconds))
            entries.append(now)
            _RATE_STORE[key] = entries


_default_limiter = RateLimiter()


def check_rate_limit(key: str, limit: int, window_seconds: int = 3600) -> None:
    """Raise HTTPException 429 if the key exceeded limit within window_seconds."""
    _default_limiter.check(key=key, limit=limit, window_seconds=window_seconds)
