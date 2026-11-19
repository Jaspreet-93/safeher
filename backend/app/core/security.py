import hashlib
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from typing import Any

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError
from fastapi import Depends
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.database import get_db
from app.core.errors import ForbiddenException, UnauthorizedException

pwd_hasher = PasswordHasher(
    time_cost=3,
    memory_cost=65536,
    parallelism=4,
)

oauth2_scheme = OAuth2PasswordBearer(
    tokenUrl=f"{settings.API_V1_PREFIX}/auth/login",
    auto_error=False,
)


def hash_password(password: str) -> str:
    """Hashes a plain password using high-entropy Argon2id."""
    return pwd_hasher.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """Verifies a plain password against an Argon2id hash."""
    try:
        return pwd_hasher.verify(hashed_password, plain_password)
    except (VerifyMismatchError, Exception):
        return False


def hash_token(raw_token: str) -> str:
    """Creates a SHA-256 hash of an opaque token for secure storage at rest."""
    return hashlib.sha256(raw_token.encode("utf-8")).hexdigest()


def generate_refresh_token() -> str:
    """Generates a high-entropy, opaque cryptographic refresh token."""
    return secrets.token_urlsafe(48)


def create_access_token(
    subject: str,
    role: str = "user",
    expires_delta: timedelta | None = None,
) -> str:
    """Creates a signed JWT access token with short-lived expiration."""
    now = datetime.now(timezone.utc)
    if expires_delta:
        expire = now + expires_delta
    else:
        expire = now + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode: dict[str, Any] = {
        "sub": subject,
        "role": role,
        "exp": expire,
        "iat": now,
        "type": "access",
    }
    return jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    """Decodes and validates a JWT access token."""
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM])
        if payload.get("type") != "access":
            raise UnauthorizedException("Invalid token type")
        return payload
    except JWTError as err:
        raise UnauthorizedException("Could not validate credentials or token expired") from err


async def get_current_user(
    token: str | None = Depends(oauth2_scheme),
    db: AsyncSession = Depends(get_db),
):
    """Dependency that extracts and validates the currently authenticated User."""
    from app.models.user import User

    if not token:
        raise UnauthorizedException("Authentication credentials were not provided")

    payload = decode_access_token(token)
    user_id_str = payload.get("sub")
    if not user_id_str:
        raise UnauthorizedException("Malformed token claims")

    result = await db.execute(
        select(User).where(User.id == user_id_str).options(selectinload(User.profile))
    )
    user = result.scalar_one_or_none()

    if not user:
        raise UnauthorizedException("User no longer exists")

    if not user.is_active:
        raise ForbiddenException("User account is inactive or disabled")

    return user


async def get_current_active_user(
    current_user=Depends(get_current_user),
):
    """Ensures current user is active."""
    return current_user


def require_role(required_roles: list[str] | str) -> Callable:
    """RBAC dependency that enforces required role(s)."""
    roles_list = [required_roles] if isinstance(required_roles, str) else required_roles

    async def role_checker(current_user=Depends(get_current_active_user)):
        if current_user.role not in roles_list and "admin" not in current_user.role:
            raise ForbiddenException(
                f"Access requires one of roles: {roles_list}. Current role: {current_user.role}"
            )
        return current_user

    return role_checker
