"""Cache abstraction with in-memory fallback and Redis-ready implementation."""

from __future__ import annotations

import hashlib
import json
import threading
import time
from abc import ABC, abstractmethod
from typing import Any

import redis


class CacheProvider(ABC):
    @abstractmethod
    def get(self, key: str) -> Any:
        raise NotImplementedError

    @abstractmethod
    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        raise NotImplementedError

    @abstractmethod
    def delete(self, key: str) -> None:
        raise NotImplementedError


class InMemoryCacheProvider(CacheProvider):
    def __init__(self):
        self._store: dict[str, Any] = {}
        self._ttl: dict[str, float] = {}
        self._lock = threading.RLock()

    def get(self, key: str) -> Any:
        with self._lock:
            if key not in self._store:
                return None
            if key in self._ttl and self._ttl[key] < time.time():
                self.delete(key)
                return None
            return self._store[key]

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        with self._lock:
            self._store[key] = value
            if ttl is not None:
                self._ttl[key] = time.time() + ttl
            else:
                self._ttl.pop(key, None)

    def delete(self, key: str) -> None:
        with self._lock:
            self._store.pop(key, None)
            self._ttl.pop(key, None)


_UNSET = object()


class RedisCacheProvider(CacheProvider):
    def __init__(self, redis_url: str):
        self.client = redis.Redis.from_url(redis_url, decode_responses=True, socket_connect_timeout=0.2)
        self.client.ping()

    def get(self, key: str) -> Any:
        try:
            value = self.client.get(key)
            if value is None:
                return None
            return json.loads(value)
        except Exception:
            return None

    def set(self, key: str, value: Any, ttl: int | None = None) -> None:
        try:
            payload = json.dumps(value)
            if ttl is None:
                self.client.set(key, payload)
            else:
                self.client.setex(key, ttl, payload)
        except Exception:
            pass

    def delete(self, key: str) -> None:
        try:
            self.client.delete(key)
        except Exception:
            pass


class CacheService:
    def __init__(self, provider: CacheProvider | None = None):
        self.provider = provider or InMemoryCacheProvider()

    def make_key(self, namespace: str, inputs: dict[str, Any]) -> str:
        payload = json.dumps(inputs, sort_keys=True, separators=(",", ":"), default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return f"{namespace}:{digest}"

    def get(self, namespace_or_key: str, key: str | None = None) -> Any:
        full_key = namespace_or_key if key is None else f"{namespace_or_key}:{key}"
        return self.provider.get(full_key)

    def set(
        self,
        namespace_or_key: str,
        key_or_value: Any,
        value: Any = _UNSET,
        ttl: int | None = None,
    ) -> None:
        if value is _UNSET:
            self.provider.set(namespace_or_key, key_or_value, ttl=ttl)
        else:
            self.provider.set(f"{namespace_or_key}:{key_or_value}", value, ttl=ttl)

    def delete(self, namespace_or_key: str, key: str | None = None) -> None:
        full_key = namespace_or_key if key is None else f"{namespace_or_key}:{key}"
        self.provider.delete(full_key)


_fallback_in_memory_provider = InMemoryCacheProvider()
_singleton_cache_service: CacheService | None = None
_cache_service_lock = threading.Lock()


def get_cache_service() -> CacheService:
    global _singleton_cache_service
    from app.utils.config import settings

    if _singleton_cache_service is not None:
        return _singleton_cache_service

    with _cache_service_lock:
        if _singleton_cache_service is not None:
            return _singleton_cache_service

        if getattr(settings, "redis_url", None):
            try:
                _singleton_cache_service = CacheService(provider=RedisCacheProvider(settings.redis_url))
                return _singleton_cache_service
            except Exception:
                pass

        _singleton_cache_service = CacheService(provider=_fallback_in_memory_provider)
        return _singleton_cache_service
