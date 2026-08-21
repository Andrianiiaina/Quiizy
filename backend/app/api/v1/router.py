from fastapi import APIRouter

from app.modules.auth.router import router as auth_router
from app.modules.categories.router import router as categories_router
from app.modules.courses.router import router as courses_router

api_router = APIRouter()
api_router.include_router(auth_router, prefix="/auth")
api_router.include_router(categories_router, prefix="/categories")
api_router.include_router(courses_router, prefix="/courses")

# Les prochains routers seront ajoutés ici.


@api_router.get("/health", tags=["system"])
async def api_health() -> dict[str, str]:
    """Health check accessible depuis le frontend via /api/v1/health."""
    return {"status": "ok", "version": "0.1.0"}
