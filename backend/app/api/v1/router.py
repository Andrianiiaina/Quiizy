from fastapi import APIRouter

api_router = APIRouter()

# Les routers des modules seront enregistrés ici au fur et à mesure :
#
# from app.modules.auth.router import router as auth_router
# api_router.include_router(auth_router, prefix="/auth", tags=["auth"])
#
# from app.modules.users.router import router as users_router
# api_router.include_router(users_router, prefix="/users", tags=["users"])


@api_router.get("/health", tags=["system"])
async def api_health() -> dict[str, str]:
    """Health check accessible depuis le frontend via /api/v1/health."""
    return {"status": "ok", "version": "0.1.0"}
