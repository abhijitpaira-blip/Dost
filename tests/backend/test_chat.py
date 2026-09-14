from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi.testclient import TestClient

from app.main import app
from services.ai import ChatMessage
from services.ai.personality import DOST_SYSTEM_PROMPT
from services.ai.provider import get_provider


class FakeProvider:
    """Records the system_prompt it was called with, so tests can assert
    on which prompt path (flat fallback vs. age-band assembly) was used."""

    def __init__(self) -> None:
        self.last_system_prompt: str | None = None

    async def send_message(self, messages: list[ChatMessage], system_prompt: str) -> str:
        self.last_system_prompt = system_prompt
        return "Hey, good to hear from you."


client = TestClient(app)


def test_chat_returns_reply(monkeypatch):
    app.dependency_overrides = {}
    get_provider.cache_clear()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: FakeProvider())

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}]},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Hey, good to hear from you."


def test_chat_rejects_empty_messages():
    response = client.post("/api/v1/chat", json={"messages": []})
    assert response.status_code == 400


def test_chat_without_age_uses_flat_fallback_prompt(monkeypatch):
    """No `age` in the request (the current frontend's shape) -> unchanged
    Phase 2 behavior: the flat DOST_SYSTEM_PROMPT constant."""
    app.dependency_overrides = {}
    get_provider.cache_clear()
    fake = FakeProvider()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: fake)

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}]},
    )

    assert response.status_code == 200
    assert fake.last_system_prompt == DOST_SYSTEM_PROMPT


def test_chat_with_age_uses_age_band_prompt(monkeypatch):
    """`age` present -> the richer, age-appropriate prompt from
    prompt_loader.build_system_prompt, not the flat constant."""
    app.dependency_overrides = {}
    get_provider.cache_clear()
    fake = FakeProvider()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: fake)

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}], "age": 11},
    )

    assert response.status_code == 200
    assert fake.last_system_prompt != DOST_SYSTEM_PROMPT
    assert "Growth Explorer" in fake.last_system_prompt  # 11-13 band
    assert "You are DOST" in fake.last_system_prompt
