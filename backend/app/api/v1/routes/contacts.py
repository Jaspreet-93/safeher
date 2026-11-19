import uuid

from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.contact import (
    ContactConsentRequest,
    ContactCreateRequest,
    ContactResponse,
    ContactUpdateRequest,
)
from app.services.contact_service import ContactService

router = APIRouter(prefix="/contacts", tags=["Emergency Contacts"])


@router.get("", response_model=list[ContactResponse])
async def list_emergency_contacts(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ContactResponse]:
    """Retrieves all active emergency contacts designated by the authenticated user."""
    return await ContactService.list_contacts(db, current_user.id)


@router.post("", response_model=ContactResponse, status_code=status.HTTP_201_CREATED)
async def add_emergency_contact(
    req: ContactCreateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    """Adds a new emergency contact and generates a consent verification token."""
    return await ContactService.create_contact(db, current_user.id, req)


@router.put("/{contact_id}", response_model=ContactResponse)
async def update_emergency_contact(
    contact_id: uuid.UUID,
    req: ContactUpdateRequest,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    """Updates an existing contact's priority or location permission scope."""
    return await ContactService.update_contact(db, current_user.id, contact_id, req)


@router.delete("/{contact_id}", status_code=status.HTTP_200_OK)
async def remove_emergency_contact(
    contact_id: uuid.UUID,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Removes an emergency contact and revokes their verification status immediately."""
    await ContactService.delete_contact(db, current_user.id, contact_id)
    return {"status": "removed", "message": "Emergency contact removed and permissions revoked."}


@router.post("/verify/{token}", response_model=ContactResponse)
async def verify_contact_consent(
    token: str,
    req: ContactConsentRequest,
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    """Public endpoint: Allows an emergency contact to accept or decline acting as a responder."""
    return await ContactService.verify_contact_consent(
        db, verification_token=token, accept=req.accept
    )
