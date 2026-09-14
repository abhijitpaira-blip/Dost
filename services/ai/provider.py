"""
Picks the active provider from AI_PROVIDER ("anthropic" | "openai"),
defaulting to anthropic. This is the only place that knows both providers
exist — everything else just calls the AIProvider interface.
"""
from __future__ import annotations

import os
from functools import lru_cache

from dotenv import load_dotenv

from .base import AIProvider

# services/ai reads API keys straight from the process environment (see
# docs/ARCHITECTURE.md — services/ must not depend on backend/app/core), so
# it has to load backend/.env itself rather than relying on anything in
# app.core.config to have done it. load_dotenv() finds the nearest .env by
# walking up from the current working directory (backend/, where uvicorn is
# run from) and does nothing if the variable is already set some other way.
load_dotenv()


@lru_cache
def get_provider() -> AIProvider:
    provider_name = os.environ.get("AI_PROVIDER", "anthropic").lower()

    if provider_name == "anthropic":
        from .anthropic_provider import AnthropicProvider

        return AnthropicProvider()

    if provider_name == "openai":
        from .openai_provider import OpenAIProvider

        return OpenAIProvider()

    raise ValueError(f"Unknown AI_PROVIDER: {provider_name!r} (expected 'anthropic' or 'openai')")

