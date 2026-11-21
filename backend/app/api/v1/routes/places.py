import uuid
from typing import Annotated, Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.errors import NotFoundException
from app.core.security import get_current_user
from app.models.user import User
from app.schemas.place import (
    SafePlaceListResponse,
    SafePlaceResponse,
    SafePlaceReviewCreate,
    SafePlaceReviewResponse,
)
from app.services.place_service import PlaceService

router = APIRouter(prefix="/places", tags=["safe-places"])


@router.get("/nearby", response_model=SafePlaceListResponse)
async def get_nearby_places(
    latitude: Annotated[float, Query(ge=-90.0, le=90.0, description="User's current WGS84 latitude")],
    longitude: Annotated[float, Query(ge=-180.0, le=180.0, description="User's current WGS84 longitude")],
    radius_km: Annotated[float, Query(ge=0.1, le=50.0, description="Search radius in km")] = 5.0,
    category: Annotated[str | None, Query(description="Filter by category")] = None,
    limit: Annotated[int, Query(ge=1, le=100)] = 20,
    verified_only: Annotated[bool, Query()] = False,
    db: AsyncSession = Depends(get_db),
) -> SafePlaceListResponse:
    """
    Returns safe places (police, hospitals, shelters, etc.) nearest to the user's coordinates.
    No authentication required — this endpoint is intentionally public so users can access
    safe place info even before logging in or in distress without their account accessible.
    """
    places = await PlaceService.find_nearby_places(
        db=db,
        latitude=latitude,
        longitude=longitude,
        radius_km=radius_km,
        category=category,
        limit=limit,
        verified_only=verified_only,
    )

    place_responses = [SafePlaceResponse(**p) for p in places]

    return SafePlaceListResponse(
        places=place_responses,
        total=len(place_responses),
        radius_km=radius_km,
        user_latitude=latitude,
        user_longitude=longitude,
    )


@router.get("/{place_id}", response_model=SafePlaceResponse)
async def get_place_detail(
    place_id: uuid.UUID,
    db: AsyncSession = Depends(get_db),
) -> SafePlaceResponse:
    """
    Returns detailed metadata for a specific SafePlace.
    Public endpoint — no authentication required.
    """
    place = await PlaceService.get_place_by_id(db, place_id)
    if not place:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Safe place with ID {place_id} not found.",
        )
    return SafePlaceResponse(
        id=place.id,
        name=place.name,
        category=place.category,
        description=place.description,
        latitude=place.latitude,
        longitude=place.longitude,
        address=place.address,
        city=place.city,
        state=place.state,
        pincode=place.pincode,
        phone_number=place.phone_number,
        is_24_7=place.is_24_7,
        operating_hours=place.operating_hours,
        is_verified=place.is_verified,
        verified_by=place.verified_by,
        safety_score=place.safety_score,
        review_count=place.review_count,
        created_at=place.created_at,
    )


@router.post("/{place_id}/reviews", response_model=SafePlaceReviewResponse, status_code=status.HTTP_201_CREATED)
async def submit_review(
    place_id: uuid.UUID,
    req: SafePlaceReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> SafePlaceReviewResponse:
    """
    Submits a community safety review for a SafePlace.
    Requires authentication. Anonymises attribution; user_id stored internally only.
    """
    try:
        review = await PlaceService.add_review(
            db=db,
            place_id=place_id,
            user_id=current_user.id,
            req=req,
        )
    except NotFoundException as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc)) from exc

    return SafePlaceReviewResponse(
        id=review.id,
        place_id=review.place_id,
        overall_rating=review.overall_rating,
        lighting_rating=review.lighting_rating,
        accessibility_rating=review.accessibility_rating,
        staff_helpfulness=review.staff_helpfulness,
        comment=review.comment,
        created_at=review.created_at,
    )


@router.post("/seed", status_code=status.HTTP_200_OK, include_in_schema=False)
async def seed_safe_places(
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Admin utility: Seed verified safe places dataset.
    Hidden from API schema docs. Idempotent — safe to call multiple times.
    """
    count = await PlaceService.seed_places(db)
    return {"seeded": count, "message": "Safe places dataset seeded successfully."}
