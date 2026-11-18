import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class RegisterRequest(BaseModel):
    email: EmailStr
    password: str = Field(min_length=8, description="Password must be at least 8 characters long")
    full_name: str = Field(min_length=2, max_length=128)
    phone_number: str | None = Field(default=None, max_length=32)
    preferred_language: str = Field(default="en", max_length=16)
    # Mandatory DPDPA Consent
    terms_consent: bool = Field(description="Consent to Terms of Service & Privacy Notice")
    location_consent: bool = Field(default=True, description="Consent to safety location telemetry")


class LoginRequest(BaseModel):
    email: EmailStr
    password: str
    device_name: str | None = "Web Client"


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"
    expires_in_seconds: int
    user_id: uuid.UUID
    email: str
    role: str
    full_name: str


class RefreshTokenRequest(BaseModel):
    refresh_token: str
    device_name: str | None = None


class SessionResponse(BaseModel):
    id: uuid.UUID
    device_name: str | None
    ip_address: str | None
    user_agent: str | None
    is_revoked: bool
    created_at: datetime
    expires_at: datetime
