from fastapi import APIRouter
from rev_claude.api_key.api_key_router import router as api_key_router
from rev_claude.client.claude_router import router as claude_router
from rev_claude.cookie.claude_cookie_router import \
    router as claude_cookie_router
from rev_claude.device_verification.device_verification_router import \
    router as device_verification_router
from rev_claude.files.files_router import router as files_router
from rev_claude.health.health_router import router as health_router
from rev_claude.history.conversation_history_router import \
    router as conversation_history_router
from rev_claude.openai_api.openai_api_router import router as openai_api_router
from rev_claude.poe_router.poe_router import router as poe_router
from rev_claude.routes.model_routes import router as model_router
from rev_claude.status.clients_status_router import \
    router as clients_status_router
from rev_claude.user_accounts.user_accounts_router import \
    router as user_accounts_router

router = APIRouter(prefix="/api/v1")
router.include_router(claude_router, prefix="/claude", tags=["claude"])
router.include_router(api_key_router, prefix="/api_key", tags=["api_key"])
router.include_router(claude_cookie_router, prefix="/cookie", tags=["cookie"])
router.include_router(
    clients_status_router, prefix="/clients_status", tags=["clients_status"]
)
router.include_router(
    conversation_history_router,
    prefix="/conversation_history",
    tags=["conversation_history"],
)

router.include_router(
    device_verification_router,
    prefix="/device_verification",
    tags=["device_verification"],
)
router.include_router(poe_router, prefix="/poe", tags=["poe"])
router.include_router(health_router, prefix="/health", tags=["health"])
router.include_router(files_router, prefix="/files", tags=["files"])
router.include_router(openai_api_router, prefix="/openai", tags=["openai"])
router.include_router(model_router, prefix="/models", tags=["models"])
router.include_router(
    user_accounts_router, prefix="/user_accounts", tags=["user_accounts"]
)
