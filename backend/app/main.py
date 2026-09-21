import logging
import time
from collections import defaultdict
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request as StarletteRequest
from starlette.responses import JSONResponse as StarletteJSONResponse

from app.api.v1.router import api_router
from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.logging import setup_logging


class _SecurityHeadersMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: StarletteRequest, call_next):  # type: ignore[override]
        response = await call_next(request)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        if settings.COOKIE_SECURE:
            response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        return response


class _LoginRateLimitMiddleware(BaseHTTPMiddleware):
    """In-memory brute-force protection for POST /api/v1/auth/login."""

    def __init__(self, app) -> None:  # type: ignore[override]
        super().__init__(app)
        self._attempts: dict[str, list[float]] = defaultdict(list)

    async def dispatch(self, request: StarletteRequest, call_next):  # type: ignore[override]
        if request.method == "POST" and request.url.path == "/api/v1/auth/login":
            ip = (request.client.host if request.client else None) or "unknown"
            now = time.time()
            cutoff = now - settings.LOGIN_RATE_LIMIT_WINDOW_SECONDS
            self._attempts[ip] = [t for t in self._attempts[ip] if t > cutoff]
            if len(self._attempts[ip]) >= settings.LOGIN_RATE_LIMIT_MAX_ATTEMPTS:
                return StarletteJSONResponse(
                    status_code=429,
                    content={"code": "RATE_LIMIT_EXCEEDED", "message": "Too many login attempts. Please try again later."},
                )
            self._attempts[ip].append(now)
        return await call_next(request)

setup_logging(debug=settings.DEBUG)
logger = logging.getLogger("lms")


@asynccontextmanager
async def lifespan(app: FastAPI) -> AsyncGenerator[None, None]:
    logger.info(
        "LMS backend starting — debug=%s", settings.DEBUG
    )
    yield
    logger.info("LMS backend shutting down")


app = FastAPI(
    title="LMS API",
    version="0.1.0",
    docs_url="/api/docs",
    redoc_url="/api/redoc",
    openapi_url="/api/openapi.json",
    lifespan=lifespan,
)

app.add_middleware(_LoginRateLimitMiddleware)
app.add_middleware(_SecurityHeadersMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.add_exception_handler(AppException, app_exception_handler)  # type: ignore[arg-type]

app.include_router(api_router, prefix="/api/v1")


@app.get("/health", tags=["system"], include_in_schema=False)
async def health() -> dict[str, str]:
    """Used by Docker healthcheck — returns 200 if the process is alive."""
    return {"status": "ok", "version": "0.1.0"}
