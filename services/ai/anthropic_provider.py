"""
Anthropic (Claude) implementation of AIProvider.
"""
from __future__ import annotations

import os

from anthropic import AsyncAnthropic

from .base import AIProvider, ChatMessage

DEFAULT_MODEL = "claude-sonnet-5"


class AnthropicProvider(AIProvider):
    def __init__(self, api_key: str | None = None, model: str = DEFAULT_MODEL):
        resolved_key = (api_key or os.environ.get("ANTHROPIC_API_KEY", "")).strip().strip('"').strip("'")
        if not resolved_key:
            raise RuntimeError(
                "ANTHROPIC_API_KEY is missing or empty in backend/.env — "
                "add a real key from console.anthropic.com and restart the server."
            )
        self._client = AsyncAnthropic(api_key=resolved_key)
        self._model = model

    async def send_message(self, messages: list[ChatMessage], system_prompt: str) -> str:
        response = await self._client.messages.create(
            model=self._model,
            max_tokens=1024,
            system=system_prompt,
            messages=[{"role": m.role, "content": m.content} for m in messages],
        )
        return "".join(block.text for block in response.content if block.type == "text")
