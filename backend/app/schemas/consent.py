import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class ConsentCreateRequest(BaseModel):
    consent_type: str = Field(
        description="Consent category: terms_and_privacy, location_sharing, telemetry"
    )
    version: str = Field(default="v1.0", description="Privacy Notice version")
    granted: bool = Field(default=True)


class ConsentResponse(BaseModel):
    id: uuid.UUID
    consent_type: str
    version: str
    granted: bool
    ip_address: str | None
    user_agent: str | None
    timestamp: datetime
