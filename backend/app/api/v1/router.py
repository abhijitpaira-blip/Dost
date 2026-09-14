from fastapi import APIRouter

from app.api.v1 import health

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)

# Later phases register their routers here, e.g.:
# from app.api.v1 import chat, memory, voice
# api_router.include_router(chat.router)
