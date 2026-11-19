import uuid
from datetime import datetime

from pydantic import BaseModel, EmailStr, Field


class ContactCreateRequest(BaseModel):
    name: str = Field(min_length=2, max_length=128)
    phone_number: str = Field(min_length=8, max_length=32, description="E.164 or national format")
    email: EmailStr | None = None
    relationship: str = Field(default="family", max_length=64)
    priority: int = Field(default=1, ge=1, le=10, description="1 is primary emergency responder")
    location_permission: str = Field(
        default="sos_only",
        description="Permission scope: none, sos_only, journeys, always",
    )


class ContactUpdateRequest(BaseModel):
    name: str | None = Field(default=None, min_length=2, max_length=128)
    phone_number: str | None = Field(default=None, min_length=8, max_length=32)
    email: EmailStr | None = None
    relationship: str | None = None
    priority: int | None = Field(default=None, ge=1, le=10)
    location_permission: str | None = None
    is_active: bool | None = None


class ContactResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    name: str
    phone_number: str
    email: str | None = None
    relationship: str
    priority: int
    location_permission: str
    is_verified: bool
    is_active: bool
    created_at: datetime
    verification_token: str | None = None


class ContactConsentRequest(BaseModel):
    accept: bool = Field(description="Consent to act as trusted emergency contact")
