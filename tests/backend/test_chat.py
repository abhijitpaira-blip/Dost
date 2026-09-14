from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi.testclient import TestClient

from app.main import app
from services.ai import ChatMessage
from services.ai.provider import get_provider


class FakeProvider:
    async def send_message(self, messages: list[ChatMessage], system_prompt: str) -> str:
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
