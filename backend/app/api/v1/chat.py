"""
POST /api/v1/chat — send a conversation to DOST, get a reply back.

Persistence (Phase 3): if the caller sends a valid Supabase access token
(`Authorization: Bearer <token>`), the latest user message and DOST's
reply are saved to public.messages via services.memory.save_turn() — see
database/migrations/0003_messages.sql. No token, or an invalid one, just
means this turn isn't remembered; the chat itself still works exactly as
before (see get_current_user_id_optional's docstring). The frontend still
sends the whole message history on every request — this endpoint doesn't
read history back from the database, it only writes to it; restoring a
past conversation on page load is a direct frontend read of
public.messages (frontend/src/lib/chat/useChatHistory.ts), the same way
profiles are read directly rather than through a backend endpoint.

System prompt selection: if the request includes `age`, we build a
per-turn, age-appropriate prompt via `build_system_prompt` (only the
matching age-band block is sent, not all of them — see
services/ai/prompt_loader.py). If `age` is omitted — the current frontend
doesn't send it yet — we fall back to the flat `DOST_SYSTEM_PROMPT` from
Phase 2, so existing callers are unaffected.

Safety net: after the AI replies, the user's own latest message is
scanned by services.safety.detect_crisis_signal() for explicit crisis
language. core.md's Section 9 already asks the AI itself to respond with
care in that situation, but prompt-following can be imperfect — this is a
deterministic backstop, not a replacement, that appends a verified
helpline footer (services.safety.CRISIS_RESOURCE_FOOTER) when it fires and
the AI's own reply didn't already include the numbers. The persisted
transcript (services.memory.save_turn) stores this final, footer-included
reply — it's what the user actually saw.
"""
from typing import Optional

from fastapi import APIRouter, Depends, HTTPException

from app.api.v1.schemas.chat import ChatRequest, ChatResponse
from services.ai import ChatMessage, PromptUser, build_system_prompt, get_provider
from services.ai.personality import DOST_SYSTEM_PROMPT
from services.auth import get_current_user_id_optional
from services.memory import MemoryError, save_turn
from services.safety import CRISIS_RESOURCE_FOOTER, detect_crisis_signal, reply_already_has_resources

router = APIRouter(tags=["chat"])


def _resolve_system_prompt(request: ChatRequest) -> str:
    if request.age is None:
        return DOST_SYSTEM_PROMPT

    user = PromptUser(
        age=request.age,
        # Age given but onboarding status not stated: assume onboarding is
        # done rather than silently reopening the onboarding flow.
        onboarding_complete=True if request.onboarding_complete is None else request.onboarding_complete,
    )
    return build_system_prompt(user)


@router.post("/chat", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    # Optional[str], not `str | None`: this file has no
    # `from __future__ import annotations`, and this repo's Python
    # predates 3.10, where FastAPI needs to resolve this exact annotation
    # to know how to inject the dependency — a bare `X | None` here raised
    # a TypeError at import time (see the same note in
    # services/auth/verify.py, and ChatRequest's `Optional[int]` above).
    auth_user_id: Optional[str] = Depends(get_current_user_id_optional),
) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    provider = get_provider()
    messages = [ChatMessage(role=m.role, content=m.content) for m in request.messages]
    system_prompt = _resolve_system_prompt(request)

    try:
        reply = await provider.send_message(messages, system_prompt=system_prompt)
    except Exception as exc:  # noqa: BLE001 — surface as a clean 502, not a stack trace
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc

    latest_user_message = request.messages[-1].content
    if detect_crisis_signal(latest_user_message) and not reply_already_has_resources(reply):
        reply = f"{reply}{CRISIS_RESOURCE_FOOTER}"

    if auth_user_id is not None:
        # Best-effort: a save failure shouldn't turn a reply DOST already
        # generated into a 500 — the user still gets their answer, it just
        # might not be remembered next time.
        try:
            save_turn(auth_user_id, latest_user_message, reply)
        except MemoryError:
            pass

    return ChatResponse(reply=reply)
