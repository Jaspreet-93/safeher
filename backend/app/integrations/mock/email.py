import uuid
from typing import Any

from app.core.logging import logger
from app.integrations.base import BaseEmailProvider, EmailResult


class MockEmailProvider(BaseEmailProvider):
    """
    Mock Transactional Email Provider.
    Honest [MOCK] labeling per Rule 5.
    """

    def __init__(self):
        self.provider_name = "MOCK_EMAIL_PROVIDER"
        self.sent_emails: list[dict[str, Any]] = []
        self.simulate_failure: bool = False

    def reset(self) -> None:
        self.sent_emails.clear()
        self.simulate_failure = False

    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> EmailResult:
        if self.simulate_failure:
            logger.warning("[MOCK EMAIL FAILURE INJECTED] Email dispatch simulated failure")
            return EmailResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error_message="Simulated SMTP server timeout or connection reset",
            )

        msg_id = f"mock-email-{uuid.uuid4()}"
        record = {
            "id": msg_id,
            "to_email": to_email,
            "subject": subject,
            "html_body": html_body,
            "text_body": text_body,
        }
        self.sent_emails.append(record)
        logger.info(f"[MOCK EMAIL DISPATCHED] ID: {msg_id} | To: {to_email} | Subject: {subject}")

        return EmailResult(
            success=True,
            provider=self.provider_name,
            message_id=msg_id,
            status="delivered",
        )


mock_email_provider = MockEmailProvider()
