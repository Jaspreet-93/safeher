import hashlib
import hmac
import json
import uuid

import pytest
from httpx import AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.integrations.base import BaseEmailProvider, BaseSmsProvider, EmailResult, SmsResult
from app.models.contact import EmergencyContact
from app.models.incident import EmergencyIncident, EmergencyNotification
from app.models.user import User
from app.services.notification_router import NotificationRouter


class FlakySmsProvider(BaseSmsProvider):
    def __init__(self, should_fail: bool = True):
        self.should_fail = should_fail
        self.provider_name = "FLAKY_PROVIDER"

    async def send_sms(
        self, to_phone: str, message: str, dlt_template_id: str | None = None  # noqa: ARG002
    ) -> SmsResult:
        if self.should_fail:
            return SmsResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error_message="Gateway connection timeout",
            )
        return SmsResult(
            success=True,
            provider=self.provider_name,
            message_id="flaky-success-123",
            status="sent",
        )


class FlakyEmailProvider(BaseEmailProvider):
    def __init__(self, should_fail: bool = False):
        self.should_fail = should_fail
        self.provider_name = "FLAKY_EMAIL"

    async def send_email(
        self, to_email: str, subject: str, html_body: str, text_body: str  # noqa: ARG002
    ) -> EmailResult:
        if self.should_fail:
            return EmailResult(
                success=False,
                provider=self.provider_name,
                error_message="SMTP server unreachable",
            )
        return EmailResult(
            success=True,
            provider=self.provider_name,
            message_id="flaky-email-123",
        )


@pytest.mark.asyncio
async def test_notification_router_failover_ladder():
    # Scenario 1: Primary succeeds
    primary_ok = FlakySmsProvider(should_fail=False)
    secondary = FlakySmsProvider(should_fail=True)
    router1 = NotificationRouter(primary_sms=primary_ok, secondary_sms=secondary)

    res1 = await router1.dispatch_alert(
        recipient_phone="9876543210",
        message="SOS Alert",
    )
    assert res1["success"] is True
    assert res1["delivered_via"] == "primary_sms"
    assert res1["message_id"] == "flaky-success-123"

    # Scenario 2: Primary fails, Secondary succeeds
    primary_fail = FlakySmsProvider(should_fail=True)
    secondary_ok = FlakySmsProvider(should_fail=False)
    router2 = NotificationRouter(primary_sms=primary_fail, secondary_sms=secondary_ok)

    res2 = await router2.dispatch_alert(
        recipient_phone="9876543210",
        message="SOS Alert",
    )
    assert res2["success"] is True
    assert res2["delivered_via"] == "secondary_sms_failover"

    # Scenario 3: Primary & Secondary fail, Email fallback succeeds
    email_ok = FlakyEmailProvider(should_fail=False)
    router3 = NotificationRouter(
        primary_sms=primary_fail,
        secondary_sms=secondary,
        email_provider=email_ok,
    )
    res3 = await router3.dispatch_alert(
        recipient_phone="9876543210",
        message="SOS Alert",
        recipient_email="guardian@example.com",
    )
    assert res3["success"] is True
    assert res3["delivered_via"] == "email_fallback"
    assert res3["message_id"] == "flaky-email-123"

    # Scenario 4: All fail
    email_fail = FlakyEmailProvider(should_fail=True)
    router4 = NotificationRouter(
        primary_sms=primary_fail,
        secondary_sms=secondary,
        email_provider=email_fail,
    )
    res4 = await router4.dispatch_alert(
        recipient_phone="9876543210",
        message="SOS Alert",
        recipient_email="guardian@example.com",
    )
    assert res4["success"] is False
    assert res4["status"] == "failed"
    assert len(res4["trail"]) == 3


@pytest.mark.asyncio
async def test_dlr_webhook_hmac_and_status_updates(
    db_session: AsyncSession, client: AsyncClient
):
    # Setup test user, incident, contact, and notification
    user = User(
        email="sos_webhook_user@example.com",
        phone_number="+919876500001",
        hashed_password="test-hash",
        is_active=True,
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    contact = EmergencyContact(
        user_id=user.id,
        name="Guardian",
        phone_number="+919876500002",
        relationship="parent",
        priority=1,
    )
    db_session.add(contact)
    await db_session.commit()
    await db_session.refresh(contact)

    incident = EmergencyIncident(
        user_id=user.id,
        idempotency_key=f"dlr-test-{uuid.uuid4()}",
        latitude=28.6139,
        longitude=77.2090,
        status="active",
    )
    db_session.add(incident)
    await db_session.commit()
    await db_session.refresh(incident)

    provider_msg_id = f"carrier-msg-{uuid.uuid4()}"
    notif = EmergencyNotification(
        incident_id=incident.id,
        contact_id=contact.id,
        channel="sms",
        status="sent",
        recipient_address=contact.phone_number,
        message_body="SOS Alert test",
        secure_ack_token=str(uuid.uuid4()),
        provider_message_id=provider_msg_id,
    )
    db_session.add(notif)
    await db_session.commit()
    await db_session.refresh(notif)

    payload = {
        "message_id": provider_msg_id,
        "status": "delivered",
        "phone_number": contact.phone_number,
    }
    raw_payload = json.dumps(payload).encode("utf-8")

    # 1. Missing HMAC signature -> 401 Unauthorized
    res_no_sig = await client.post(
        "/api/v1/webhooks/sms/dlr",
        content=raw_payload,
        headers={"Content-Type": "application/json"},
    )
    assert res_no_sig.status_code == 401

    # 2. Forged HMAC signature -> 401 Unauthorized
    res_bad_sig = await client.post(
        "/api/v1/webhooks/sms/dlr",
        content=raw_payload,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": "forged_deadbeef_signature",
        },
    )
    assert res_bad_sig.status_code == 401

    # 3. Valid HMAC signature -> 200 OK & Status updated to delivered
    valid_sig = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"),
        raw_payload,
        hashlib.sha256,
    ).hexdigest()

    res_ok = await client.post(
        "/api/v1/webhooks/sms/dlr",
        content=raw_payload,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": valid_sig,
        },
    )
    assert res_ok.status_code == 200
    data = res_ok.json()
    assert data["status"] == "processed"
    assert data["new_status"] == "delivered"

    # Verify DB record updated
    await db_session.refresh(notif)
    assert notif.status == "delivered"
    assert notif.delivered_at is not None

    # 4. Failure DLR payload
    fail_payload = {
        "message_id": provider_msg_id,
        "status": "failed",
        "error_code": "ERR_ABSENT_SUBSCRIBER",
        "error_message": "Subscriber handset switched off",
    }
    fail_raw = json.dumps(fail_payload).encode("utf-8")
    fail_sig = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"),
        fail_raw,
        hashlib.sha256,
    ).hexdigest()

    res_fail = await client.post(
        "/api/v1/webhooks/sms/dlr",
        content=fail_raw,
        headers={
            "Content-Type": "application/json",
            "X-Webhook-Signature": fail_sig,
        },
    )
    assert res_fail.status_code == 200
    await db_session.refresh(notif)
    assert notif.status == "failed"
    assert "Subscriber handset switched off" in (notif.failure_reason or "")
