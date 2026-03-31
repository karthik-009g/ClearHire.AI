"""Authentication schemas."""

from __future__ import annotations

from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8)


class LoginRequest(BaseModel):
    email: EmailStr
    password: str


class TokenResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"


class UserResponse(BaseModel):
    id: str
    email: str
    created_at: datetime
    updated_at: datetime
    full_name: str | None = None
    headline: str | None = None
    location: str | None = None
    phone: str | None = None
    bio: str | None = None
    profile_image_data_url: str | None = None


class UpdateProfileRequest(BaseModel):
    full_name: str | None = Field(default=None, max_length=120)
    headline: str | None = Field(default=None, max_length=160)
    location: str | None = Field(default=None, max_length=120)
    phone: str | None = Field(default=None, max_length=40)
    bio: str | None = Field(default=None, max_length=2000)
    profile_image_data_url: str | None = Field(default=None, max_length=2500000)
    clear_profile_image: bool = False


class DeleteAccountResponse(BaseModel):
    deleted: bool
    deleted_resumes: int
    deleted_files: int
