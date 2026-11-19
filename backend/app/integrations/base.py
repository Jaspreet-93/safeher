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


class PushResult(BaseModel):
    success: bool
    provider: str
    message_id: str | None = None
    status: str  # sent, failed
    error_message: str | None = None


class BasePushProvider(ABC):
    """Abstract interface for device and web push notifications."""

    @abstractmethod
    async def send_push(
        self,
        subscription_info: dict[str, Any],
        title: str,
        body: str,
        data: dict[str, Any] | None = None,
    ) -> PushResult:
        """Dispatches an encrypted push payload to a client device."""
        pass


class EmailResult(BaseModel):
    success: bool
    provider: str
    message_id: str | None = None
    status: str = "sent"  # sent, delivered, failed
    error_message: str | None = None


class BaseEmailProvider(ABC):
    """Abstract interface for transactional emergency email dispatch."""

    @abstractmethod
    async def send_email(
        self,
        to_email: str,
        subject: str,
        html_body: str,
        text_body: str | None = None,
    ) -> EmailResult:
        """Sends an emergency email alert."""
        pass
