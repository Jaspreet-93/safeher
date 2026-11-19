import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SOSTriggerRequest(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0, description="WGS84 latitude")
    longitude: float = Field(ge=-180.0, le=180.0, description="WGS84 longitude")
    accuracy_meters: float | None = Field(
        default=None, ge=0.0, description="GPS horizontal accuracy in meters"
    )
    location_timestamp: datetime | None = None
    grace_period_seconds: int = Field(
        default=5, ge=0, le=30, description="Cancel countdown duration"
    )


class SOSCancelRequest(BaseModel):
    cancel_reason: str | None = Field(default="Accidental trigger", max_length=255)


class SOSResolveRequest(BaseModel):
    safe_pin: str | None = Field(default=None, max_length=16)
    resolution_notes: str | None = Field(default=None, max_length=1000)


class NotificationStatusResponse(BaseModel):
    id: uuid.UUID
    contact_id: uuid.UUID
    contact_name: str
    recipient_address: str
    channel: str
    status: str  # queued, sent, delivered, failed, acknowledged
    sent_at: datetime | None = None
    delivered_at: datetime | None = None
    acknowledged_at: datetime | None = None
    failure_reason: str | None = None


class IncidentDetailResponse(BaseModel):
    id: uuid.UUID
    user_id: uuid.UUID
    status: str  # created, active, cancelled, resolved, escalated
    idempotency_key: str
    latitude: float
    longitude: float
    accuracy_meters: float | None
    grace_period_seconds: int
    triggered_at: datetime
    activated_at: datetime | None = None
    cancelled_at: datetime | None = None
    resolved_at: datetime | None = None
    cancel_reason: str | None = None
    resolution_notes: str | None = None
    notifications: list[NotificationStatusResponse] = []


class ContactAckResponse(BaseModel):
    incident_id: uuid.UUID
    user_name: str
    contact_name: str
    status: str
    latitude: float
    longitude: float
    accuracy_meters: float | None
    triggered_at: datetime
    acknowledged_at: datetime
    emergency_fallback_number: str = "112"
    map_deep_link: str
