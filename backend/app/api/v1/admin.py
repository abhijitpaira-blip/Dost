"""
GET /api/v1/admin/stats — a handful of aggregate usage numbers for the
app owner (total users, total messages, messages today, active users this
week, new signups this week). See services/admin/stats.py for exactly
what's counted, and services/auth/verify.py's get_current_admin_user_id
for who's allowed to call this: the caller's Supabase JWT is verified
first (401 if missing/invalid, same as every other protected route),
then their auth_user_id is checked against the ADMIN_USER_IDS allow-list
(403 if not present) — never a client-supplied id or email.
"""
from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.schemas.admin import AdminStatsResponse
from app.core.supabase import get_supabase
from services.admin import compute_admin_stats
from services.auth import get_current_admin_user_id

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
async def stats(
    # Unused except to gate the route — see this file's docstring.
    _admin_user_id: str = Depends(get_current_admin_user_id),
) -> AdminStatsResponse:
    client = get_supabase()
    if client is None:
        raise HTTPException(status_code=503, detail="Supabase isn't configured on this server")

    return AdminStatsResponse(**compute_admin_stats(client))
