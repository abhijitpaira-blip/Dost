"""
Verifies the Supabase-issued JWT on incoming requests and returns the caller's
auth_user_id (a UUID string). This is the *only* thing that should ever be
trusted as "who is this user" — never a client-supplied name or age.

Not wired into any route yet in Phase 1 (there are no protected routes yet),
but future protected endpoints depend on `get_current_user_id`.
"""
import os
from typing import Optional

from fastapi import Header, HTTPException, status
from jose import JWTError, jwt

# Deliberately reads the environment directly instead of importing
# backend/app/core/config: `services/` must not depend on `backend/`, only
# the other way around (see docs/ARCHITECTURE.md). Both processes load the
# same .env, so the variable is available either way.
SUPABASE_JWT_SECRET = os.environ.get("SUPABASE_JWT_SECRET", "")

# Optional[str], not `str | None`: this file has no
# `from __future__ import annotations`, and this repo's Python is older
# than 3.10, where a bare `X | None` annotation raises a TypeError the
# moment the function is defined (not just when it's used) — see
# schemas/chat.py's existing `Optional[int]` for the same reason.


def get_current_user_id(authorization: str = Header(default="")) -> str:
    """
    FastAPI dependency. Expects `Authorization: Bearer <supabase-access-token>`.
    Raises 401 if the token is missing or invalid.

    NOTE: SUPABASE_JWT_SECRET is the project's Auth JWT secret (Supabase
    dashboard → Project Settings → API), NOT the service-role key. This is
    wired into an actual protected route in a later phase — no route depends
    on it yet in Phase 1.
    """
    if not authorization.startswith("Bearer "):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing bearer token")

    if not SUPABASE_JWT_SECRET:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="SUPABASE_JWT_SECRET is not configured",
        )

    # Slicing, not str.removeprefix(): that method needs Python 3.9+, and
    # this repo's Python predates that too (see the str | None notes above).
    token = authorization[len("Bearer "):].strip()

    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError as exc:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid token") from exc

    user_id = payload.get("sub")
    if not user_id:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token missing subject")

    return user_id


def get_current_user_id_optional(authorization: str = Header(default="")) -> Optional[str]:
    """
    Same verification as get_current_user_id, but returns None instead of
    raising when the header is missing or the token is invalid, rather
    than rejecting the request outright.

    First use: backend/app/api/v1/chat.py, so chat keeps working exactly
    as before (no auth at all) for any caller that doesn't send a token —
    existing tests included — while a signed-in frontend request gets its
    turn saved to services.memory. "Best effort, only when we know who's
    asking" mirrors how age/onboarding_complete are optional on
    ChatRequest, rather than a hard requirement of that endpoint.
    """
    if not authorization.startswith("Bearer ") or not SUPABASE_JWT_SECRET:
        return None

    # Slicing, not str.removeprefix(): see the comment in get_current_user_id.
    token = authorization[len("Bearer "):].strip()
    try:
        payload = jwt.decode(
            token,
            SUPABASE_JWT_SECRET,
            algorithms=["HS256"],
            options={"verify_aud": False},
        )
    except JWTError:
        return None

    user_id = payload.get("sub")
    return user_id if isinstance(user_id, str) and user_id else None
