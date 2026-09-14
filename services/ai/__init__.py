"""
services.ai — provider-agnostic AI layer.

Anything that talks to an LLM goes through `get_provider()`. Swapping
Anthropic <-> OpenAI, or adding a third provider later, never touches the
backend routes or the frontend — only this package.
"""
from .base import AIProvider, ChatMessage
from .provider import get_provider

__all__ = ["AIProvider", "ChatMessage", "get_provider"]
