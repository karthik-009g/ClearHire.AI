"""Optional JWT auth helpers and dependency."""

from __future__ import annotations

import threading
import time
from datetime import datetime, timedelta

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from jose import JWTError, jwt
from passlib.context import CryptContext
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.utils.config import settings

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")
security = HTTPBearer(auto_error=False)

_USER_CACHE_LOCK = threading.Lock()
_USER_CACHE: dict[str, tuple[User, float]] = {}
_USER_CACHE_TTL = 120.0  # 120 seconds TTL


def invalidate_user_cache(user_id: str | None = None) -> None:
    """Thread-safe cache invalidation for authenticated users."""
    with _USER_CACHE_LOCK:
        if user_id is None:
            _USER_CACHE.clear()
        else:
            _USER_CACHE.pop(user_id, None)


def get_cached_user(user_id: str) -> User | None:
    """Thread-safe retrieval of cached user if TTL is valid."""
    now = time.time()
    with _USER_CACHE_LOCK:
        entry = _USER_CACHE.get(user_id)
        if entry is not None:
            user, expires_at = entry
            if now < expires_at:
                return user
            _USER_CACHE.pop(user_id, None)
    return None


def set_cached_user(user_id: str, user: User, ttl: float = _USER_CACHE_TTL) -> None:
    """Thread-safe caching of user object."""
    now = time.time()
    with _USER_CACHE_LOCK:
        _USER_CACHE[user_id] = (user, now + ttl)


def hash_password(password: str) -> str:
    return pwd_context.hash(password)


def verify_password(password: str, password_hash: str) -> bool:
    return pwd_context.verify(password, password_hash)


def create_access_token(user_id: str) -> str:
    expire = datetime.utcnow() + timedelta(hours=settings.jwt_expiration_hours)
    payload = {"sub": user_id, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=settings.jwt_algorithm)


def get_current_user_optional(
    credentials: HTTPAuthorizationCredentials | None = Depends(security),
    db: Session = Depends(get_db),
) -> User | None:
    if not settings.auth_enabled:
        return None

    if credentials is None:
        return None

    token = credentials.credentials
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[settings.jwt_algorithm])
        user_id = payload.get("sub")
        if not user_id:
            raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token")
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    cached = get_cached_user(user_id)
    if cached is not None:
        try:
            return db.merge(cached, load=False)
        except Exception:
            return cached

    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="User not found")

    set_cached_user(user_id, user)
    return user


def get_current_user(
    user: User | None = Depends(get_current_user_optional),
) -> User:
    if not settings.auth_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Authentication is disabled")
    if user is None:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")
    return user
