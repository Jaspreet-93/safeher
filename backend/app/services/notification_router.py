from typing import Any

from app.core.logging import logger
from app.integrations.base import BaseEmailProvider, BasePushProvider, BaseSmsProvider
from app.integrations.mock.email import mock_email_provider
from app.integrations.mock.push import mock_push_provider
from app.integrations.mock.sms import mock_sms_provider
from app.integrations.sms.dlt_provider import DLTSmsProvider


class NotificationRouter:
    """
    Emergency Notification Failover & Circuit Breaker Engine.
    Orchestrates:
    Primary SMS (DLT Gateway) ──(fail)──► Secondary SMS Gateway ──(fail)──► Email / Push
    """

    def __init__(
        self,
        primary_sms: BaseSmsProvider | None = None,
        secondary_sms: BaseSmsProvider | None = None,
        push_provider: BasePushProvider | None = None,
        email_provider: BaseEmailProvider | None = None,
    ):
        self.primary_sms = primary_sms or DLTSmsProvider()
        self.secondary_sms = secondary_sms or mock_sms_provider
        self.push_provider = push_provider or mock_push_provider
        self.email_provider = email_provider or mock_email_provider

    async def dispatch_alert(
        self,
        recipient_phone: str,
        message: str,
        recipient_email: str | None = None,
        dlt_template_id: str | None = None,
    ) -> dict[str, Any]:
        """
        Dispatches emergency alert with automated multi-tier failover.
        """
        dispatch_trail = []

        # Tier 1: Primary SMS Gateway
        logger.info(f"[NOTIF ROUTER] Attempting Tier 1 Primary SMS to {recipient_phone}")
        res_primary = await self.primary_sms.send_sms(
            to_phone=recipient_phone,
            message=message,
            dlt_template_id=dlt_template_id,
        )
        dispatch_trail.append({"tier": 1, "channel": "primary_sms", "result": res_primary.model_dump()})

        if res_primary.success:
            return {
                "success": True,
                "delivered_via": "primary_sms",
                "message_id": res_primary.message_id,
                "status": res_primary.status,
                "trail": dispatch_trail,
            }

        logger.warning(
            f"[NOTIF ROUTER FAILOVER] Primary SMS failed ({res_primary.error_message}). Escalating to Tier 2 Secondary SMS Gateway."
        )

        # Tier 2: Secondary SMS Gateway Failover
        res_secondary = await self.secondary_sms.send_sms(
            to_phone=recipient_phone,
            message=message,
            dlt_template_id=dlt_template_id,
        )
        dispatch_trail.append({"tier": 2, "channel": "secondary_sms", "result": res_secondary.model_dump()})

        if res_secondary.success:
            return {
                "success": True,
                "delivered_via": "secondary_sms_failover",
                "message_id": res_secondary.message_id,
                "status": res_secondary.status,
                "trail": dispatch_trail,
            }

        logger.warning(
            f"[NOTIF ROUTER FAILOVER] Secondary SMS failed ({res_secondary.error_message}). Attempting Tier 3 Email/Push."
        )

        # Tier 3: Email Fallback (if email provided)
        if recipient_email:
            res_email = await self.email_provider.send_email(
                to_email=recipient_email,
                subject="URGENT: SafeHer Emergency SOS Alert",
                html_body=f"<p>{message}</p>",
                text_body=message,
            )
            dispatch_trail.append({"tier": 3, "channel": "email_fallback", "result": res_email.model_dump()})
            if res_email.success:
                return {
                    "success": True,
                    "delivered_via": "email_fallback",
                    "message_id": res_email.message_id,
                    "status": "delivered",
                    "trail": dispatch_trail,
                }

        # All channels failed: Fail loudly!
        last_error = (
            (res_email.error_message if recipient_email and "res_email" in locals() else None)
            or res_secondary.error_message
            or res_primary.error_message
            or "Gateway failure"
        )
        logger.error(f"[NOTIF ROUTER CRITICAL] All emergency alert channels failed for {recipient_phone}: {last_error}")
        return {
            "success": False,
            "delivered_via": None,
            "status": "failed",
            "error_message": f"All carrier gateways and fallbacks failed to dispatch alert: {last_error}",
            "trail": dispatch_trail,
        }


notification_router = NotificationRouter()
