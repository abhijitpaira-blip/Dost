from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi.testclient import TestClient

from app.main import app
from services.voice import SpeechmaError

client = TestClient(app)


async def _fake_synthesize(text: str, voice: str, *, pitch=None, rate=None) -> bytes:
    return f"AUDIO({voice}:{text})".encode()


async def _fake_synthesize_fails(text: str, voice: str, *, pitch=None, rate=None) -> bytes:
    raise SpeechmaError("Speechma TTS request failed (429): quota exceeded")


def test_speak_returns_mp3_audio(monkeypatch):
    monkeypatch.setattr("app.api.v1.voice.synthesize", _fake_synthesize)
    monkeypatch.setattr("app.api.v1.voice.voice_id_for_language", lambda language: "voice-en-1")

    response = client.post("/api/v1/voice/speak", json={"text": "Hi DOST", "language": "english"})

    assert response.status_code == 200
    assert response.headers["content-type"] == "audio/mpeg"
    assert response.content == b"AUDIO(voice-en-1:Hi DOST)"


def test_speak_uses_explicit_voice_over_language(monkeypatch):
    monkeypatch.setattr("app.api.v1.voice.synthesize", _fake_synthesize)
    monkeypatch.setattr(
        "app.api.v1.voice.voice_id_for_language",
        lambda language: (_ for _ in ()).throw(AssertionError("should not resolve by language")),
    )

    response = client.post(
        "/api/v1/voice/speak",
        json={"text": "Hi DOST", "voice": "voice-explicit"},
    )

    assert response.status_code == 200
    assert response.content == b"AUDIO(voice-explicit:Hi DOST)"


def test_speak_rejects_empty_text():
    response = client.post("/api/v1/voice/speak", json={"text": "   "})
    assert response.status_code == 400


def test_speak_returns_502_on_speechma_error(monkeypatch):
    monkeypatch.setattr("app.api.v1.voice.synthesize", _fake_synthesize_fails)
    monkeypatch.setattr("app.api.v1.voice.voice_id_for_language", lambda language: "voice-en-1")

    response = client.post("/api/v1/voice/speak", json={"text": "Hi DOST"})

    assert response.status_code == 502
    assert "quota exceeded" in response.json()["detail"]
