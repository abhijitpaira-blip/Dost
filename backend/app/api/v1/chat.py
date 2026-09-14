"""
POST /api/v1/chat — send a conversation to DOST, get a reply back.

No persistence in this phase: the frontend sends the whole message history
on every request, and nothing is written to the database. That's Phase 3
(services/memory).
"""
from fastapi import APIRouter, HTTPException

from app.api.v1.schemas.chat import ChatRequest, ChatResponse
from services.ai import ChatMessage, get_provider
from services.ai.personality import DOST_SYSTEM_PROMPT

router = APIRouter(tags=["chat"])


@router.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest) -> ChatResponse:
    if not request.messages:
        raise HTTPException(status_code=400, detail="messages must not be empty")

    provider = get_provider()
    messages = [ChatMessage(role=m.role, content=m.content) for m in request.messages]

    try:
        reply = await provider.send_message(messages, system_prompt=DOST_SYSTEM_PROMPT)
    except Exception as exc:  # noqa: BLE001 — surface as a clean 502, not a stack trace
        raise HTTPException(status_code=502, detail=f"AI provider error: {exc}") from exc

    return ChatResponse(reply=reply)
