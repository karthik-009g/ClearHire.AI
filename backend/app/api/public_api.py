"""Minimal public API foundation with API-key auth and scoped access."""

from __future__ import annotations

from hashlib import sha256

import secrets

from fastapi import APIRouter, Depends, HTTPException, Header
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.database import get_db
from app.models import User
from app.models.api_key import APIKey
from app.utils.auth import get_current_user_optional

router = APIRouter()


class APIKeyCreateRequest(BaseModel):
    name: str
    scopes: list[str] | None = None


class APIKeyResponse(BaseModel):
    api_key_id: int
    name: str
    scopes: list[str]
    revoked: bool
    plain_text_key: str | None = None


def _hash_key(value: str) -> str:
    return sha256(value.encode("utf-8")).hexdigest()


def _require_valid_api_key(
    x_api_key: str | None = Header(default=None, alias="X-API-Key"),
    db: Session = Depends(get_db),
):
    if not x_api_key:
        raise HTTPException(status_code=401, detail="Missing API key")
    key_hash = _hash_key(x_api_key)
    record = db.query(APIKey).filter(APIKey.key_hash == key_hash).first()
    if not record or record.revoked:
        raise HTTPException(status_code=401, detail="Invalid or revoked API key")
    return record


@router.post("/keys", response_model=APIKeyResponse)
def create_api_key(
    request: APIKeyCreateRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    raw_key = f"ch_{secrets.token_urlsafe(32)}"
    record = APIKey(
        user_id=current_user.id if current_user else None,
        name=request.name,
        key_hash=_hash_key(raw_key),
        scopes=",".join(request.scopes or ["read"]),
    )
    db.add(record)
    db.commit()
    db.refresh(record)
    return APIKeyResponse(
        api_key_id=record.id,
        name=record.name,
        scopes=(record.scopes or "read").split(","),
        revoked=record.revoked,
        plain_text_key=raw_key,
    )


@router.get("/keys", response_model=list[APIKeyResponse])
def list_api_keys(
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    query = db.query(APIKey)
    if current_user:
        query = query.filter((APIKey.user_id == current_user.id) | (APIKey.user_id.is_(None)))
    rows = query.order_by(APIKey.created_at.desc()).all()
    return [
        APIKeyResponse(
            api_key_id=row.id,
            name=row.name,
            scopes=(row.scopes or "read").split(","),
            revoked=row.revoked,
        )
        for row in rows
    ]


@router.post("/keys/{api_key_id}/revoke")
def revoke_api_key(
    api_key_id: int,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    record = db.query(APIKey).filter(APIKey.id == api_key_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="API key not found")
    if current_user and record.user_id and record.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="Not authorized to revoke this key")
    record.revoked = True
    db.commit()
    return {"api_key_id": record.id, "revoked": True}


@router.get("/whoami")
def api_whoami(api_key: APIKey = Depends(_require_valid_api_key)):
    if "read" not in (api_key.scopes or "").split(","):
        raise HTTPException(status_code=403, detail="Missing read scope")
    return {"key_id": api_key.key_id, "scopes": api_key.scopes.split(",") if api_key.scopes else ["read"]}
