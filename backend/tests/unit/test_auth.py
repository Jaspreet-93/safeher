import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_register_and_login_flow(client: AsyncClient) -> None:
    # 1. Register a new user
    reg_payload = {
        "email": "priya.sharma@example.com",
        "password": "StrongPassword123!",
        "full_name": "Priya Sharma",
        "phone_number": "+919876543210",
        "terms_consent": True,
        "location_consent": True,
    }
    reg_res = await client.post("/api/v1/auth/register", json=reg_payload)
    assert reg_res.status_code == 201
    reg_data = reg_res.json()
    assert reg_data["email"] == "priya.sharma@example.com"
    assert reg_data["full_name"] == "Priya Sharma"
    assert "access_token" in reg_data
    assert "refresh_token" in reg_data

    # 2. Login with correct credentials
    login_payload = {
        "email": "priya.sharma@example.com",
        "password": "StrongPassword123!",
    }
    login_res = await client.post("/api/v1/auth/login", json=login_payload)
    assert login_res.status_code == 200
    login_data = login_res.json()
    assert login_data["email"] == "priya.sharma@example.com"
    assert "access_token" in login_data


@pytest.mark.asyncio
async def test_register_requires_mandatory_consent(client: AsyncClient) -> None:
    payload = {
        "email": "no.consent@example.com",
        "password": "StrongPassword123!",
        "full_name": "No Consent User",
        "terms_consent": False,
        "location_consent": False,
    }
    res = await client.post("/api/v1/auth/register", json=payload)
    assert res.status_code == 422
    data = res.json()
    assert "Mandatory consent" in data["message"]


@pytest.mark.asyncio
async def test_no_user_enumeration_on_login(client: AsyncClient) -> None:
    # Probing non-existent user returns generic message
    res = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "nonexistent.victim@example.com",
            "password": "AnyPassword123!",
        },
    )
    assert res.status_code == 401
    assert res.json()["message"] == "Invalid email or password"


@pytest.mark.asyncio
async def test_brute_force_lockout_after_10_failed_attempts(client: AsyncClient) -> None:
    # Register user
    await client.post(
        "/api/v1/auth/register",
        json={
            "email": "target.user@example.com",
            "password": "CorrectPassword123!",
            "full_name": "Target User",
            "terms_consent": True,
        },
    )

    # Attempt 9 failed logins
    for _ in range(9):
        res = await client.post(
            "/api/v1/auth/login",
            json={
                "email": "target.user@example.com",
                "password": "WrongPassword!",
            },
        )
        assert res.status_code == 401

    # 10th failed attempt triggers the lockout
    res_10 = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "target.user@example.com",
            "password": "WrongPassword!",
        },
    )
    assert res_10.status_code == 401

    # 11th attempt (even with correct password) must be rejected with HTTP 423 Locked!
    res_11 = await client.post(
        "/api/v1/auth/login",
        json={
            "email": "target.user@example.com",
            "password": "CorrectPassword123!",
        },
    )
    assert res_11.status_code == 423
    assert "Account is temporarily locked" in res_11.json()["message"]


@pytest.mark.asyncio
async def test_refresh_token_rotation_and_reuse_theft_detection(client: AsyncClient) -> None:
    # Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "rotation.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Rotation User",
            "terms_consent": True,
        },
    )
    refresh_token_1 = reg_res.json()["refresh_token"]

    # Rotate refresh token
    rotate_res = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token_1,
            "device_name": "Web Browser",
        },
    )
    assert rotate_res.status_code == 200
    rotate_data = rotate_res.json()
    refresh_token_2 = rotate_data["refresh_token"]
    assert refresh_token_2 != refresh_token_1

    # Attempt to reuse refresh_token_1 (Simulating token theft)
    theft_res = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token_1,
        },
    )
    assert theft_res.status_code == 401
    assert "Token reuse detected" in theft_res.json()["message"]

    # Now refresh_token_2 should also be invalid because all sessions were revoked!
    theft_cascade_res = await client.post(
        "/api/v1/auth/refresh",
        json={
            "refresh_token": refresh_token_2,
        },
    )
    assert theft_cascade_res.status_code == 401


@pytest.mark.asyncio
async def test_user_profile_and_consent_tracking(client: AsyncClient) -> None:
    # Register
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "profile.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Profile User",
            "terms_consent": True,
            "location_consent": True,
        },
    )
    access_token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Get /me
    me_res = await client.get("/api/v1/users/me", headers=auth_headers)
    assert me_res.status_code == 200
    assert me_res.json()["email"] == "profile.user@example.com"
    assert me_res.json()["profile"]["full_name"] == "Profile User"

    # Update profile with emergency notes
    update_res = await client.put(
        "/api/v1/users/me/profile",
        headers=auth_headers,
        json={
            "blood_group": "B+",
            "emergency_notes": "Allergic to penicillin. Carries inhaler.",
            "preferred_language": "hi",
        },
    )
    assert update_res.status_code == 200
    assert update_res.json()["blood_group"] == "B+"
    assert update_res.json()["preferred_language"] == "hi"

    # Check consent history (should have terms_and_privacy and location_sharing)
    consent_res = await client.get("/api/v1/consent/history", headers=auth_headers)
    assert consent_res.status_code == 200
    consents = consent_res.json()
    assert len(consents) >= 2


@pytest.mark.asyncio
async def test_rbac_authorization(client: AsyncClient) -> None:
    # Standard user trying to access admin endpoint
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "regular.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Regular User",
            "terms_consent": True,
        },
    )
    access_token = reg_res.json()["access_token"]
    auth_headers = {"Authorization": f"Bearer {access_token}"}

    # Attempt to access admin route
    admin_res = await client.get("/api/v1/users/admin/overview", headers=auth_headers)
    assert admin_res.status_code == 403
    assert "Access requires one of roles" in admin_res.json()["message"]
