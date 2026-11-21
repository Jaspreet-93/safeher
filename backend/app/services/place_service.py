import math
import uuid
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.models.place import SafePlace, SafePlaceReview
from app.schemas.place import SafePlaceReviewCreate

# ---------------------------------------------------------------------------
# Geodesic Distance Utilities
# ---------------------------------------------------------------------------

EARTH_RADIUS_KM = 6371.0


def haversine_distance(lat1: float, lng1: float, lat2: float, lng2: float) -> float:
    """
    Returns the geodesic distance between two WGS84 coordinate pairs in kilometres.
    Uses the Haversine formula with an Earth radius of 6371 km.
    """
    phi1, phi2 = math.radians(lat1), math.radians(lat2)
    d_phi = math.radians(lat2 - lat1)
    d_lambda = math.radians(lng2 - lng1)

    a = (
        math.sin(d_phi / 2) ** 2
        + math.cos(phi1) * math.cos(phi2) * math.sin(d_lambda / 2) ** 2
    )
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
    return EARTH_RADIUS_KM * c


def bounding_box(lat: float, lng: float, radius_km: float) -> tuple[float, float, float, float]:
    """
    Returns approximate lat/lng bounding box for a given radius.
    Used to pre-filter rows before Haversine precision calculation.
    1 degree latitude ≈ 111 km. Longitude degrees depend on latitude.
    """
    delta_lat = radius_km / 111.0
    delta_lng = radius_km / (111.0 * math.cos(math.radians(lat)))
    return (
        lat - delta_lat,
        lat + delta_lat,
        lng - delta_lng,
        lng + delta_lng,
    )


# ---------------------------------------------------------------------------
# Place Service
# ---------------------------------------------------------------------------

