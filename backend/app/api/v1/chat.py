"""
POST /api/v1/chat — send a conversation to DOST, get a reply back.

No persistence in this phase: the frontend sends the whole message history
on every request, and nothing is written to the database. That's Phase 3
(services/memory).

System prompt selection: if the request includes `age`, we build a
per-turn, age-appropriate prompt via `build_system_prompt` (only the
matching age-band block is sent, not all of them — see
services/ai/prompt_loader.py). If `age` is omitted — the current frontend
doesn't send it yet — we fall back to the flat `DOST_SYSTEM_PROMPT` from
Phase 2, so existing callers are unaffected.
"""
from fastapi import APIRouter, HTTPException

from app.api.v1.schemas.chat import ChatRequest, ChatResponse
from services.ai import ChatMessage, PromptUser, build_system_prompt, get_provider
from services.ai.personality import DOST_SYSTEM_PROMPT

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
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    provider = get_provider()
    messages = [ChatMessage(role=m.role, content=m.content) for m in request.messages]
    system_prompt = _resolve_system_prompt(request)

    try:
        reply = await provider.send_message(messages, system_prompt=system_prompt)
    except Exception as exc:  # noqa: BLE001 — surface as a clean 502, not a stack trace
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc

    return ChatResponse(reply=reply)
