import pytest
from httpx import AsyncClient

from app.integrations.mock.sms import mock_sms_provider


@pytest.mark.asyncio
async def test_sos_lifecycle_and_idempotency(client: AsyncClient) -> None:
    mock_sms_provider.reset()

    # 1. Register user and add a verified contact
    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "sos.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "SOS User",
            "terms_consent": True,
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    contact_res = await client.post(
        "/api/v1/contacts",
        headers=headers,
        json={
            "name": "Sister",
            "phone_number": "+919988776655",
            "relationship": "sibling",
            "priority": 1,
            "location_permission": "sos_only",
        },
    )
    verification_token = contact_res.json()["verification_token"]
    # Verify contact
    await client.post(f"/api/v1/contacts/verify/{verification_token}", json={"accept": True})

    # 2. Trigger SOS with idempotency key
    sos_payload = {
        "latitude": 28.6139,
        "longitude": 77.2090,
        "accuracy_meters": 4.5,
        "grace_period_seconds": 5,
    }
    idempotency_key = "client-unique-sos-key-999"

    sos_res_1 = await client.post(
        "/api/v1/incidents/sos",
        headers={**headers, "X-Idempotency-Key": idempotency_key},
        json=sos_payload,
    )
    assert sos_res_1.status_code == 201
    incident_1 = sos_res_1.json()
    assert incident_1["status"] == "created"
    assert incident_1["latitude"] == 28.6139

    incident_id = incident_1["id"]

    # 3. Duplicate SOS trigger with SAME idempotency key must return exact same incident
    sos_res_2 = await client.post(
        "/api/v1/incidents/sos",
        headers={**headers, "X-Idempotency-Key": idempotency_key},
        json=sos_payload,
    )
    assert sos_res_2.status_code == 201
    assert sos_res_2.json()["id"] == incident_id

    # 4. Activate SOS (simulating grace period expiration)
    act_res = await client.post(f"/api/v1/incidents/{incident_id}/activate", headers=headers)
    assert act_res.status_code == 200
    act_data = act_res.json()
    assert act_data["status"] == "active"
    assert len(act_data["notifications"]) == 1

    notification = act_data["notifications"][0]
    assert notification["status"] in ["sent", "delivered"]
    assert len(mock_sms_provider.sent_messages) == 1

    # Extract secure ack token from provider sent message
    sent_msg = mock_sms_provider.sent_messages[0]["message"]
    assert "SAFEHER SOS ALERT" in sent_msg
    # Extract token from the URL in the message
    ack_token = sent_msg.split("/emergency/ack/")[1].split(" ")[0]

    # 5. Contact opens secure link and acknowledges
    ack_res = await client.post(f"/api/v1/incidents/ack/{ack_token}")
    assert ack_res.status_code == 200
    ack_data = ack_res.json()
    assert ack_data["status"] == "acknowledged"
    assert ack_data["emergency_fallback_number"] == "112"

    # 6. Check incident status reflects acknowledged notification
    status_res = await client.get(f"/api/v1/incidents/{incident_id}/status", headers=headers)
    assert status_res.status_code == 200
    assert status_res.json()["notifications"][0]["status"] == "acknowledged"

    # 7. Resolve incident
    resolve_res = await client.post(
        f"/api/v1/incidents/{incident_id}/resolve",
        headers=headers,
        json={"resolution_notes": "Reached police station safely."},
    )
    assert resolve_res.status_code == 200
    assert resolve_res.json()["status"] == "resolved"


@pytest.mark.asyncio
async def test_sos_cancel_within_grace_window(client: AsyncClient) -> None:
    mock_sms_provider.reset()

    reg_res = await client.post(
        "/api/v1/auth/register",
        json={
            "email": "cancel.user@example.com",
            "password": "StrongPassword123!",
            "full_name": "Cancel User",
            "terms_consent": True,
        },
    )
    token = reg_res.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # Trigger SOS
    sos_res = await client.post(
        "/api/v1/incidents/sos",
        headers={**headers, "X-Idempotency-Key": "cancel-key-123"},
        json={
            "latitude": 19.0760,
            "longitude": 72.8777,
            "accuracy_meters": 10.0,
            "grace_period_seconds": 10,
        },
    )
    incident_id = sos_res.json()["id"]
    assert sos_res.json()["status"] == "created"

    # Cancel within grace window
    cancel_res = await client.post(
        f"/api/v1/incidents/{incident_id}/cancel",
        headers=headers,
        json={"cancel_reason": "Accidental tap while putting phone in purse"},
    )
    assert cancel_res.status_code == 200
    assert cancel_res.json()["status"] == "cancelled"

    # Verify zero SMS messages were dispatched
    assert len(mock_sms_provider.sent_messages) == 0
