from fastapi import APIRouter

from app.api.v1 import chat, health, voice

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(voice.router)

# Later phases register their routers here, e.g.:
# from app.api.v1 import memory
# api_router.include_router(memory.router)
