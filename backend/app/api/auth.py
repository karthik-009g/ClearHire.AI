"""Optional authentication APIs."""

from __future__ import annotations

from datetime import datetime

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.api.schemas.auth import DeleteAccountResponse, LoginRequest, RegisterRequest, TokenResponse, UpdateProfileRequest, UserResponse
from app.database import get_db
from app.models import Application, Resume, User, UserPreference
from app.services.scheduler_service import run_on_login
from app.services.storage import get_storage_provider
from app.utils.auth import create_access_token, get_current_user_optional, hash_password, verify_password
from app.utils.config import settings

router = APIRouter()
storage = get_storage_provider(settings.storage_root)


def _to_user_response(user: User) -> UserResponse:
    return UserResponse(
        id=user.id,
        email=user.email,
        created_at=user.created_at,
        updated_at=user.updated_at,
        full_name=user.full_name,
        headline=user.headline,
        location=user.location,
        phone=user.phone,
        bio=user.bio,
        profile_image_data_url=user.profile_image_data_url,
    )


def _clean_optional_text(value: str | None) -> str | None:
    if value is None:
        return None
    cleaned = value.strip()
    return cleaned or None


def _require_current_user(current_user: User | None) -> User:
    if current_user is None:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auth is disabled")
    return current_user


@router.post("/register", response_model=UserResponse)
def register(request: RegisterRequest, db: Session = Depends(get_db)):
    if not settings.auth_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auth is disabled")

    existing = db.query(User).filter(User.email == request.email.lower()).first()
    if existing:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already exists")

    user = User(email=request.email.lower(), password_hash=hash_password(request.password))
    db.add(user)
    db.commit()
    db.refresh(user)

    return _to_user_response(user)


@router.post("/login", response_model=TokenResponse)
def login(request: LoginRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not settings.auth_enabled:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Auth is disabled")

    user = db.query(User).filter(User.email == request.email.lower()).first()
    if not user or not verify_password(request.password, user.password_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid credentials")

    background_tasks.add_task(run_on_login, user.id)
    token = create_access_token(user.id)
    return TokenResponse(access_token=token)


@router.get("/me", response_model=UserResponse)
def me(current_user: User | None = Depends(get_current_user_optional)):
    user = _require_current_user(current_user)
    return _to_user_response(user)


@router.patch("/me", response_model=UserResponse)
def update_me(
    request: UpdateProfileRequest,
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user = _require_current_user(current_user)
    payload = request.model_dump(exclude_unset=True)

    for field_name in ("full_name", "headline", "location", "phone", "bio"):
        if field_name in payload:
            setattr(user, field_name, _clean_optional_text(payload[field_name]))

    if payload.get("clear_profile_image"):
        user.profile_image_data_url = None
    elif "profile_image_data_url" in payload:
        profile_image_data_url = _clean_optional_text(payload["profile_image_data_url"])
        if profile_image_data_url and (
            not profile_image_data_url.startswith("data:image/")
            or ";base64," not in profile_image_data_url
        ):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="profile_image_data_url must be a valid image data URL",
            )
        user.profile_image_data_url = profile_image_data_url

    user.updated_at = datetime.utcnow()
    db.commit()
    db.refresh(user)
    return _to_user_response(user)


@router.delete("/account", response_model=DeleteAccountResponse)
def delete_account(
    confirm: str = Query(..., description="Set to DELETE to confirm account deletion"),
    db: Session = Depends(get_db),
    current_user: User | None = Depends(get_current_user_optional),
):
    user = _require_current_user(current_user)
    if confirm != "DELETE":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Confirmation value must be DELETE")

    owned_resumes = db.query(Resume).filter(Resume.user_id == user.id).all()
    deleted_files = 0
    for resume in owned_resumes:
        if resume.stored_path and storage.delete_file(resume.stored_path):
            deleted_files += 1
        db.delete(resume)

    db.query(Application).filter(Application.user_id == user.id).delete(synchronize_session=False)
    db.query(UserPreference).filter(UserPreference.user_id == user.id).delete(synchronize_session=False)
    db.delete(user)
    db.commit()

    return DeleteAccountResponse(
        deleted=True,
        deleted_resumes=len(owned_resumes),
        deleted_files=deleted_files,
    )
