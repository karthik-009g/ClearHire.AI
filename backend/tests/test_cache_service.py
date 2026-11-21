from __future__ import annotations

from app.services.cache_service import CacheService, InMemoryCacheProvider


def test_cache_hit_miss_and_invalidation():
    cache = CacheService(provider=InMemoryCacheProvider())

    first_key = cache.make_key("parsed_summary", {"content_hash": "abc", "model": "mini", "version": "v1"})
    second_key = cache.make_key("parsed_summary", {"content_hash": "def", "model": "mini", "version": "v1"})

    assert cache.get("parsed_summary", first_key) is None
    cache.set("parsed_summary", first_key, {"skills": ["python"]}, ttl=60)
    assert cache.get("parsed_summary", first_key) == {"skills": ["python"]}
    assert cache.get("parsed_summary", second_key) is None

    cache.delete("parsed_summary", first_key)
    assert cache.get("parsed_summary", first_key) is None


def test_cache_key_changes_with_input_hash():
    cache = CacheService(provider=InMemoryCacheProvider())

    first_key = cache.make_key("embedding", {"content_hash": "hash-1", "model": "mini", "version": "v1"})
    second_key = cache.make_key("embedding", {"content_hash": "hash-2", "model": "mini", "version": "v1"})

    assert first_key != second_key
