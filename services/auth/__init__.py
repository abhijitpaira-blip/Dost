"""
services.auth — Supabase Auth helpers.

This is the one service package with real logic in Phase 1: verifying a
Supabase JWT sent by the frontend and resolving it to a profile row. Sign-up,
password reset, OTP and social login are all handled by Supabase Auth itself
on the frontend (see frontend/src/lib/supabase) — this package is for the
backend to trust *who* is calling it.
"""
from .verify import get_current_user_id, get_current_user_id_optional

__all__ = ["get_current_user_id", "get_current_user_id_optional"]
