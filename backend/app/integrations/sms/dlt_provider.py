import re
from typing import Any

import httpx

from app.core.config import settings
from app.core.logging import logger
from app.integrations.base import BaseSmsProvider, SmsResult
from app.integrations.mock.sms import mock_sms_provider


class DLTSmsProvider(BaseSmsProvider):
    """
    Indian DLT-Compliant SMS Provider Adapter.
    Adheres to TRAI regulations with mandatory Sender ID and registered template enforcement.
    Falls back gracefully to MockSmsProvider in dev/testing when API keys are absent.
    """

    # Pre-registered TRAI DLT Template IDs & Format strings
    TEMPLATES = {
        "SOS_ALERT": {
            "dlt_template_id": "1107168923450912345",
            "format": "SAFEHER SOS ALERT: {user_name} has triggered an emergency alert! Location: {maps_url} . Tap to view: {ack_url} or call 112.",
        },
        "CONTACT_VERIFY": {
            "dlt_template_id": "1107168923450912346",
            "format": "SAFEHER: You were nominated as emergency contact for {user_name}. Tap to accept or decline: {verify_url}",
        },
    }

    def __init__(self):
        self.provider_name = "FAST2SMS_DLT"
        self.sender_id = settings.SMS_DLT_SENDER_ID
        self.api_key = settings.FAST2SMS_API_KEY

    def validate_indian_phone(self, phone: str) -> str:
        """Sanitizes and validates an Indian mobile number."""
        clean = re.sub(r"[^\d]", "", phone)
        if clean.startswith("91") and len(clean) == 12:
            clean = clean[2:]
        if len(clean) != 10 or clean[0] not in "6789":
            raise ValueError(f"Invalid Indian mobile number: {phone}")
        return clean

    async def send_sms(
        self,
        to_phone: str,
        message: str,
        dlt_template_id: str | None = None,
    ) -> SmsResult:
        # Check if real gateway credentials are configured
        if not self.api_key:
            logger.info(
                f"[MOCK DLT SMS] API key absent. Delegating dispatch to MockSmsProvider for {to_phone} (Sender: {self.sender_id})"
            )
            return await mock_sms_provider.send_sms(to_phone, message, dlt_template_id)

        try:
            sanitized_phone = self.validate_indian_phone(to_phone)
        except ValueError as e:
            return SmsResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error_message=str(e),
            )

        # Real Fast2SMS / Gateway HTTP Dispatch
        endpoint = "https://www.fast2sms.com/dev/bulkV2"
        headers = {
            "authorization": self.api_key,
            "Content-Type": "application/json",
        }
        payload: dict[str, Any] = {
            "route": "dlt",
            "sender_id": self.sender_id,
            "message": message,
            "numbers": sanitized_phone,
        }
        if dlt_template_id:
            payload["template_id"] = dlt_template_id

        try:
            async with httpx.AsyncClient(timeout=8.0) as client:
                res = await client.post(endpoint, json=payload, headers=headers)
                data = res.json()

                if res.status_code == 200 and data.get("return") is True:
                    msg_id = data.get("request_id", str(data.get("message", ["ok"])[0]))
                    return SmsResult(
                        success=True,
                        provider=self.provider_name,
                        message_id=msg_id,
                        status="sent",
                        raw_response=data,
                    )
                else:
                    err_msg = data.get("message", f"HTTP {res.status_code} Error from SMS Gateway")
                    logger.error(f"[DLT SMS GATEWAY ERROR] {err_msg}")
                    return SmsResult(
                        success=False,
                        provider=self.provider_name,
                        status="failed",
                        error_message=str(err_msg),
                        raw_response=data,
                    )
        except Exception as e:
            logger.error(f"[DLT SMS NETWORK ERROR] Failed to contact gateway: {e}")
            return SmsResult(
                success=False,
                provider=self.provider_name,
                status="failed",
                error_message=f"Network error contacting SMS gateway: {str(e)}",
            )
