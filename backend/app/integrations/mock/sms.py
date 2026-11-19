import asyncio
import uuid
from datetime import datetime, timezone
from typing import Any

from app.core.logging import logger
from app.integrations.base import BaseSmsProvider, SmsResult


class MockSmsProvider(BaseSmsProvider):
    """
    Mock SMS Provider for local development, CI, and chaos testing.
    Explicitly labeled [MOCK] as required by Rule 5.
    Provides controllable fault injection levers for chaos verification.
    """

    def __init__(self):
        self.provider_name = "MOCK_SMS_PROVIDER"
        self.sent_messages: list[dict[str, Any]] = []
        self.simulate_failure: bool = False
        self.fail_count: int = 0
        self.simulate_delay_seconds: float = 0.0

    def reset(self) -> None:
        """Resets all mock state and fault injection flags."""
        self.sent_messages.clear()
        self.simulate_failure = False
        self.fail_count = 0
        self.simulate_delay_seconds = 0.0

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        dlt_template_id: str | None = None,
    ) -> SmsResult:
        if self.simulate_delay_seconds > 0:
            await asyncio.sleep(self.simulate_delay_seconds)

        # Fault Injection: Simulated Gateway Failure
        if self.simulate_failure or self.fail_count > 0:
            if self.fail_count > 0:
                self.fail_count -= 1
            logger.warning(
                f"[MOCK SMS FAILURE INJECTED] Failed dispatch to {to_phone}: Simulated Telecom DLT Scrubbing Timeout"
            )
            return SmsResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error_message="Simulated Telecom Gateway Outage / DLT Scrubbing Timeout",
            )

        msg_id = f"mock-sms-{uuid.uuid4()}"
        record = {
            "id": msg_id,
            "to_phone": to_phone,
            "message": message,
            "dlt_template_id": dlt_template_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "status": "delivered",
        }
        self.sent_messages.append(record)

        logger.info(
            f"[MOCK SMS DISPATCHED] ID: {msg_id} | To: {to_phone} | Message: {message[:60]}..."
        )

        return SmsResult(
            success=True,
            provider=self.provider_name,
            message_id=msg_id,
            status="delivered",
            raw_response={"mock_carrier": "Simulated Airtel/Jio", "dlt_approved": True},
        )


mock_sms_provider = MockSmsProvider()
