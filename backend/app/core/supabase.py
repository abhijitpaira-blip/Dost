"""
Server-side Supabase client, built from the service-role key.
This client bypasses Row Level Security — it must never be exposed to the
frontend and must only be used behind an endpoint that has already
authenticated the caller (Phase 2+: verifying the user's Supabase JWT).
"""
from __future__ import annotations

from functools import lru_cache

from supabase import Client, create_client

from app.core.config import get_settings


@lru_cache
def get_supabase() -> Client | None:
    settings = get_settings()
    if not settings.supabase_configured:
        return None
    return create_client(settings.supabase_url, settings.supabase_service_role_key)
