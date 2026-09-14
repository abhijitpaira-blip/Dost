"""
The interface every AI provider implements, and the message shape used
everywhere else in the codebase — routes and future services (memory,
communication coach, etc.) depend on this shape, never on a specific
provider's SDK types.
"""
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Literal

Role = Literal["user", "assistant"]


@dataclass
class ChatMessage:
    role: Role
    content: str


class AIProvider(ABC):
    """A minimal chat-completion interface. Add methods here only when a
    real feature needs them — keep this the smallest surface that works."""

    @abstractmethod
    async def send_message(
        self,
        messages: list[ChatMessage],
        system_prompt: str,
    ) -> str:
        """Send the conversation so far and return DOST's reply as plain text."""
        raise NotImplementedError
