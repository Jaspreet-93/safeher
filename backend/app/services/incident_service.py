import asyncio
import secrets
import uuid
from datetime import datetime, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundException, ValidationException
from app.core.logging import logger
from app.models.contact import EmergencyContact
from app.models.incident import EmergencyIncident, EmergencyNotification
from app.models.user import User
from app.schemas.incident import (
    ContactAckResponse,
    IncidentDetailResponse,
    NotificationStatusResponse,
    SOSCancelRequest,
    SOSResolveRequest,
    SOSTriggerRequest,
)
from app.services.outbox_service import OutboxService


class IncidentService:
    @staticmethod
    async def trigger_sos(
        db: AsyncSession,
        user: User,
        req: SOSTriggerRequest,
        idempotency_key: str,
    ) -> EmergencyIncident:
        """
        Idempotent SOS trigger. If the idempotency key was already processed,
        returns the existing incident without creating duplicates or redundant notifications.
        """
        now = datetime.now(timezone.utc)

        # 1. Idempotency Check
        existing_res = await db.execute(
            select(EmergencyIncident)
            .where(EmergencyIncident.idempotency_key == idempotency_key)
            .options(
                selectinload(EmergencyIncident.notifications).selectinload(
                    EmergencyNotification.contact
                )
            )
        )
        existing = existing_res.scalar_one_or_none()
        if existing:
            logger.info(f"[IDEMPOTENCY HIT] Re-returning existing incident: {existing.id}")
            return existing

        # 2. Create Incident Record
        incident = EmergencyIncident(
            user_id=user.id,
            status="created",
            idempotency_key=idempotency_key,
            latitude=req.latitude,
            longitude=req.longitude,
            accuracy_meters=req.accuracy_meters,
            location_timestamp=req.location_timestamp or now,
            grace_period_seconds=req.grace_period_seconds,
            triggered_at=now,
        )
        try:
            db.add(incident)
            await db.commit()
        except Exception:
            await db.rollback()
            for _ in range(5):
                existing_res = await db.execute(
                    select(EmergencyIncident)
                    .where(EmergencyIncident.idempotency_key == idempotency_key)
                    .options(
                        selectinload(EmergencyIncident.notifications).selectinload(
                            EmergencyNotification.contact
                        )
                    )
                )
                existing = existing_res.scalar_one_or_none()
                if existing:
                    logger.info(
                        f"[CONCURRENT IDEMPOTENCY RESOLVED] Returning existing incident: {existing.id}"
                    )
                    return existing
                await asyncio.sleep(0.05)
            raise

        logger.info(
            f"[SOS CREATED] User: {user.id} | Incident: {incident.id} | Grace: {req.grace_period_seconds}s"
        )

        # If zero grace period configured, activate immediately
        if req.grace_period_seconds == 0:
            return await IncidentService.activate_incident(db, user, incident.id)

        return incident

    @staticmethod
    async def activate_incident(
        db: AsyncSession,
        user: User,
        incident_id: uuid.UUID,
    ) -> EmergencyIncident:
        """
        Transitions incident state: created -> active.
        Generates Transactional Outbox notifications for trusted contacts and triggers dispatch.
        """
        now = datetime.now(timezone.utc)
        query = select(EmergencyIncident).where(
            EmergencyIncident.id == incident_id,
            EmergencyIncident.user_id == user.id,
        )
        res = await db.execute(query)
        incident = res.scalar_one_or_none()
        if not incident:
            raise NotFoundException("Emergency incident not found")

        if incident.status == "cancelled":
            raise ValidationException("Cannot activate an incident that was already cancelled.")

        incident.status = "active"
        incident.activated_at = now

        # Fetch eligible emergency contacts
        # Only contacts with location_permission != "none" receive coordinates
        contacts_query = (
            select(EmergencyContact)
            .where(
                EmergencyContact.user_id == user.id,
                EmergencyContact.is_active.is_(True),
            )
            .order_by(EmergencyContact.priority)
        )
        contacts_res = await db.execute(contacts_query)
        contacts = list(contacts_res.scalars().all())

        user_res = await db.execute(
            select(User).where(User.id == user.id).options(selectinload(User.profile))
        )
        loaded_user = user_res.scalar_one_or_none()
        user_display_name = user.email.split("@")[0]
        if loaded_user and loaded_user.profile and loaded_user.profile.full_name:
            user_display_name = loaded_user.profile.full_name

        # Atomically populate Transactional Outbox
        for contact in contacts:
            if contact.location_permission == "none":
                # Contact requested zero location telemetry
                continue

            ack_token = secrets.token_urlsafe(32)
            ack_url = f"http://localhost:5173/emergency/ack/{ack_token}"
            maps_url = f"https://www.google.com/maps/search/?api=1&query={incident.latitude},{incident.longitude}"

            sms_body = (
                f"SAFEHER SOS ALERT: {user_display_name} has triggered an emergency alert! "
                f"Location: {maps_url} . "
                f"Tap to view and acknowledge: {ack_url} or call 112."
            )

            notif = EmergencyNotification(
                incident_id=incident.id,
                contact_id=contact.id,
                channel="sms",
                status="queued",
                recipient_address=contact.phone_number,
                message_body=sms_body,
                secure_ack_token=ack_token,
            )
            db.add(notif)

        await db.commit()

        # Immediately dispatch queued items through Outbox Engine
        await OutboxService.process_queued_notifications(db)

        # Refresh incident with notifications
        refreshed_res = await db.execute(
            select(EmergencyIncident)
            .where(EmergencyIncident.id == incident.id)
            .options(
                selectinload(EmergencyIncident.notifications).selectinload(
                    EmergencyNotification.contact
                )
            )
        )
        return refreshed_res.scalar_one()

    @staticmethod
    async def cancel_incident(
        db: AsyncSession,
        user: User,
        incident_id: uuid.UUID,
        req: SOSCancelRequest,
    ) -> EmergencyIncident:
        """
        Cancels incident (typically within grace window countdown).
        Aborts any pending notifications in outbox so zero external alerts are dispatched.
        """
        now = datetime.now(timezone.utc)
        query = select(EmergencyIncident).where(
            EmergencyIncident.id == incident_id,
            EmergencyIncident.user_id == user.id,
        )
        res = await db.execute(query)
        incident = res.scalar_one_or_none()
        if not incident:
            raise NotFoundException("Emergency incident not found")

        incident.status = "cancelled"
        incident.cancelled_at = now
        incident.cancel_reason = req.cancel_reason

        # Abort any queued notifications that haven't been picked up
        notifs_res = await db.execute(
            select(EmergencyNotification).where(
                EmergencyNotification.incident_id == incident.id,
                EmergencyNotification.status == "queued",
            )
        )
        for notif in notifs_res.scalars().all():
            notif.status = "failed"
            notif.failure_reason = "Incident cancelled by user within grace window"

        await db.commit()
        await db.refresh(incident)
        logger.info(f"[SOS CANCELLED] Incident: {incident.id} | Reason: {req.cancel_reason}")
        return incident

    @staticmethod
    async def resolve_incident(
        db: AsyncSession,
        user: User,
        incident_id: uuid.UUID,
        req: SOSResolveRequest,
    ) -> EmergencyIncident:
        """Resolves active incident when user or responder confirms safety."""
        now = datetime.now(timezone.utc)
        query = select(EmergencyIncident).where(
            EmergencyIncident.id == incident_id,
            EmergencyIncident.user_id == user.id,
        )
        res = await db.execute(query)
        incident = res.scalar_one_or_none()
        if not incident:
            raise NotFoundException("Emergency incident not found")

        incident.status = "resolved"
        incident.resolved_at = now
        incident.resolution_notes = req.resolution_notes
        await db.commit()
        await db.refresh(incident)
        return incident

    @staticmethod
    async def acknowledge_alert(
        db: AsyncSession,
        ack_token: str,
    ) -> ContactAckResponse:
        """Public contact acknowledgement endpoint when opening the secure SMS emergency link."""
        now = datetime.now(timezone.utc)
        query = (
            select(EmergencyNotification)
            .where(EmergencyNotification.secure_ack_token == ack_token)
            .options(
                selectinload(EmergencyNotification.incident)
                .selectinload(EmergencyIncident.user)
                .selectinload(User.profile),
                selectinload(EmergencyNotification.contact),
            )
        )
        res = await db.execute(query)
        notif = res.scalar_one_or_none()
        if not notif:
            raise NotFoundException("Invalid or expired emergency acknowledgement token")

        notif.status = "acknowledged"
        notif.acknowledged_at = now
        await db.commit()

        incident = notif.incident
        sharer = incident.user
        sharer_name = sharer.profile.full_name if sharer.profile else sharer.email

        maps_link = f"https://www.google.com/maps/search/?api=1&query={incident.latitude},{incident.longitude}"

        return ContactAckResponse(
            incident_id=incident.id,
            user_name=sharer_name,
            contact_name=notif.contact.name,
            status="acknowledged",
            latitude=incident.latitude,
            longitude=incident.longitude,
            accuracy_meters=incident.accuracy_meters,
            triggered_at=incident.triggered_at,
            acknowledged_at=now,
            emergency_fallback_number="112",
            map_deep_link=maps_link,
        )

    @staticmethod
    async def get_incident_status(
        db: AsyncSession,
        user: User,
        incident_id: uuid.UUID,
    ) -> IncidentDetailResponse:
        """Returns the complete incident status and per-contact delivery receipts."""
        query = (
            select(EmergencyIncident)
            .where(
                EmergencyIncident.id == incident_id,
                EmergencyIncident.user_id == user.id,
            )
            .options(
                selectinload(EmergencyIncident.notifications).selectinload(
                    EmergencyNotification.contact
                )
            )
        )
        res = await db.execute(query)
        incident = res.scalar_one_or_none()
        if not incident:
            raise NotFoundException("Incident not found")

        notification_dtos = [
            NotificationStatusResponse(
                id=n.id,
                contact_id=n.contact_id,
                contact_name=n.contact.name if n.contact else "Unknown",
                recipient_address=n.recipient_address,
                channel=n.channel,
                status=n.status,
                sent_at=n.sent_at,
                delivered_at=n.delivered_at,
                acknowledged_at=n.acknowledged_at,
                failure_reason=n.failure_reason,
            )
            for n in incident.notifications
        ]

        return IncidentDetailResponse(
            id=incident.id,
            user_id=incident.user_id,
            status=incident.status,
            idempotency_key=incident.idempotency_key,
            latitude=incident.latitude,
            longitude=incident.longitude,
            accuracy_meters=incident.accuracy_meters,
            grace_period_seconds=incident.grace_period_seconds,
            triggered_at=incident.triggered_at,
            activated_at=incident.activated_at,
            cancelled_at=incident.cancelled_at,
            resolved_at=incident.resolved_at,
            cancel_reason=incident.cancel_reason,
            resolution_notes=incident.resolution_notes,
            notifications=notification_dtos,
        )
