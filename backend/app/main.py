import logging
from contextlib import asynccontextmanager
from collections.abc import AsyncGenerator

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.core.config import settings
from app.core.exceptions import AppException, app_exception_handler
from app.core.logging import setup_logging
from app.api.v1.router import api_router

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
