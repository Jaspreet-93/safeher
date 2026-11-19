import pytest

from app.integrations.mock.email import MockEmailProvider
from app.integrations.mock.push import MockPushProvider
from app.integrations.mock.sms import MockSmsProvider
from app.integrations.sms.dlt_provider import DLTSmsProvider


def test_dlt_indian_phone_validation():
    provider = DLTSmsProvider()

    # Valid 10-digit formats
    assert provider.validate_indian_phone("9876543210") == "9876543210"
    assert provider.validate_indian_phone("+919876543210") == "9876543210"
    assert provider.validate_indian_phone("+91-98765-43210") == "9876543210"
    assert provider.validate_indian_phone("918888888888") == "8888888888"
    assert provider.validate_indian_phone("7123456789") == "7123456789"
    assert provider.validate_indian_phone("6123456789") == "6123456789"

    # Invalid numbers
    with pytest.raises(ValueError, match="Invalid Indian mobile number"):
        provider.validate_indian_phone("1234567890")  # starts with 1

    with pytest.raises(ValueError, match="Invalid Indian mobile number"):
        provider.validate_indian_phone("98765")  # too short

    with pytest.raises(ValueError, match="Invalid Indian mobile number"):
        provider.validate_indian_phone("+14155552671")  # US number


@pytest.mark.asyncio
async def test_mock_sms_provider_dispatch():
    sms = MockSmsProvider()
    sms.reset()

    res = await sms.send_sms(to_phone="+919876543210", message="Test alert")
    assert res.success is True
    assert res.provider == "MOCK_SMS_PROVIDER"
    assert res.status == "delivered"
    assert res.message_id.startswith("mock-sms-")
    assert len(sms.sent_messages) == 1


@pytest.mark.asyncio
async def test_mock_sms_fault_injection():
    sms = MockSmsProvider()
    sms.reset()
    sms.simulate_failure = True

    res = await sms.send_sms(to_phone="+919876543210", message="Test alert")
    assert res.success is False
    assert res.status == "failed"
    assert "Simulated Telecom Gateway Outage" in (res.error_message or "")


@pytest.mark.asyncio
async def test_mock_push_provider():
    push = MockPushProvider()
    push.reset()

    res = await push.send_push(
        subscription_info={"endpoint": "https://fcm.googleapis.com/fcm/send/123"},
        title="SOS Alert",
        body="Emergency alert triggered",
    )
    assert res.success is True
    assert res.provider == "MOCK_PUSH_PROVIDER"
    assert res.status == "sent"
    assert len(push.sent_pushes) == 1


@pytest.mark.asyncio
async def test_mock_email_provider():
    email = MockEmailProvider()
    email.reset()

    res = await email.send_email(
        to_email="contact@example.com",
        subject="SafeHer SOS Alert",
        html_body="<p>Emergency alert</p>",
        text_body="Emergency alert",
    )
    assert res.success is True
    assert res.provider == "MOCK_EMAIL_PROVIDER"
    assert res.message_id.startswith("mock-email-")
    assert len(email.sent_emails) == 1
