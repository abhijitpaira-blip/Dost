from typing import Optional

from pydantic import BaseModel, Field


class SpeakRequest(BaseModel):
    text: str
    # Matches the three languages services/ai/prompts/core.md supports.
    # Ignored when `voice` is given directly.
    language: str = "english"
    voice: Optional[str] = None
    pitch: Optional[int] = Field(default=None, ge=-100, le=100)
    rate: Optional[int] = Field(default=None, ge=-100, le=100)
