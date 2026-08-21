import uuid

import jwt
from fastapi import Cookie, Depends

from app.core.database import get_db, AsyncSession
from app.core.exceptions import AppException
from app.core.security import decode_access_token
from app.modules.users.models import User, UserRole
from app.modules.users.repository import UserRepository


async def get_current_user(
    db: AsyncSession = Depends(get_db),
    access_token: str | None = Cookie(default=None),
) -> User:
    if not access_token:
        raise AppException(
            code="NOT_AUTHENTICATED", message="Authentication required.", status_code=401
        )
    try:
        payload = decode_access_token(access_token)
        user_id = uuid.UUID(payload["sub"])
    except (jwt.ExpiredSignatureError, jwt.InvalidTokenError, KeyError, ValueError):
        raise AppException(
            code="INVALID_TOKEN", message="Invalid or expired token.", status_code=401
        )

    user = await UserRepository(db).get_by_id(user_id)
    if not user or not user.is_active:
        raise AppException(
            code="USER_NOT_FOUND", message="User not found or inactive.", status_code=401
        )
    return user


async def require_admin(current_user: User = Depends(get_current_user)) -> User:
    if current_user.role != UserRole.ADMIN:
        raise AppException(
            code="ACCESS_DENIED", message="Admin access required.", status_code=403
        )
    return current_user
