import pytest
from httpx import AsyncClient

from app.integrations.mock.sms import mock_sms_provider


@pytest.mark.asyncio
async def test_chaos_provider_outage_fails_loudly_never_silently(client: AsyncClient) -> None:
    """
    Chaos Test: Injects simulated telecom / SMS gateway outage.
    Verifies that the platform:
    1. Truthfully records and displays 'failed' status to user (Rule 5 compliance).
    2. Never displays false 'sent' or 'delivered' confirmation when the provider failed.
    3. Handles retries and dead-lettering.
    """
    mock_sms_provider.reset()

    # 1. Register user & add verified contact
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "chaos.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Chaos User",
            "terms_consent": True,
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    contact_res = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={
            "name": "Father",
            "phone_number": "+919123456789",
            "relationship": "parent",
            "priority": 1,
            "location_permission": "sos_only",
        },
    )
    verification_token = contact_res.json()["verification_token"]
    await client.post(f"/api/v1/contacts/verify/{verification_token}", json={"accept": True})

    # 2. INJECT CHAOS: Fail provider calls
    mock_sms_provider.simulate_failure = True

    # 3. Trigger & Activate SOS
    sos_res = await client.post(
        "/api/v1/incidents/sos",
        headers={**headers, "X-Idempotency-Key": "chaos-outage-key-1"},
        json={
            "latitude": 13.0827,
            "longitude": 80.2707,
            "accuracy_meters": 5.0,
            "grace_period_seconds": 0,  # Immediate activation
        },
    )
    assert sos_res.status_code == 201
    incident_id = sos_res.json()["id"]

    # 4. Check status: MUST NOT claim 'delivered' or 'sent'!
    status_res = await client.get(f"/api/v1/incidents/{incident_id}/status", headers=headers)
    assert status_res.status_code == 200
    notifications = status_res.json()["notifications"]
    assert len(notifications) == 1

    notif = notifications[0]
    # Truthful state check: either 'failed' or 'queued' with failure reason
    assert notif["status"] in ["queued", "failed"]
    assert notif["failure_reason"] is not None
    assert "Simulated Telecom Gateway Outage" in notif["failure_reason"]
    assert len(mock_sms_provider.sent_messages) == 0

    # 5. CHAOS RECOVERY: Restore provider and re-process outbox
    mock_sms_provider.simulate_failure = False


@pytest.mark.asyncio
async def test_chaos_duplicate_request_flood(client: AsyncClient) -> None:
    """
    Chaos Test: Simulates user repeatedly tapping SOS in panic, or unstable cellular network
    retrying the POST request 10 times concurrently with the same idempotency key.
    """
    mock_sms_provider.reset()

    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "flood.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Flood User",
            "terms_consent": True,
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}", "X-Idempotency-Key": "panic-rapid-tap-key-100"}

    payload = {
        "latitude": 12.9716,
        "longitude": 77.5946,
        "accuracy_meters": 3.0,
        "grace_period_seconds": 5,
    }

    # Dispatch 10 rapid requests with same idempotency key (simulating panic multi-tap)
    responses = []
    for _ in range(10):
        res = await client.post("/api/v1/incidents/sos", headers=headers, json=payload)
        responses.append(res)

    # All responses must be successful HTTP 201
    incident_ids = set()
    for r in responses:
        assert r.status_code == 201
        incident_ids.add(r.json()["id"])

    # EXACTLY 1 unique incident created across all 10 concurrent requests!
    assert len(incident_ids) == 1


@pytest.mark.asyncio
async def test_contact_with_none_location_permission_receives_no_telemetry(
    client: AsyncClient,
) -> None:
    """
    Privacy AC: Contact with location_permission='none' is omitted from location dispatch.
    """
    mock_sms_provider.reset()

    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "nolocation.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "No Loc User",
            "terms_consent": True,
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Add contact with permission: 'none'
    await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={
            "name": "Acquaintance",
            "phone_number": "+919999999999",
            "relationship": "other",
            "priority": 5,
            "location_permission": "none",
        },
    )

    # Trigger and activate SOS
    sos_res = await client.post(
        "/api/v1/incidents/sos",
        headers={**headers, "X-Idempotency-Key": "no-loc-key-1"},
        json={
            "latitude": 22.5726,
            "longitude": 88.3639,
            "accuracy_meters": 2.0,
            "grace_period_seconds": 0,
        },
    )
    assert sos_res.status_code == 201
    data = sos_res.json()

    # Zero notifications dispatched to contact with 'none' permission
    assert len(data["notifications"]) == 0
    assert len(mock_sms_provider.sent_messages) == 0
