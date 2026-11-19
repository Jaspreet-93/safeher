import secrets
import uuid

from sqlalchemy import asc, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.errors import NotFoundException, ValidationException
from app.models.contact import EmergencyContact
from app.schemas.contact import ContactCreateRequest, ContactUpdateRequest


class ContactService:
    @staticmethod
    async def list_contacts(db: AsyncSession, user_id: uuid.UUID) -> list[EmergencyContact]:
        """Lists active emergency contacts for a user, ordered by priority."""
        query = (
            select(EmergencyContact)
            .where(EmergencyContact.user_id == user_id, EmergencyContact.is_active.is_(True))
            .order_by(asc(EmergencyContact.priority))
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def create_contact(
        db: AsyncSession,
        user_id: uuid.UUID,
        req: ContactCreateRequest,
    ) -> EmergencyContact:
        """Adds a new emergency contact and generates an initial verification consent token."""
        # Check existing contact with same phone for this user
        existing_res = await db.execute(
            select(EmergencyContact).where(
                EmergencyContact.user_id == user_id,
                EmergencyContact.phone_number == req.phone_number,
                EmergencyContact.is_active.is_(True),
            )
        )
        if existing_res.scalar_one_or_none():
            raise ValidationException(
                "An active emergency contact with this phone number already exists."
            )

        verification_token = secrets.token_urlsafe(32)

        contact = EmergencyContact(
            user_id=user_id,
            name=req.name,
            phone_number=req.phone_number,
            email=req.email,
            relationship=req.relationship,
            priority=req.priority,
            location_permission=req.location_permission,
            is_verified=False,  # Requires contact consent
            verification_token=verification_token,
            is_active=True,
        )
        db.add(contact)
        await db.commit()
        await db.refresh(contact)
        return contact

    @staticmethod
    async def update_contact(
        db: AsyncSession,
        user_id: uuid.UUID,
        contact_id: uuid.UUID,
        req: ContactUpdateRequest,
    ) -> EmergencyContact:
        """Updates contact details and permission scopes."""
        query = select(EmergencyContact).where(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == user_id,
        )
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundException("Emergency contact not found")

        update_data = req.model_dump(exclude_unset=True)
        for key, val in update_data.items():
            setattr(contact, key, val)

        await db.commit()
        await db.refresh(contact)
        return contact

    @staticmethod
    async def delete_contact(
        db: AsyncSession,
        user_id: uuid.UUID,
        contact_id: uuid.UUID,
    ) -> None:
        """Deactivates and removes an emergency contact."""
        query = select(EmergencyContact).where(
            EmergencyContact.id == contact_id,
            EmergencyContact.user_id == user_id,
        )
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundException("Emergency contact not found")

        contact.is_active = False
        contact.verification_token = None  # Invalidate token immediately
        await db.commit()

    @staticmethod
    async def verify_contact_consent(
        db: AsyncSession,
        verification_token: str,
        accept: bool,
    ) -> EmergencyContact:
        """Allows a contact to accept or decline being an emergency contact via secure token link."""
        query = select(EmergencyContact).where(
            EmergencyContact.verification_token == verification_token,
        )
        result = await db.execute(query)
        contact = result.scalar_one_or_none()
        if not contact:
            raise NotFoundException("Invalid or expired verification link")

        if accept:
            contact.is_verified = True
        else:
            contact.is_active = False
            contact.is_verified = False

        contact.verification_token = None  # One-time use token
        await db.commit()
        await db.refresh(contact)
        return contact
