"""
services.ai — provider-agnostic AI layer.

Anything that talks to an LLM goes through `get_provider()`. Swapping
Anthropic <-> OpenAI, or adding a third provider later, never touches the
backend routes or the frontend — only this package.

`build_system_prompt` (in `prompt_loader.py`) assembles DOST's per-turn
system prompt from `prompts/core.md` + the caller's age band, superseding
the flat `DOST_SYSTEM_PROMPT` in `personality.py` once a request knows the
user's age — see prompt_loader.py's docstring and
`backend/app/api/v1/chat.py` for how the two are used together.
"""
from .base import AIProvider, ChatMessage
from .prompt_loader import PromptUser, UnknownAgeBandError, build_system_prompt
from .provider import get_provider

__all__ = [
    "AIProvider",
    "ChatMessage",
    "get_provider",
    "PromptUser",
    "UnknownAgeBandError",
    "build_system_prompt",
]
