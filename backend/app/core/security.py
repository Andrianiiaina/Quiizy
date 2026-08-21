import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Any

import jwt
from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

from app.core.config import settings

_ph = PasswordHasher(time_cost=2, memory_cost=65536, parallelism=2)
_ALGORITHM = "HS256"


def hash_password(password: str) -> str:
    return _ph.hash(password)


def verify_password(plain: str, hashed: str) -> bool:
    try:
        _ph.verify(hashed, plain)
        return True
    except VerifyMismatchError:
        return False
    except Exception:
        return False


def create_access_token(user_id: str, role: str) -> str:
    payload: dict[str, Any] = {
        "sub": user_id,
        "role": role,
        "exp": datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES),
        "type": "access",
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=_ALGORITHM)


def decode_access_token(token: str) -> dict[str, Any]:
    return jwt.decode(token, settings.SECRET_KEY, algorithms=[_ALGORITHM])


def generate_refresh_token() -> str:
    return secrets.token_urlsafe(64)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode()).hexdigest()
