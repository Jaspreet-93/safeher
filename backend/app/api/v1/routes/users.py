from fastapi import APIRouter, Depends, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user, require_role
from app.models.user import User
from app.schemas.user import (
    ProfileResponse,
    UserProfileUpdate,
    UserWithProfileResponse,
)
from app.services.user_service import UserService

router = APIRouter(prefix="/users", tags=["Users & Profiles"])


@router.get("/me", response_model=UserWithProfileResponse)
async def get_my_profile(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> UserWithProfileResponse:
    """Returns the authenticated user's account details and profile."""
    user = await UserService.get_user_with_profile(db, current_user.id)
    return user


@router.put("/me/profile", response_model=ProfileResponse)
async def update_my_profile(
    req: UserProfileUpdate,
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> ProfileResponse:
    """Updates voluntary emergency contact notes and profile preferences."""
    profile = await UserService.update_profile(db, current_user.id, req)
    return profile


@router.delete("/me", status_code=status.HTTP_200_OK)
async def delete_my_account(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Initiates user-requested account deactivation and cascades session revocation."""
    await UserService.deactivate_account(db, current_user.id)
    return {
        "status": "deactivated",
        "message": "Account has been deactivated. Data retention and erasure workflow initiated.",
    }


@router.get("/admin/overview", dependencies=[Depends(require_role("admin"))])
async def admin_only_overview() -> dict[str, str]:
    """Protected endpoint for verifying Role-Based Access Control (RBAC). Only accessible by admins."""
    return {"status": "authorized", "scope": "platform_admin"}
