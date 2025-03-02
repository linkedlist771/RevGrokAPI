from fastapi import APIRouter

from revgrokapi.openai_api.openai_api_router import router as openai_api_router
from revgrokapi.routers.cookie.router import router as cookie_router
from revgrokapi.routers.health.router import router as health_router

router = APIRouter(prefix="/api/v1")
router.include_router(cookie_router, prefix="/cookie", tags=["cookie"])
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(openai_api_router, prefix="/openai", tags=["openai"])
