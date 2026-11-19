import uuid
from typing import Any

from app.core.logging import logger
from app.integrations.base import BasePushProvider, PushResult


class MockPushProvider(BasePushProvider):
    """
    Mock Web Push & Device Push Provider.
    Honest [MOCK] labeling per Rule 5.
    """

    def __init__(self):
        self.provider_name = "MOCK_PUSH_PROVIDER"
        self.sent_pushes: list[dict[str, Any]] = []
        self.simulate_failure: bool = False

    def reset(self) -> None:
        self.sent_pushes.clear()
        self.simulate_failure = False

    async def send_push(
        self,
        subscription_info: dict[str, Any],
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> PushResult:
        if self.simulate_failure:
            logger.warning("[MOCK PUSH FAILURE INJECTED] Push dispatch simulated failure")
            return PushResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error_message="Simulated push endpoint expired or unreachable",
            )

        msg_id = f"mock-push-{uuid.uuid4()}"
        record = {
            "id": msg_id,
            "title": title,
            "body": body,
            "data": data or {},
            "subscription": subscription_info,
        }
        self.sent_pushes.append(record)
        logger.info(f"[MOCK PUSH DISPATCHED] ID: {msg_id} | Title: {title} | Body: {body}")

        return PushResult(
            success=True,
            provider=self.provider_name,
            message_id=msg_id,
            status="sent",
        )


mock_push_provider = MockPushProvider()
