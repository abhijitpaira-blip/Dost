from typing import List, Optional

from pydantic import BaseModel, Field


class ChatRequestMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatRequestMessage]

    # Both optional and both None by default, so a request that omits them
    # (e.g. the existing Phase 2 frontend, or test_chat.py) keeps getting
    # the flat DOST_SYSTEM_PROMPT fallback unchanged — see chat.py.
    # Once the frontend knows the user's age (post-onboarding, from the
    # profiles table), it should start sending `age` on every request.
    age: Optional[int] = Field(default=None, ge=5, le=120)
    onboarding_complete: Optional[bool] = None

    # Non-empty -> Communication Coach mode for this turn (see
    # services/ai/prompts/communication_coach.md and frontend's /coach
    # screen): the user's own description of the conversation they want
    # to practice, e.g. "asking my manager for a raise". None/omitted ->
    # ordinary companion chat, unchanged. Coach turns are NOT persisted to
    # public.messages — see chat.py's docstring for why.
    scenario: Optional[str] = Field(default=None, max_length=500)


class ChatResponse(BaseModel):
    reply: str
