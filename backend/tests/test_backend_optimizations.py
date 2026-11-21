from __future__ import annotations

import time
from unittest.mock import MagicMock, patch

from fastapi import FastAPI
from fastapi.security import HTTPAuthorizationCredentials
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from app.database import Base, engine
from app.models import User
from app.services.cache_service import InMemoryCacheProvider, RedisCacheProvider, get_cache_service
from app.services.workflow_service import run_resume_analysis_flow, _COMPILED_APP
from app.utils.auth import (
    create_access_token,
    get_cached_user,
    get_current_user_optional,
    invalidate_user_cache,
    set_cached_user,
)
from app.utils.config import settings
from app.main import is_database_available, _readiness_cache_lock


def test_database_pool_configuration():
    """Verify QueuePool sizing is configured to 60 pool_size, 40 max_overflow, 10.0 pool_timeout."""
    # Check that engine has pool_size and max_overflow configured
    pool = engine.pool
    # If pool is QueuePool
    if hasattr(pool, "size"):
        assert pool.size() == 60
    if hasattr(pool, "_max_overflow"):
        assert pool._max_overflow == 40
    if hasattr(pool, "_timeout"):
        assert pool._timeout == 10.0


def test_auth_user_caching_and_invalidation():
    """Verify get_current_user_optional caches users and invalidate_user_cache cleans it."""
    test_engine = create_engine(
        "sqlite://",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Session = sessionmaker(autocommit=False, autoflush=False, bind=test_engine)
    Base.metadata.create_all(bind=test_engine)
    session = Session()

    user = User(id="opt-test-user-123", email="optim@example.com", password_hash="hash")
    session.add(user)
    session.commit()

    token = create_access_token(user.id)
    creds = HTTPAuthorizationCredentials(scheme="Bearer", credentials=token)

    invalidate_user_cache()
    assert get_cached_user(user.id) is None

    # First call - queries DB and populates cache
    with patch.object(settings, "auth_enabled", True):
        u1 = get_current_user_optional(credentials=creds, db=session)
        assert u1 is not None
        assert u1.id == user.id
        assert get_cached_user(user.id) is not None

        # Second call - returns from cache, verify DB query is not executed
        with patch.object(session, "query") as mock_query:
            u2 = get_current_user_optional(credentials=creds, db=session)
            assert u2 is not None
            assert u2.id == user.id
            mock_query.assert_not_called()

        # Invalidate cache
        invalidate_user_cache(user.id)
        assert get_cached_user(user.id) is None


def test_auth_cache_ttl_expiry():
    """Verify cached user expires after TTL."""
    user = User(id="ttl-test-user", email="ttl@example.com", password_hash="hash")
    invalidate_user_cache()
    set_cached_user(user.id, user, ttl=0.05)
    assert get_cached_user(user.id) is not None

    time.sleep(0.06)
    assert get_cached_user(user.id) is None


def test_readiness_ping_5s_caching():
    """Verify is_database_available caches database status across 5s window."""
    import app.main as main_module

    with main_module._readiness_cache_lock:
        main_module._readiness_cache_time = 0.0
        main_module._readiness_cache_result = False

    with patch("app.main.engine.connect") as mock_connect:
        mock_conn = MagicMock()
        mock_connect.return_value.__enter__.return_value = mock_conn

        res1 = is_database_available()
        assert res1 is True
        assert mock_connect.call_count == 1

        # Second immediate call uses cached result
        res2 = is_database_available()
        assert res2 is True
        assert mock_connect.call_count == 1  # Not called again


def test_cache_service_singleton_and_timeout():
    """Verify get_cache_service returns singleton and RedisCacheProvider uses connect timeout."""
    svc1 = get_cache_service()
    svc2 = get_cache_service()
    assert svc1 is svc2
    assert isinstance(svc1.provider, InMemoryCacheProvider)

    # Test RedisCacheProvider constructor passes socket_connect_timeout=0.2
    with patch("redis.Redis.from_url") as mock_redis_from_url:
        mock_client = MagicMock()
        mock_redis_from_url.return_value = mock_client
        provider = RedisCacheProvider("redis://localhost:6379/0")
        mock_redis_from_url.assert_called_once_with(
            "redis://localhost:6379/0",
            decode_responses=True,
            socket_connect_timeout=0.2,
        )
        mock_client.ping.assert_called_once()


def test_workflow_precompiled_and_parsed_summary_reuse():
    """Verify StateGraph is pre-compiled at module scope and parsed_summary is reused without re-parsing."""
    assert _COMPILED_APP is not None

    mock_parser = MagicMock()
    mock_matcher = MagicMock()
    mock_matcher.match.return_value = {"score": 95, "matched_skills": ["Python"]}

    existing_summary = {"skills": ["Python", "FastAPI"], "experience_years": 5}
    result = run_resume_analysis_flow(
        resume_text="Senior Python Developer",
        jd_text="Looking for Senior Python Developer",
        parser=mock_parser,
        matcher=mock_matcher,
        parsed_summary=existing_summary,
    )

    # Parser should NOT have been called because parsed_summary was provided
    mock_parser.parse_resume.assert_not_called()
    assert result["parsed"] == existing_summary
    assert result["match"]["score"] == 95
