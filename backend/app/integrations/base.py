from abc import ABC, abstractmethod
from typing import Any

from pydantic import BaseModel


class SmsResult(BaseModel):
    success: bool
    provider: str
    message_id: str | None = None
    status: str  # sent, delivered, failed
    error_message: str | None = None
    raw_response: dict[str, Any] | None = None


class BaseSmsProvider(ABC):
    """Abstract interface for transactional SMS dispatch."""

    @abstractmethod
    async def send_sms(
        self,
        to_phone: str,
        message: str,
        dlt_template_id: str | None = None,
    ) -> SmsResult:
        """Dispatches an SMS to the given phone number adhering to DLT parameters."""
        pass
