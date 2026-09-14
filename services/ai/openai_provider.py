"""
OpenAI (GPT) implementation of AIProvider. Not the active provider yet
(DOST currently runs on ANTHROPIC_API_KEY), but the same interface means
switching is a one-line env change once an OpenAI key is added.
"""
from __future__ import annotations

import os

from openai import AsyncOpenAI

from .base import AIProvider, ChatMessage

DEFAULT_MODEL = "gpt-4o"


class OpenAIProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        self._client = AsyncOpenAI(api_key=api_key or os.environ.get("OPENAI_API_KEY", ""))
        self._model = model

    async def send_message(self, messages: list[ChatMessage], system_prompt: str) -> str:
        response = await self._client.chat.completions.create(
            model=self._model,
            messages=[{"role": "system", "content": system_prompt}]
            + [{"role": m.role, "content": m.content} for m in messages],
        )
        return response.choices[0].message.content or ""
