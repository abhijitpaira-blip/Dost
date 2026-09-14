"""
services.memory.store — persists chat turns to public.messages
(database/migrations/0003_messages.sql) and reads them back.

Reads SUPABASE_URL / SUPABASE_SERVICE_ROLE_KEY directly from the
environment rather than importing backend/app/core/config: services/ must
not depend on backend/ (see docs/ARCHITECTURE.md, and the same pattern in
services/auth/verify.py and services/voice/speechma_client.py). Both
processes load the same .env, so the values are available either way.

Uses the service-role key because this only ever runs server-side, behind
backend/app/api/v1/chat.py having already resolved *who* is calling via
services.auth.get_current_user_id_optional — by the time save_turn() is
called, auth_user_id has already been verified from the caller's Supabase
JWT, not taken from anything client-supplied.
"""
from __future__ import annotations

import os
from functools import lru_cache

from supabase import Client, create_client


class MemoryError(Exception):
    """Raised when a chat turn can't be saved or loaded."""


@lru_cache
def _client() -> Client | None:
    url = os.environ.get("SUPABASE_URL", "").strip()
    key = os.environ.get("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    if not url or not key:
        return None
    return create_client(url, key)


def save_turn(auth_user_id: str, user_content: str, assistant_content: str) -> None:
    """
    Persists one exchange — the user's latest message and DOST's reply —
    as two rows in public.messages.

    Silently a no-op if Supabase isn't configured (e.g. local dev/tests
    with no .env) — chat still works, it just isn't remembered, matching
    how backend/app/core/supabase.py's get_supabase() degrades. Callers
    that DO have Supabase configured but hit a real error get a
    MemoryError, which backend/app/api/v1/chat.py catches so a save
    failure never breaks the (already-generated) reply.
    """
    client = _client()
    if client is None:
        return

    rows = [
        {"auth_user_id": auth_user_id, "role": "user", "content": user_content},
        {"auth_user_id": auth_user_id, "role": "assistant", "content": assistant_content},
    ]
    try:
        client.table("messages").insert(rows).execute()
    except Exception as exc:  # noqa: BLE001 — surfaced as MemoryError, never a raw SDK exception
        raise MemoryError(f"Could not save chat turn: {exc}") from exc


def load_history(auth_user_id: str, limit: int = 50) -> list[dict[str, str]]:
    """
    Returns this user's most recent `limit` messages, oldest first, as
    [{"role": "user" | "assistant", "content": str}, ...] - the shape
    services.ai.ChatMessage expects. Returns [] if Supabase isn't
    configured. Not currently called from any route (the frontend reads
    public.messages directly, the same way it already reads profiles -
    see frontend/src/lib/chat/useChatHistory.ts) - kept here as the
    server-side equivalent for whenever a backend caller needs it
    (e.g. a future endpoint that rebuilds context from the DB instead of
    trusting the client-supplied history).
    """
    client = _client()
    if client is None:
        return []

    try:
        result = (
            client.table("messages")
            .select("role, content")
            .eq("auth_user_id", auth_user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
    except Exception as exc:  # noqa: BLE001
        raise MemoryError(f"Could not load chat history: {exc}") from exc

    rows = result.data or []
    return list(reversed(rows))
