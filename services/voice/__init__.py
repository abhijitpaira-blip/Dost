"""
services.voice — Speechma text-to-speech integration.

Anything that turns DOST's text reply into audio goes through
`synthesize()` and `voice_id_for_language()` here. The Speechma API key
stays server-side (see speechma_client.py) — the frontend only ever
receives audio back from `POST /api/v1/voice/speak`
(backend/app/api/v1/voice.py), never the key itself.

Speech-to-text (the user's side of the conversation) is NOT handled here:
the frontend uses the browser's built-in Web Speech API
(SpeechRecognition) for now, since it's free and needs no backend round
trip. That only works in Chromium-based browsers — swapping in a
server-side STT provider (e.g. Whisper) for broader/mobile support is a
later-phase decision, not blocking this one.
"""
from .language_voices import voice_id_for_language
from .speechma_client import SpeechmaError, list_voices, synthesize

__all__ = ["SpeechmaError", "synthesize", "list_voices", "voice_id_for_language"]
