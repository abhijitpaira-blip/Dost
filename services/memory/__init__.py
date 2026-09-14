"""
services.memory — DOST's persisted chat history.

Phase 3: backend/app/api/v1/chat.py now saves every turn (once the caller
is identified via services.auth.get_current_user_id_optional) to
public.messages (database/migrations/0003_messages.sql) through
save_turn() below. Longer-term "memory" in the fuller sense the DOST spec
describes - distilled facts about a user, not just a raw transcript -
is still future work; this package only covers the transcript for now.
"""
from .store import MemoryError, load_history, save_turn

__all__ = ["MemoryError", "load_history", "save_turn"]
