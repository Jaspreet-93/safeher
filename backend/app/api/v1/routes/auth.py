from fastapi import APIRouter, Depends, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.database import get_db
from app.core.security import get_current_active_user
from app.models.user import User
from app.schemas.auth import (
    LoginRequest,
    RefreshTokenRequest,
    RegisterRequest,
    TokenResponse,
)
from app.services.auth_service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=TokenResponse, status_code=status.HTTP_201_CREATED)
async def register(
    req: RegisterRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Registers a new user account, profile, and initial DPDPA consent record."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await AuthService.register(db, req, ip_address=ip, user_agent=ua)


@router.post("/login", response_model=TokenResponse)
async def login(
    req: LoginRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Authenticates credentials, guards against brute force, and returns rotating tokens."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await AuthService.login(db, req, ip_address=ip, user_agent=ua)


@router.post("/refresh", response_model=TokenResponse)
async def refresh_tokens(
    req: RefreshTokenRequest,
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> TokenResponse:
    """Rotates refresh token and returns a new access/refresh pair. Detects token reuse."""
    ip = request.client.host if request.client else None
    ua = request.headers.get("user-agent")
    return await AuthService.refresh_tokens(
        db,
        raw_refresh_token=req.refresh_token,
        device_name=req.device_name,
        ip_address=ip,
        user_agent=ua,
    )


@router.post("/logout", status_code=status.HTTP_200_OK)
async def logout(
    req: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Revokes the specified refresh token session."""
    await AuthService.logout(db, raw_refresh_token=req.refresh_token)
    return {"status": "logged_out", "message": "Session revoked successfully"}


@router.post("/sessions/revoke-all", status_code=status.HTTP_200_OK)
async def revoke_all_sessions(
    current_user: User = Depends(get_current_active_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """Nuclear option: Revokes all active sessions for the authenticated user across all devices."""
    await AuthService.revoke_all_sessions(db, user_id=current_user.id)
    return {"status": "all_revoked", "message": "All active sessions have been terminated"}
