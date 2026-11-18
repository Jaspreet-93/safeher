import uuid

from sqlalchemy import desc, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.core.errors import NotFoundException
from app.models.consent import ConsentRecord
from app.models.session import AuthSession
from app.models.user import User, UserProfile
from app.schemas.consent import ConsentCreateRequest
from app.schemas.user import UserProfileUpdate


class UserService:
    @staticmethod
    async def get_user_with_profile(db: AsyncSession, user_id: uuid.UUID) -> User:
        """Retrieves user entity with eagerly loaded profile."""
        query = select(User).where(User.id == user_id).options(selectinload(User.profile))
        result = await db.execute(query)
        user = result.scalar_one_or_none()
        if not user:
            raise NotFoundException("User not found")
        return user

    @staticmethod
    async def update_profile(
        db: AsyncSession,
        user_id: uuid.UUID,
        req: UserProfileUpdate,
    ) -> UserProfile:
        """Updates voluntary emergency and personal preferences on user profile."""
        query = select(UserProfile).where(UserProfile.user_id == user_id)
        result = await db.execute(query)
        profile = result.scalar_one_or_none()

        if not profile:
            profile = UserProfile(user_id=user_id, full_name="User")
            db.add(profile)

        update_dict = req.model_dump(exclude_unset=True)
        for key, val in update_dict.items():
            setattr(profile, key, val)

        await db.commit()
        await db.refresh(profile)
        return profile

    @staticmethod
    async def record_consent(
        db: AsyncSession,
        user_id: uuid.UUID,
        req: ConsentCreateRequest,
        ip_address: str | None = None,
        user_agent: str | None = None,
    ) -> ConsentRecord:
        """Records an auditable DPDPA consent action."""
        record = ConsentRecord(
            user_id=user_id,
            consent_type=req.consent_type,
            version=req.version,
            granted=req.granted,
            ip_address=ip_address,
            user_agent=user_agent,
        )
        db.add(record)
        await db.commit()
        await db.refresh(record)
        return record

    @staticmethod
    async def get_consent_history(
        db: AsyncSession,
        user_id: uuid.UUID,
    ) -> list[ConsentRecord]:
        """Fetches full historical audit log of privacy consents."""
        query = (
            select(ConsentRecord)
            .where(ConsentRecord.user_id == user_id)
            .order_by(desc(ConsentRecord.timestamp))
        )
        result = await db.execute(query)
        return list(result.scalars().all())

    @staticmethod
    async def deactivate_account(db: AsyncSession, user_id: uuid.UUID) -> None:
        """Initiates account deactivation, revokes all sessions, and stages for erasure."""
        user = await UserService.get_user_with_profile(db, user_id)
        user.is_active = False

        # Revoke all active sessions
        sessions_query = select(AuthSession).where(AuthSession.user_id == user_id)
        sessions_res = await db.execute(sessions_query)
        for s in sessions_res.scalars().all():
            s.is_revoked = True

        await db.commit()
