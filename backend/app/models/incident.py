import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import GUID

if TYPE_CHECKING:
    from app.models.contact import EmergencyContact
    from app.models.user import User


class EmergencyIncident(Base):
    __tablename__ = "emergency_incidents"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    user_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    # State Machine: created -> active -> (cancelled | resolved | escalated)
    status: Mapped[str] = mapped_column(String(32), default="created", nullable=False)

    # Client-supplied idempotency key to prevent duplicate incidents
    idempotency_key: Mapped[str] = mapped_column(
        String(128), unique=True, index=True, nullable=False
    )

    # Geolocation Telemetry
    latitude: Mapped[float] = mapped_column(Float, nullable=False)
    longitude: Mapped[float] = mapped_column(Float, nullable=False)
    accuracy_meters: Mapped[float | None] = mapped_column(Float, nullable=True)
    location_timestamp: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Timers & Lifecycle
    grace_period_seconds: Mapped[int] = mapped_column(Integer, default=5, nullable=False)
    triggered_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    activated_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    cancelled_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    cancel_reason: Mapped[str | None] = mapped_column(String(255), nullable=True)
    resolution_notes: Mapped[str | None] = mapped_column(Text, nullable=True)
    safe_pin_hash: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User")
    notifications: Mapped[list["EmergencyNotification"]] = relationship(
        "EmergencyNotification", back_populates="incident", cascade="all, delete-orphan"
    )


class EmergencyNotification(Base):
    __tablename__ = "emergency_notifications"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    incident_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("emergency_incidents.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    contact_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("emergency_contacts.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )

    # Channel & State Machine: queued -> sent -> delivered -> (failed | acknowledged)
    channel: Mapped[str] = mapped_column(String(32), default="sms", nullable=False)
    status: Mapped[str] = mapped_column(String(32), default="queued", nullable=False)

    recipient_address: Mapped[str] = mapped_column(String(255), nullable=False)
    message_body: Mapped[str] = mapped_column(Text, nullable=False)

    # Opaque token for contact acknowledgement link (Hashed at rest)
    secure_ack_token: Mapped[str] = mapped_column(
        String(64), unique=True, index=True, nullable=False
    )

    retry_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    failure_reason: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    sent_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    delivered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    acknowledged_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    incident: Mapped["EmergencyIncident"] = relationship(
        "EmergencyIncident", back_populates="notifications"
    )
    contact: Mapped["EmergencyContact"] = relationship(
        "EmergencyContact", back_populates="notifications"
    )