class PlaceService:
    @staticmethod
    async def find_nearby_places(
        db: AsyncSession,
        latitude: float,
        longitude: float,
        radius_km: float = 5.0,
        category: str | None = None,
        limit: int = 20,
        verified_only: bool = False,
    ) -> list[dict[str, Any]]:
        """
        Finds safe places within radius_km of the given coordinates.
        Uses bounding box pre-filter followed by exact Haversine distance calculation.
        Compatible with both PostgreSQL and SQLite (dev/test).
        """
        min_lat, max_lat, min_lng, max_lng = bounding_box(latitude, longitude, radius_km)

        query = select(SafePlace).where(
            SafePlace.is_active.is_(True),
            SafePlace.latitude >= min_lat,
            SafePlace.latitude <= max_lat,
            SafePlace.longitude >= min_lng,
            SafePlace.longitude <= max_lng,
        )
        if category:
            query = query.where(SafePlace.category == category)
        if verified_only:
            query = query.where(SafePlace.is_verified.is_(True))

        result = await db.execute(query)
        candidates = list(result.scalars().all())

        # Apply exact Haversine filter and sort by distance
        places_with_distance = []
        for place in candidates:
            dist = haversine_distance(latitude, longitude, place.latitude, place.longitude)
            if dist <= radius_km:
                places_with_distance.append((dist, place))

        places_with_distance.sort(key=lambda x: x[0])

        output = []
        for dist, place in places_with_distance[:limit]:
            output.append({
                "id": place.id,
                "name": place.name,
                "category": place.category,
                "description": place.description,
                "latitude": place.latitude,
                "longitude": place.longitude,
                "address": place.address,
                "city": place.city,
                "state": place.state,
                "pincode": place.pincode,
                "phone_number": place.phone_number,
                "is_24_7": place.is_24_7,
                "operating_hours": place.operating_hours,
                "is_verified": place.is_verified,
                "verified_by": place.verified_by,
                "safety_score": place.safety_score,
                "review_count": place.review_count,
                "distance_km": round(dist, 3),
                "created_at": place.created_at,
            })

        return output

    @staticmethod
    async def get_place_by_id(
        db: AsyncSession,
        place_id: uuid.UUID,
    ) -> SafePlace | None:
        """Fetches a single SafePlace by primary key."""
        result = await db.execute(
            select(SafePlace).where(SafePlace.id == place_id, SafePlace.is_active.is_(True))
        )
        return result.scalar_one_or_none()

    @staticmethod
    async def add_review(
        db: AsyncSession,
        place_id: uuid.UUID,
        user_id: uuid.UUID | None,
        req: SafePlaceReviewCreate,
    ) -> SafePlaceReview:
        """
        Adds a community safety review to a SafePlace and recalculates aggregate score.
        """
        # Load place
        result = await db.execute(
            select(SafePlace).where(SafePlace.id == place_id, SafePlace.is_active.is_(True))
        )
        place = result.scalar_one_or_none()
        if place is None:
            from app.core.errors import NotFoundException
            raise NotFoundException(f"SafePlace {place_id} not found")

        review = SafePlaceReview(
            place_id=place_id,
            user_id=user_id,
            overall_rating=req.overall_rating,
            lighting_rating=req.lighting_rating,
            accessibility_rating=req.accessibility_rating,
            staff_helpfulness=req.staff_helpfulness,
            comment=req.comment,
        )
        db.add(review)

        # Recalculate aggregate safety score
        new_total = (place.safety_score or 0.0) * place.review_count + req.overall_rating
        place.review_count += 1
        place.safety_score = round(new_total / place.review_count, 2)

        await db.commit()
        await db.refresh(review)
        logger.info(
            f"[SAFE PLACE REVIEW] Place {place.name} ({place_id}) | New Score: {place.safety_score} | Reviews: {place.review_count}"
        )
        return review

    @staticmethod
    async def seed_places(db: AsyncSession) -> int:
        """
        Seeds the database with verified emergency facilities across major Indian cities.
        Idempotent: Skips if data already exists.
        """
        existing = await db.execute(select(SafePlace).limit(1))
        if existing.scalar_one_or_none() is not None:
            logger.info("[SEED] Safe places already seeded — skipping.")
            return 0

        seed_data = [
            # Delhi
            {
                "name": "Connaught Place Police Station",
                "category": "police_station",
                "latitude": 28.6315, "longitude": 77.2167,
                "address": "Connaught Place, New Delhi, Delhi 110001",
                "city": "New Delhi", "state": "Delhi",
                "phone_number": "011-23340100", "is_24_7": True,
                "is_verified": True, "verified_by": "Delhi Police",
                "safety_score": 4.2, "review_count": 48,
            },
            {
                "name": "AIIMS Trauma Centre (24x7 Emergency)",
                "category": "hospital_24_7",
                "latitude": 28.5675, "longitude": 77.2100,
                "address": "Sri Aurobindo Marg, Ansari Nagar, New Delhi 110029",
                "city": "New Delhi", "state": "Delhi",
                "phone_number": "011-26588500", "is_24_7": True,
                "is_verified": True, "verified_by": "MoHFW",
                "safety_score": 4.7, "review_count": 112,
            },
            {
                "name": "Delhi Women Helpline & Crisis Centre",
                "category": "women_helpdesk",
                "latitude": 28.6508, "longitude": 77.2311,
                "address": "Kashmere Gate, New Delhi 110006",
                "city": "New Delhi", "state": "Delhi",
                "phone_number": "1091", "is_24_7": True,
                "is_verified": True, "verified_by": "Delhi Commission for Women",
                "safety_score": 4.5, "review_count": 67,
            },
            {
                "name": "Rajiv Chowk Metro Station (CISF)",
                "category": "transit_hub",
                "latitude": 28.6328, "longitude": 77.2197,
                "address": "Rajiv Chowk, Connaught Place, New Delhi 110001",
                "city": "New Delhi", "state": "Delhi",
                "phone_number": "011-23417910", "is_24_7": False,
                "operating_hours": "05:30–23:30 Daily",
                "is_verified": True, "verified_by": "DMRC",
                "safety_score": 4.3, "review_count": 203,
            },
            # Bengaluru
            {
                "name": "Cubbon Park Police Station",
                "category": "police_station",
                "latitude": 12.9793, "longitude": 77.5929,
                "address": "Cubbon Park, Bengaluru, Karnataka 560001",
                "city": "Bengaluru", "state": "Karnataka",
                "phone_number": "080-22942222", "is_24_7": True,
                "is_verified": True, "verified_by": "Karnataka Police",
                "safety_score": 4.1, "review_count": 29,
            },
            {
                "name": "Victoria Hospital Emergency (24x7)",
                "category": "hospital_24_7",
                "latitude": 12.9674, "longitude": 77.5760,
                "address": "Fort, Bengaluru, Karnataka 560002",
                "city": "Bengaluru", "state": "Karnataka",
                "phone_number": "080-26703111", "is_24_7": True,
                "is_verified": True, "verified_by": "BBMP",
                "safety_score": 4.0, "review_count": 87,
            },
            {
                "name": "Sakhi One Stop Centre (Bengaluru)",
                "category": "women_helpdesk",
                "latitude": 12.9752, "longitude": 77.5940,
                "address": "Cunningham Road, Bengaluru, Karnataka 560052",
                "city": "Bengaluru", "state": "Karnataka",
                "phone_number": "181", "is_24_7": True,
                "is_verified": True, "verified_by": "Karnataka WCD Dept",
                "safety_score": 4.6, "review_count": 42,
            },
            # Mumbai
            {
                "name": "Colaba Police Station",
                "category": "police_station",
                "latitude": 18.9218, "longitude": 72.8322,
                "address": "Colaba Causeway, Mumbai, Maharashtra 400005",
                "city": "Mumbai", "state": "Maharashtra",
                "phone_number": "022-22024444", "is_24_7": True,
                "is_verified": True, "verified_by": "Mumbai Police",
                "safety_score": 4.0, "review_count": 55,
            },
            {
                "name": "KEM Hospital Emergency (24x7)",
                "category": "hospital_24_7",
                "latitude": 19.0024, "longitude": 72.8415,
                "address": "Acharya Donde Marg, Parel, Mumbai, Maharashtra 400012",
                "city": "Mumbai", "state": "Maharashtra",
                "phone_number": "022-24107000", "is_24_7": True,
                "is_verified": True, "verified_by": "BMC",
                "safety_score": 4.3, "review_count": 94,
            },
            {
                "name": "CST Railway Station (RPF)",
                "category": "transit_hub",
                "latitude": 18.9398, "longitude": 72.8355,
                "address": "Chhatrapati Shivaji Maharaj Terminus, Mumbai 400001",
                "city": "Mumbai", "state": "Maharashtra",
                "phone_number": "022-23697355", "is_24_7": True,
                "is_verified": True, "verified_by": "RPF / CR Railways",
                "safety_score": 3.9, "review_count": 310,
            },
            # Hyderabad
            {
                "name": "Madhapur Police Station",
                "category": "police_station",
                "latitude": 17.4484, "longitude": 78.3779,
                "address": "Madhapur, Hyderabad, Telangana 500081",
                "city": "Hyderabad", "state": "Telangana",
                "phone_number": "040-23480600", "is_24_7": True,
                "is_verified": True, "verified_by": "Telangana Police",
                "safety_score": 4.2, "review_count": 38,
            },
            {
                "name": "NIMHANS Night Shelter for Women",
                "category": "verified_shelter",
                "latitude": 12.9403, "longitude": 77.5956,
                "address": "Hosur Road, Lakkasandra, Bengaluru 560029",
                "city": "Bengaluru", "state": "Karnataka",
                "phone_number": "080-46110007", "is_24_7": True,
                "is_verified": True, "verified_by": "NIMHANS",
                "safety_score": 4.8, "review_count": 19,
            },
        ]

        count = 0
        for item in seed_data:
            place = SafePlace(**item)
            db.add(place)
            count += 1

        await db.commit()
        logger.info(f"[SEED] Seeded {count} verified safe places.")
        return count
