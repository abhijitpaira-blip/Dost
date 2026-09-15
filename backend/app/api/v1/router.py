from fastapi import APIRouter

from app.api.v1 import admin, chat, health, voice

api_router = APIRouter(prefix="/api/v1")
api_router.include_router(health.router)
api_router.include_router(chat.router)
api_router.include_router(voice.router)
api_router.include_router(admin.router)

# Chat memory (Phase 3) doesn't have its own router — persistence is
# wired directly into chat.py's /chat route (services.memory.save_turn),
# and history is read straight from Supabase by the frontend, the same
# way profiles are. See services/memory/store.py.
#
# Later phases still register their own routers here as needed, e.g.:
# from app.api.v1 import communication
# api_router.include_router(communication.router)
