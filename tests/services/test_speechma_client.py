from __future__ import annotations

import pytest

from services.voice import speechma_client
from services.voice.speechma_client import SpeechmaError, list_voices, synthesize


class FakeResponse:
    def __init__(self, status_code: int, content: bytes = b"", json_data=None, text: str = ""):
        self.status_code = status_code
        self.content = content
        self._json_data = json_data
        self.text = text

    def json(self):
        if self._json_data is None:
            raise ValueError("no json body")
        return self._json_data


class FakeAsyncClient:
    """Stands in for httpx.AsyncClient as an async context manager, recording
    the call it was asked to make and returning a pre-set FakeResponse."""

    last_call: dict | None = None
    response: FakeResponse = FakeResponse(200, content=b"ID3fake-mp3-bytes")

    def __init__(self, *args, **kwargs):
        pass

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, *, headers=None, json=None):
        FakeAsyncClient.last_call = {"method": "post", "url": url, "headers": headers, "json": json}
        return FakeAsyncClient.response

    async def get(self, url, *, headers=None, params=None):
        FakeAsyncClient.last_call = {"method": "get", "url": url, "headers": headers, "params": params}
        return FakeAsyncClient.response


@pytest.fixture(autouse=True)
def _patch_httpx(monkeypatch):
    monkeypatch.setattr(speechma_client.httpx, "AsyncClient", FakeAsyncClient)
    monkeypatch.setenv("SPEECHMA_API_KEY", "sm_test_key")
    FakeAsyncClient.response = FakeResponse(200, content=b"ID3fake-mp3-bytes")
    yield


@pytest.mark.asyncio
async def test_synthesize_returns_audio_bytes_on_success():
    audio = await synthesize("Hello DOST", "voice-1")
    assert audio == b"ID3fake-mp3-bytes"
    assert FakeAsyncClient.last_call["json"] == {"text": "Hello DOST", "voice": "voice-1"}
    assert FakeAsyncClient.last_call["headers"]["X-API-Key"] == "sm_test_key"


@pytest.mark.asyncio
async def test_synthesize_includes_pitch_and_rate_when_given():
    await synthesize("Hi", "voice-1", pitch=10, rate=-5)
    assert FakeAsyncClient.last_call["json"] == {"text": "Hi", "voice": "voice-1", "pitch": 10, "rate": -5}


@pytest.mark.asyncio
async def test_synthesize_rejects_empty_text():
    with pytest.raises(SpeechmaError):
        await synthesize("   ", "voice-1")


@pytest.mark.asyncio
async def test_synthesize_missing_api_key_raises(monkeypatch):
    monkeypatch.delenv("SPEECHMA_API_KEY", raising=False)
    with pytest.raises(SpeechmaError, match="SPEECHMA_API_KEY"):
        await synthesize("hi", "voice-1")


@pytest.mark.asyncio
async def test_synthesize_raises_on_error_status():
    FakeAsyncClient.response = FakeResponse(429, json_data={"error": "quota exceeded"})
    with pytest.raises(SpeechmaError, match="quota exceeded"):
        await synthesize("hi", "voice-1")


@pytest.mark.asyncio
async def test_list_voices_passes_language_filter():
    FakeAsyncClient.response = FakeResponse(200, json_data=[{"voice_id": "v1", "language": "Hindi"}])
    voices = await list_voices(language="Hindi")
    assert voices == [{"voice_id": "v1", "language": "Hindi"}]
    assert FakeAsyncClient.last_call["params"] == {"language": "Hindi"}


@pytest.mark.asyncio
async def test_list_voices_raises_on_error_status():
    FakeAsyncClient.response = FakeResponse(401, text="unauthorized")
    with pytest.raises(SpeechmaError, match="401"):
        await list_voices()
