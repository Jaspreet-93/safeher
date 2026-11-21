"""Integration tests for the Safe Places API: nearby search, category filter, reviews."""
import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.place import SafePlace


async def _seed_test_places(db: AsyncSession) -> list[SafePlace]:
    """Inserts a small test dataset of safe places around Delhi."""
    places = [
        SafePlace(
            name="Test Police Station",
            category="police_station",
            latitude=28.6315,
            longitude=77.2167,
            city="New Delhi",
            state="Delhi",
            phone_number="011-00000001",
            is_24_7=True,
            is_verified=True,
            verified_by="Test Authority",
            safety_score=4.5,
            review_count=10,
        ),
        SafePlace(
            name="Test Hospital",
            category="hospital_24_7",
            latitude=28.6450,
            longitude=77.2250,
            city="New Delhi",
            state="Delhi",
            phone_number="011-00000002",
            is_24_7=True,
            is_verified=True,
            verified_by="Test Health Dept",
            safety_score=4.2,
            review_count=8,
        ),
        SafePlace(
            name="Test Women Helpdesk",
            category="women_helpdesk",
            latitude=28.6200,
            longitude=77.2100,
            city="New Delhi",
            state="Delhi",
            phone_number="1091",
            is_24_7=True,
            is_verified=True,
            safety_score=4.7,
            review_count=15,
        ),
        SafePlace(
            name="Far Away Place",
            category="police_station",
            latitude=19.0760,  # Mumbai — well outside 50km Delhi radius
            longitude=72.8777,
            city="Mumbai",
            state="Maharashtra",
            is_24_7=True,
            is_verified=True,
        ),
    ]
    for p in places:
        db.add(p)
    await db.commit()
    for p in places:
        await db.refresh(p)
    return places


@pytest.mark.asyncio
async def test_nearby_places_returns_only_places_within_radius(
    client: AsyncClient, db_session: AsyncSession
):
    await _seed_test_places(db_session)

    # Query from India Gate, Delhi — expect first 3 places, not Mumbai
    res = await client.get(
        "/api/v1/places/nearby",
        params={"latitude": 28.6129, "longitude": 77.2295, "radius_km": 10.0},
    )
    assert res.status_code == 200
    data = res.json()

    assert data["total"] == 3
    names = {p["name"] for p in data["places"]}
    assert "Far Away Place" not in names
    assert "Test Police Station" in names


@pytest.mark.asyncio
async def test_nearby_places_sorted_by_distance_ascending(
    client: AsyncClient, db_session: AsyncSession
):
    await _seed_test_places(db_session)

    res = await client.get(
        "/api/v1/places/nearby",
        params={"latitude": 28.6129, "longitude": 77.2295, "radius_km": 10.0},
    )
    assert res.status_code == 200
    distances = [p["distance_km"] for p in res.json()["places"]]
    assert distances == sorted(distances), "Places must be sorted nearest-first"


@pytest.mark.asyncio
async def test_category_filter_returns_only_matching_category(
    client: AsyncClient, db_session: AsyncSession
):
    await _seed_test_places(db_session)

    res = await client.get(
        "/api/v1/places/nearby",
        params={
            "latitude": 28.6129,
            "longitude": 77.2295,
            "radius_km": 10.0,
            "category": "police_station",
        },
    )
    assert res.status_code == 200
    data = res.json()
    assert data["total"] == 1
    assert data["places"][0]["category"] == "police_station"


@pytest.mark.asyncio
async def test_verified_only_filter(
    client: AsyncClient, db_session: AsyncSession
):
    # Add an unverified place
    unverified = SafePlace(
        name="Unverified Shop",
        category="pharmacy",
        latitude=28.6300,
        longitude=77.2200,
        city="New Delhi",
        state="Delhi",
        is_24_7=False,
        is_verified=False,
    )
    db_session.add(unverified)
    await db_session.commit()

    res = await client.get(
        "/api/v1/places/nearby",
        params={
            "latitude": 28.6129,
            "longitude": 77.2295,
            "radius_km": 10.0,
            "verified_only": "true",
        },
    )
    assert res.status_code == 200
    for p in res.json()["places"]:
        assert p["is_verified"] is True


@pytest.mark.asyncio
async def test_place_detail_endpoint(
    client: AsyncClient, db_session: AsyncSession
):
    places = await _seed_test_places(db_session)
    target = places[0]

    res = await client.get(f"/api/v1/places/{target.id}")
    assert res.status_code == 200
    data = res.json()
    assert data["id"] == str(target.id)
    assert data["name"] == target.name
    assert data["category"] == target.category


@pytest.mark.asyncio
async def test_place_detail_404_for_nonexistent(client: AsyncClient):
    import uuid

    res = await client.get(f"/api/v1/places/{uuid.uuid4()}")
    assert res.status_code == 404


@pytest.mark.asyncio
async def test_submit_review_requires_authentication(
    client: AsyncClient, db_session: AsyncSession
):
    places = await _seed_test_places(db_session)
    res = await client.post(
        f"/api/v1/places/{places[0].id}/reviews",
        json={"overall_rating": 5, "comment": "Very safe!"},
    )
    assert res.status_code == 401  # Unauthenticated


@pytest.mark.asyncio
async def test_submit_review_authenticated_updates_aggregate_score(
    client: AsyncClient, db_session: AsyncSession
):
    # Register & login a user, then submit a review
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "review_tester@example.com",
            "password": "TestPass123!",
            "full_name": "Review Tester",
            "phone_number": "+919000000001",
            "terms_consent": True,
        },
    )
    assert reg_res.status_code == 201
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    places = await _seed_test_places(db_session)
    target = places[0]
    old_score = target.safety_score or 0.0
    old_count = target.review_count

    res = await client.post(
        f"/api/v1/places/{target.id}/reviews",
        json={
            "overall_rating": 3,
            "lighting_rating": 4,
            "comment": "Decent lighting, helpful staff",
        },
        headers=headers,
    )
    assert res.status_code == 201
    data = res.json()
    assert data["overall_rating"] == 3

    # Verify place's aggregate score was recalculated
    detail_res = await client.get(f"/api/v1/places/{target.id}")
    updated = detail_res.json()
    assert updated["review_count"] == old_count + 1
    expected_new_score = round((old_score * old_count + 3) / (old_count + 1), 2)
    assert abs(updated["safety_score"] - expected_new_score) < 0.01
