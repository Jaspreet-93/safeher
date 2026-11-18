from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.config import settings
from app.core.errors import (
    SafeHerException,
    UnauthorizedException,
    ValidationException,
)
from app.core.logging import logger
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.models.consent import ConsentRecord
from app.models.session import AuthSession
from app.models.user import User, UserProfile
from app.schemas.auth import LoginRequest, RegisterRequest, TokenResponse


def ensure_utc(dt: datetime | None) -> datetime | None:
    if dt is None:
        return None
    if dt.tzinfo is None:
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


class AuthService:
    @staticmethod
    async def register(
        db: AsyncSession,
        req: RegisterRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Registers a new user, creates their profile, records DPDPA consent, and issues initial tokens."""
        if not req.terms_consent:
            raise ValidationException(
                "Mandatory consent to Terms of Service & Privacy Notice is required."
            )

        # Check existing user by email
        existing_res = await db.execute(select(User).where(User.email == req.email.lower()))
        if existing_res.scalar_one_or_none():
            raise ValidationException("An account with this email address already exists.")

        # Create user with Argon2id hash
        hashed_pwd = hash_password(req.password)
        user = User(
            email=req.email.lower(),
            phone_number=req.phone_number,
            hashed_password=hashed_pwd,
            role="user",
            is_active=True,
            is_verified=False,
        )
        db.add(user)
        await db.flush()  # Populates user.id

        # Create profile
        profile = UserProfile(
            user_id=user.id,
            full_name=req.full_name,
            preferred_language=req.preferred_language,
        )
        db.add(profile)

        # Record immutable DPDPA consent records
        consent_terms = ConsentRecord(
            user_id=user.id,
            consent_type="terms_and_privacy",
            version="v1.0",
            granted=True,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(consent_terms)

        if req.location_consent:
            consent_location = ConsentRecord(
                user_id=user.id,
                consent_type="location_sharing",
                version="v1.0",
                granted=True,
                ip_address=ip_address,
                user_agent=user_agent,
            )
            db.add(consent_location)

        # Generate tokens and session
        raw_refresh = generate_refresh_token()
        refresh_hash = hash_token(raw_refresh)
        session_expiry = datetime.now(timezone.utc) + timedelta(
            days=settings.REFRESH_TOKEN_EXPIRE_DAYS
        )

        session = AuthSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device_name="Web Client",
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=session_expiry,
        )
        db.add(session)
        await db.commit()

        access_token = create_access_token(subject=str(user.id), role=user.role)

        logger.info(f"User registered successfully: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            role=user.role,
            full_name=profile.full_name,
        )

    @staticmethod
    async def login(
        db: AsyncSession,
        req: LoginRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Authenticates user with Argon2id, lockout protection, and issues rotating tokens."""
        now = datetime.now(timezone.utc)

        # Retrieve user with profile
        query = (
            select(User).where(User.email == req.email.lower()).options(selectinload(User.profile))
        )
        result = await db.execute(query)
        user = result.scalar_one_or_none()

        if not user:
            # Generic error to prevent user enumeration
            raise UnauthorizedException("Invalid email or password")

        # Check account lockout
        if user.locked_until and ensure_utc(user.locked_until) > now:
            remaining_mins = int((ensure_utc(user.locked_until) - now).total_seconds() / 60) + 1
            logger.warning(f"Login attempt on locked account: {user.email}")
            raise SafeHerException(
                f"Account is temporarily locked due to repeated failed attempts. Please retry in {remaining_mins} minutes.",
                error_code="ACCOUNT_LOCKED",
                status_code=423,
            )

        # Verify password
        if not verify_password(req.password, user.hashed_password):
            user.failed_login_attempts += 1
            if user.failed_login_attempts >= 10:
                user.locked_until = now + timedelta(minutes=15)
                logger.warning(f"Account locked after 10 failed attempts: {user.email}")
            await db.commit()
            raise UnauthorizedException("Invalid email or password")

        # Reset failed attempts on success
        user.failed_login_attempts = 0
        user.locked_until = None

        # Issue rotating tokens and create session
        raw_refresh = generate_refresh_token()
        refresh_hash = hash_token(raw_refresh)
        session_expiry = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        session = AuthSession(
            user_id=user.id,
            refresh_token_hash=refresh_hash,
            device_name=req.device_name or "Web Client",
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=session_expiry,
        )
        db.add(session)
        await db.commit()

        access_token = create_access_token(subject=str(user.id), role=user.role)
        full_name = user.profile.full_name if user.profile else user.email

        logger.info(f"User logged in successfully: {user.id}")

        return TokenResponse(
            access_token=access_token,
            refresh_token=raw_refresh,
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            role=user.role,
            full_name=full_name,
        )

    @staticmethod
    async def refresh_tokens(
        db: AsyncSession,
        raw_refresh_token: str,
        device_name: str | None = None,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> TokenResponse:
        """Rotates refresh token. Detects token reuse (theft) and revokes all sessions if compromised."""
        now = datetime.now(timezone.utc)
        token_hash = hash_token(raw_refresh_token)

        query = (
            select(AuthSession)
            .where(AuthSession.refresh_token_hash == token_hash)
            .options(selectinload(AuthSession.user).selectinload(User.profile))
        )
        result = await db.execute(query)
        session = result.scalar_one_or_none()

        if not session:
            raise UnauthorizedException("Invalid refresh token")

        # Theft Detection: If an already-revoked token is presented again, invalidate all sessions for that user!
        if session.is_revoked:
            logger.critical(
                f"Revoked refresh token reuse detected for user {session.user_id}! Revoking all sessions."
            )
            await db.execute(
                update(AuthSession)
                .where(AuthSession.user_id == session.user_id)
                .values(is_revoked=True)
            )
            await db.commit()
            raise UnauthorizedException(
                "Security alert: Token reuse detected. All sessions have been revoked."
            )

        # Check expiry
        if ensure_utc(session.expires_at) < now:
            session.is_revoked = True
            await db.commit()
            raise UnauthorizedException("Refresh token has expired")

        user = session.user
        if not user or not user.is_active:
            raise UnauthorizedException("User account is inactive")

        # Rotate token: revoke current session and issue a new one
        session.is_revoked = True

        new_raw_refresh = generate_refresh_token()
        new_token_hash = hash_token(new_raw_refresh)
        new_session_expiry = now + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)

        new_session = AuthSession(
            user_id=user.id,
            refresh_token_hash=new_token_hash,
            device_name=device_name or session.device_name,
            ip_address=ip_address,
            user_agent=user_agent,
            expires_at=new_session_expiry,
        )
        db.add(new_session)
        await db.commit()

        access_token = create_access_token(subject=str(user.id), role=user.role)
        full_name = user.profile.full_name if user.profile else user.email

        return TokenResponse(
            access_token=access_token,
            refresh_token=new_raw_refresh,
            expires_in_seconds=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
            user_id=user.id,
            email=user.email,
            role=user.role,
            full_name=full_name,
        )

    @staticmethod
    async def logout(db: AsyncSession, raw_refresh_token: str) -> None:
        """Revokes an active session."""
        token_hash = hash_token(raw_refresh_token)
        await db.execute(
            update(AuthSession)
            .where(AuthSession.refresh_token_hash == token_hash)
            .values(is_revoked=True)
        )
        await db.commit()

    @staticmethod
    async def revoke_all_sessions(db: AsyncSession, user_id) -> None:
        """Revokes all active sessions for a user (useful in panic / device loss scenarios)."""
        await db.execute(
            update(AuthSession).where(AuthSession.user_id == user_id).values(is_revoked=True)
        )
        await db.commit()
