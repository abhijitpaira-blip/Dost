"""
Thin client for the Speechma text-to-speech API (https://speechma.com/api/).

Mirrors the shape of services/ai/anthropic_provider.py: reads its API key
straight from the environment (services/ must not depend on backend/app/core
— see docs/ARCHITECTURE.md), raises a clear error if it's missing, and does
nothing at import time that requires the key to exist yet.
"""
from __future__ import annotations

import os

import httpx
from dotenv import load_dotenv

load_dotenv()

SPEECHMA_BASE_URL = "https://speechma.com/api/v1"


class SpeechmaError(Exception):
    """Raised for any Speechma configuration or API-call failure."""


def _api_key() -> str:
    key = os.environ.get("SPEECHMA_API_KEY", "").strip().strip('"').strip("'")
    if not key:
        raise SpeechmaError(
            "SPEECHMA_API_KEY is missing or empty in backend/.env — sign up at "
            "speechma.com, add a real key, and restart the server."
        )
    return key


async def synthesize(
    text: str,
    voice: str,
    *,
    pitch: int | None = None,
    rate: int | None = None,
    timeout: float = 30.0,
) -> bytes:
    """
    Convert `text` to speech with the given Speechma voice id. Returns raw
    MP3 bytes on success. `pitch` and `rate` are each -100..100 if given.
    """
    if not text.strip():
        raise SpeechmaError("text must not be empty")

    body: dict[str, object] = {"text": text, "voice": voice}
    if pitch is not None:
        body["pitch"] = pitch
    if rate is not None:
        body["rate"] = rate

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.post(
            f"{SPEECHMA_BASE_URL}/tts",
            headers={"X-API-Key": _api_key(), "Content-Type": "application/json"},
            json=body,
        )

    if response.status_code != 200:
        detail = response.text
        try:
            detail = response.json().get("error", detail)
        except ValueError:
            pass
        raise SpeechmaError(f"Speechma TTS request failed ({response.status_code}): {detail}")

    return response.content


async def list_voices(language: str | None = None, *, timeout: float = 15.0) -> list[dict]:
    """
    Fetch Speechma's voice catalog, optionally filtered by language (e.g.
    "Hindi", "Bengali", "English"). Use this once, interactively, to find
    real voice_id values for SPEECHMA_VOICE_* in backend/.env — see
    services/voice/__init__.py for how those env vars are read.
    """
    params = {"language": language} if language else {}

    async with httpx.AsyncClient(timeout=timeout) as client:
        response = await client.get(
            f"{SPEECHMA_BASE_URL}/voices",
            headers={"X-API-Key": _api_key()},
            params=params,
        )

    if response.status_code != 200:
        raise SpeechmaError(f"Speechma /voices request failed ({response.status_code}): {response.text}")

    return response.json()
