from typing import List

from pydantic import BaseModel, Field


class ChatRequestMessage(BaseModel):
    role: str = Field(pattern="^(user|assistant)$")
    content: str


class ChatRequest(BaseModel):
    messages: List[ChatRequestMessage]


class ChatResponse(BaseModel):
    reply: str
