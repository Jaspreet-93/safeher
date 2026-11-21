import uuid
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from sqlalchemy import (
    Boolean,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.core.database import Base
from app.models.user import GUID

if TYPE_CHECKING:
    from app.models.user import User


class SafePlace(Base):
    """
    Verified emergency safe haven / facility.
    Categories: police_station, hospital_24_7, women_helpdesk,
                pharmacy, transit_hub, verified_shelter
    """

    __tablename__ = "safe_places"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )

    # Identity
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    category: Mapped[str] = mapped_column(
        String(64), nullable=False, index=True
    )  # police_station | hospital_24_7 | women_helpdesk | pharmacy | transit_hub | verified_shelter
    description: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Location (WGS84)
    latitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    longitude: Mapped[float] = mapped_column(Float, nullable=False, index=True)
    address: Mapped[str | None] = mapped_column(String(512), nullable=True)
    city: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    state: Mapped[str | None] = mapped_column(String(128), nullable=True)
    pincode: Mapped[str | None] = mapped_column(String(16), nullable=True)

    # Contact & Operations
    phone_number: Mapped[str | None] = mapped_column(String(32), nullable=True)
    is_24_7: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    operating_hours: Mapped[str | None] = mapped_column(
        String(255), nullable=True
    )  # e.g. "Mon–Fri 08:00–20:00"

    # Trust & Verification
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    verified_by: Mapped[str | None] = mapped_column(
        String(128), nullable=True
    )  # e.g. "Delhi Police", "MoHFW"
    safety_score: Mapped[float | None] = mapped_column(
        Float, nullable=True
    )  # Aggregate community score (0.0 – 5.0)
    review_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    reviews: Mapped[list["SafePlaceReview"]] = relationship(
        "SafePlaceReview", back_populates="place", cascade="all, delete-orphan"
    )


class SafePlaceReview(Base):
    """
    Community safety telemetry and trust signal for a SafePlace.
    Anonymous by design — user_id is nullable and stored hashed.
    """

    __tablename__ = "safe_place_reviews"

    id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        primary_key=True,
        default=uuid.uuid4,
    )
    place_id: Mapped[uuid.UUID] = mapped_column(
        GUID,
        ForeignKey("safe_places.id", ondelete="CASCADE"),
        index=True,
        nullable=False,
    )
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        GUID,
        ForeignKey("users.id", ondelete="SET NULL"),
        index=True,
        nullable=True,
    )

    # Ratings (1–5 scale)
    overall_rating: Mapped[int] = mapped_column(Integer, nullable=False)  # 1–5
    lighting_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    accessibility_rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    staff_helpfulness: Mapped[int | None] = mapped_column(Integer, nullable=True)
    comment: Mapped[str | None] = mapped_column(Text, nullable=True)

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False,
    )

    # Relationships
    place: Mapped["SafePlace"] = relationship("SafePlace", back_populates="reviews")
    user: Mapped["User | None"] = relationship("User")
