from fastapi import APIRouter

from app.core.config import get_settings
from app.core.supabase import get_supabase

router = APIRouter(tags=["health"])


@router.get("/health")
def health_check() -> dict:
    settings = get_settings()
    return {
        "status": "ok",
        "environment": settings.environment,
        "supabase_configured": settings.supabase_configured,
        "supabase_reachable": get_supabase() is not None,
    }
