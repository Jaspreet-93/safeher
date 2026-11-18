from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.consent import ConsentCreateRequest, ConsentResponse
from app.services.user_service import UserService

router = APIRouter(prefix="/consent", tags=["Privacy & Consent (DPDPA)"])


@router.post("", response_model=ConsentResponse, status_code=status.HTTP_201_CREATED)
async def record_user_consent(
    req: ConsentCreateRequest,
    request: Request,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ConsentResponse:
    """Records an explicit, auditable consent decision under the Digital Personal Data Protection Act, 2023."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await UserService.record_consent(
        db,
        user_id=current_user.id,
        req=req,
        ip_address=ip,
        user_agent=ua,
    )


@router.get("/history", response_model=list[ConsentResponse])
async def get_consent_history(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> list[ConsentResponse]:
    """Retrieves the authenticated user's complete historical consent trail."""
    return await UserService.get_consent_history(db, current_user.id)
