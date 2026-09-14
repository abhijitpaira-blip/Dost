"""
Maps DOST's three supported languages (see services/ai/prompts/core.md §2)
to a Speechma voice_id, via environment variables — because Speechma's
actual voice ids for Hindi/Bengali/English aren't knowable ahead of time
(the API has 580+ voices across 60+ languages, and picking the right one
is a product/voice decision, not a code one).

Setup (one-time): with a real SPEECHMA_API_KEY in backend/.env, call
`services.voice.speechma_client.list_voices(language="Hindi")` (etc.) to
see the available voice ids, pick the ones that sound right, and set them
below in backend/.env. See backend/.env.example.
"""
from __future__ import annotations

import os

from .speechma_client import SpeechmaError

_LANGUAGE_ENV_VARS = {
    "english": "SPEECHMA_VOICE_ENGLISH",
    "hindi": "SPEECHMA_VOICE_HINDI",
    "bengali": "SPEECHMA_VOICE_BENGALI",
}

_DEFAULT_VOICE_ENV = "SPEECHMA_VOICE_DEFAULT"


def voice_id_for_language(language: str) -> str:
    """
    Resolve a Speechma voice_id for one of DOST's languages. Falls back to
    SPEECHMA_VOICE_DEFAULT if a language-specific one isn't set, and raises
    SpeechmaError with setup instructions if neither is configured.
    """
    normalized = language.strip().lower()
    env_var = _LANGUAGE_ENV_VARS.get(normalized)

    voice = (os.environ.get(env_var, "").strip() if env_var else "") or os.environ.get(
        _DEFAULT_VOICE_ENV, ""
    ).strip()

    if not voice:
        known = ", ".join(sorted(_LANGUAGE_ENV_VARS))
        raise SpeechmaError(
            f"No Speechma voice configured for language={language!r}. Set "
            f"{env_var or '(unknown language)'} or {_DEFAULT_VOICE_ENV} in backend/.env "
            f"(supported languages: {known}) — see services/voice/language_voices.py."
        )

    return voice
