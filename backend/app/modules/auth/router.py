from fastapi import APIRouter, Cookie, Depends, Response
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.database import get_db
from app.core.exceptions import AppException
from app.core.security import hash_token
from app.modules.auth.dependencies import get_current_user
from app.modules.auth.schemas import LoginRequest, RegisterRequest
from app.modules.auth.service import AuthService
from app.modules.users.models import User
from app.modules.users.schemas import UserResponse

router = APIRouter(tags=["auth"])

_COOKIE = dict(httponly=True, samesite="lax", secure=settings.COOKIE_SECURE)


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(
    body: RegisterRequest,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user = await AuthService(db).register(
        email=body.email,
        password=body.password,
        first_name=body.first_name,
        last_name=body.last_name,
    )
    return UserResponse.model_validate(user)


@router.post("/login", response_model=UserResponse)
async def login(
    body: LoginRequest,
    response: Response,
    db: AsyncSession = Depends(get_db),
) -> UserResponse:
    user, access_token, refresh_token = await AuthService(db).login(
        email=body.email, password=body.password
    )
    response.set_cookie(
        "access_token", access_token,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/api", **_COOKIE,
    )
    response.set_cookie(
        "refresh_token", refresh_token,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, path="/api/v1/auth/refresh", **_COOKIE,
    )
    return UserResponse.model_validate(user)


@router.post("/logout", status_code=204)
async def logout(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> None:
    if refresh_token:
        await AuthService(db).logout(hash_token(refresh_token))
    response.delete_cookie("access_token", path="/api")
    response.delete_cookie("refresh_token", path="/api/v1/auth/refresh")


@router.post("/refresh", response_model=UserResponse)
async def refresh(
    response: Response,
    db: AsyncSession = Depends(get_db),
    refresh_token: str | None = Cookie(default=None),
) -> UserResponse:
    if not refresh_token:
        raise AppException(
            code="NO_REFRESH_TOKEN", message="No refresh token provided.", status_code=401
        )
    user, new_access, new_refresh = await AuthService(db).refresh(refresh_token)
    response.set_cookie(
        "access_token", new_access,
        max_age=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60, path="/api", **_COOKIE,
    )
    response.set_cookie(
        "refresh_token", new_refresh,
        max_age=settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400, path="/api/v1/auth/refresh", **_COOKIE,
    )
    return UserResponse.model_validate(user)


@router.get("/me", response_model=UserResponse)
async def me(current_user: User = Depends(get_current_user)) -> UserResponse:
    return UserResponse.model_validate(current_user)
