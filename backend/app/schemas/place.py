import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class SafePlaceResponse(BaseModel):
    id: uuid.UUID
    name: str
    category: str
    description: str | None = None
    latitude: float
    longitude: float
    address: str | None = None
    city: str | None = None
    state: str | None = None
    pincode: str | None = None
    phone_number: str | None = None
    is_24_7: bool
    operating_hours: str | None = None
    is_verified: bool
    verified_by: str | None = None
    safety_score: float | None = None
    review_count: int
    distance_km: float | None = None  # Computed at query time
    created_at: datetime

    model_config = {"from_attributes": True}


class SafePlaceListResponse(BaseModel):
    places: list[SafePlaceResponse]
    total: int
    radius_km: float
    user_latitude: float
    user_longitude: float


class NearbySearchQuery(BaseModel):
    latitude: float = Field(ge=-90.0, le=90.0)
    longitude: float = Field(ge=-180.0, le=180.0)
    radius_km: float = Field(default=5.0, ge=0.1, le=50.0)
    category: str | None = None  # Optional category filter
    limit: int = Field(default=20, ge=1, le=100)
    verified_only: bool = False


class SafePlaceReviewCreate(BaseModel):
    overall_rating: int = Field(ge=1, le=5)
    lighting_rating: int | None = Field(default=None, ge=1, le=5)
    accessibility_rating: int | None = Field(default=None, ge=1, le=5)
    staff_helpfulness: int | None = Field(default=None, ge=1, le=5)
    comment: str | None = Field(default=None, max_length=1000)


class SafePlaceReviewResponse(BaseModel):
    id: uuid.UUID
    place_id: uuid.UUID
    overall_rating: int
    lighting_rating: int | None = None
    accessibility_rating: int | None = None
    staff_helpfulness: int | None = None
    comment: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}
