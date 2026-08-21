import uuid
from datetime import datetime, timedelta, timezone

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import AppException
from app.core.security import (
    create_access_token,
    generate_refresh_token,
    hash_password,
    hash_token,
    verify_password,
)
from app.modules.users.models import RefreshToken, User
from app.modules.users.repository import UserRepository


class AuthService:
    def __init__(self, db: AsyncSession) -> None:
        self._db = db
        self._users = UserRepository(db)

    async def register(
        self,
        *,
        email: str,
        password: str,
        first_name: str,
        last_name: str,
    ) -> User:
        if await self._users.get_by_email(email):
            raise AppException(
                code="EMAIL_ALREADY_EXISTS",
                message="An account with this email already exists.",
                status_code=409,
            )
        user = await self._users.create(
            email=email,
            password_hash=hash_password(password),
            first_name=first_name,
            last_name=last_name,
        )
        await self._db.commit()
        return user

    async def login(self, *, email: str, password: str) -> tuple[User, str, str]:
        user = await self._users.get_by_email(email)
        # Vérifie toujours un hash pour éviter l'énumération par timing
        hash_to_check = user.password_hash if user else "$argon2id$v=19$m=65536,t=2,p=2$invalid"
        if not user or not verify_password(password, hash_to_check):
            raise AppException(
                code="INVALID_CREDENTIALS",
                message="Invalid email or password.",
                status_code=401,
            )
        if not user.is_active:
            raise AppException(
                code="ACCOUNT_DISABLED",
                message="This account has been disabled.",
                status_code=403,
            )
        access_token = create_access_token(str(user.id), user.role.value)
        raw_refresh, _ = await self._create_refresh_token(user.id)
        await self._db.commit()
        return user, access_token, raw_refresh

    async def logout(self, token_hash: str) -> None:
        result = await self._db.execute(
            select(RefreshToken).where(
                RefreshToken.token_hash == token_hash,
                RefreshToken.revoked_at.is_(None),
            )
        )
        rt = result.scalar_one_or_none()
        if rt:
            rt.revoked_at = datetime.now(timezone.utc)
            await self._db.commit()

    async def refresh(self, raw_refresh_token: str) -> tuple[User, str, str]:
        token_hash = hash_token(raw_refresh_token)
        result = await self._db.execute(
            select(RefreshToken).where(RefreshToken.token_hash == token_hash)
        )
        rt = result.scalar_one_or_none()

        if not rt:
            raise AppException(
                code="INVALID_REFRESH_TOKEN",
                message="Invalid or expired refresh token.",
                status_code=401,
            )

        # Détection de réutilisation : révoque toutes les sessions de l'utilisateur
        if rt.revoked_at is not None:
            await self._db.execute(
                update(RefreshToken)
                .where(
                    RefreshToken.user_id == rt.user_id,
                    RefreshToken.revoked_at.is_(None),
                )
                .values(revoked_at=datetime.now(timezone.utc))
            )
            await self._db.commit()
            raise AppException(
                code="REFRESH_TOKEN_REUSE",
                message="Token reuse detected. All sessions have been revoked.",
                status_code=401,
            )

        if rt.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
            raise AppException(
                code="REFRESH_TOKEN_EXPIRED",
                message="Session expired. Please log in again.",
                status_code=401,
            )

        user = await self._users.get_by_id(rt.user_id)
        if not user or not user.is_active:
            raise AppException(
                code="ACCOUNT_DISABLED",
                message="This account has been disabled.",
                status_code=403,
            )

        rt.revoked_at = datetime.now(timezone.utc)
        new_access = create_access_token(str(user.id), user.role.value)
        raw_new_refresh, _ = await self._create_refresh_token(user.id)
        await self._db.commit()
        return user, new_access, raw_new_refresh

    async def _create_refresh_token(self, user_id: uuid.UUID) -> tuple[str, str]:
        raw = generate_refresh_token()
        token_hash = hash_token(raw)
        self._db.add(
            RefreshToken(
                user_id=user_id,
                token_hash=token_hash,
                expires_at=datetime.now(timezone.utc)
                + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS),
            )
        )
        await self._db.flush()
        return raw, token_hash
