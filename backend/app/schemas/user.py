import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ProfileResponse(BaseModel):
    id: uuid.UUID
    full_name: str
    avatar_url: str | None = None
    emergency_notes: str | None = None
    blood_group: str | None = None
    preferred_language: str
    created_at: datetime
    updated_at: datetime


class UserProfileUpdate(BaseModel):
    full_name: str | None = Field(default=None, min_length=2, max_length=128)
    avatar_url: str | None = None
    emergency_notes: str | None = None
    blood_group: str | None = None
    preferred_language: str | None = None


class UserResponse(BaseModel):
    id: uuid.UUID
    email: EmailStr
    phone_number: str | None = None
    role: str
    is_active: bool
    is_verified: bool
    created_at: datetime


class UserWithProfileResponse(UserResponse):
    profile: ProfileResponse | None = None
