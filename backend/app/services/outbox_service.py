from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.logging import logger
from app.integrations.mock.sms import mock_sms_provider
from app.models.incident import EmergencyNotification


class OutboxService:
    @staticmethod
    async def process_queued_notifications(
        db: AsyncSession,
        max_batch_size: int = 50,
    ) -> dict[str, int]:
        """
        Polls and dispatches queued notifications from the transactional outbox.
        Enforces state transitions: queued -> sent/delivered or failed.
        """
        now = datetime.now(timezone.utc)
        query = (
            select(EmergencyNotification)
            .where(EmergencyNotification.status == "queued")
            .limit(max_batch_size)
        )
        result = await db.execute(query)
        queued_items = list(result.scalars().all())

        dispatched_count = 0
        failed_count = 0

        for item in queued_items:
            try:
                # Dispatch through provider
                send_result = await mock_sms_provider.send_sms(
                    to_phone=item.recipient_address,
                    message=item.message_body,
                )

                if send_result.success:
                    item.status = send_result.status  # "sent" or "delivered"
                    item.sent_at = now
                    if send_result.status == "delivered":
                        item.delivered_at = now
                    dispatched_count += 1
                else:
                    item.retry_count += 1
                    item.failure_reason = send_result.error_message
                    if item.retry_count >= 3:
                        item.status = "failed"
                        logger.error(
                            f"[OUTBOX DEAD-LETTER] Notification {item.id} permanently failed after 3 retries: {send_result.error_message}"
                        )
                    failed_count += 1
            except Exception as e:
                item.retry_count += 1
                item.failure_reason = str(e)
                if item.retry_count >= 3:
                    item.status = "failed"
                failed_count += 1
                logger.error(f"[OUTBOX EXCEPTION] Error dispatching notification {item.id}: {e}")

        await db.commit()
        return {
            "processed": len(queued_items),
            "dispatched": dispatched_count,
            "failed": failed_count,
        }
