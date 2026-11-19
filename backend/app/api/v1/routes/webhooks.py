import hashlib
import hmac
import json
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Header, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.logging import logger
from app.models.incident import EmergencyNotification

router = APIRouter(prefix="/webhooks", tags=["webhooks"])


class DLRWebhookPayload(BaseModel):
    message_id: str = Field(description="Carrier message identifier")
    status: str = Field(description="Carrier delivery status (delivered, failed, etc.)")
    phone_number: str | None = None
    error_code: str | None = None
    error_message: str | None = None
    timestamp: datetime | None = None


def verify_webhook_hmac(body_bytes: bytes, signature_header: str | None) -> bool:
    """Verifies SHA-256 HMAC signature against raw payload bytes."""
    if not signature_header:
        return False
    expected_sig = hmac.new(
        settings.WEBHOOK_SECRET.encode("utf-8"),
        body_bytes,
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(expected_sig, signature_header)


@router.post("/sms/dlr")
async def handle_sms_dlr_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    x_webhook_signature: str | None = Header(None, alias="X-Webhook-Signature"),
) -> dict[str, Any]:
    """
    Carrier Delivery Receipt (DLR) Webhook.
    Verifies HMAC-SHA256 signature to protect against spoofing/tampering.
    Updates outbox notification status to delivered/failed.
    """
    raw_body = await request.body()
    if not verify_webhook_hmac(raw_body, x_webhook_signature):
        logger.warning("[DLR WEBHOOK FORGERY ATTEMPT] Webhook signature invalid or missing.")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or missing webhook signature",
        )

    try:
        data = json.loads(raw_body)
        payload = DLRWebhookPayload.model_validate(data)
    except Exception as e:
        logger.error(f"[DLR WEBHOOK INVALID PAYLOAD] {e}")
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Malformed webhook payload: {e}",
        ) from e

    # Lookup EmergencyNotification by provider_message_id
    query = select(EmergencyNotification).where(
        EmergencyNotification.provider_message_id == payload.message_id
    )
    result = await db.execute(query)
    notif = result.scalar_one_or_none()

    if not notif:
        logger.warning(
            f"[DLR WEBHOOK] Notification with provider_message_id {payload.message_id} not found."
        )
        return {
            "status": "ignored",
            "reason": "notification_not_found",
            "message_id": payload.message_id,
        }

    normalized_status = payload.status.lower()
    now = datetime.now(timezone.utc)

    if normalized_status in ("delivered", "delivrd", "success"):
        notif.status = "delivered"
        notif.delivered_at = payload.timestamp or now
    elif normalized_status in ("failed", "undeliv", "undelivered", "rejected"):
        notif.status = "failed"
        notif.failure_reason = payload.error_message or payload.error_code or "Carrier delivery failed"
    else:
        # e.g., "sent", "buffered", "enroute"
        notif.status = "sent"

    await db.commit()
    await db.refresh(notif)
    logger.info(
        f"[DLR WEBHOOK PROCESSED] Notification {notif.id} updated to {notif.status} (Provider Msg ID: {payload.message_id})"
    )

    return {
        "status": "processed",
        "notification_id": str(notif.id),
        "new_status": notif.status,
    }
