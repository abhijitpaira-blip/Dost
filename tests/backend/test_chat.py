from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi.testclient import TestClient
from jose import jwt

from app.main import app
from services.ai import ChatMessage
from services.ai.personality import DOST_SYSTEM_PROMPT
from services.ai.provider import get_provider

TEST_JWT_SECRET = "test-jwt-secret"


def _bearer_token(user_id: str = "user-123") -> str:
    token = jwt.encode({"sub": user_id}, TEST_JWT_SECRET, algorithm="HS256")
    return f"Bearer {token}"


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


def test_chat_without_auth_header_does_not_save(monkeypatch):
    """No Authorization header (the shape every prior test above uses) ->
    chat still works and nothing is persisted — Phase 3 memory must not
    break any existing caller."""
    app.dependency_overrides = {}
    get_provider.cache_clear()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: FakeProvider())
    save_calls = []
    monkeypatch.setattr("app.api.v1.chat.save_turn", lambda *a, **kw: save_calls.append((a, kw)))

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}]},
    )

    assert response.status_code == 200
    assert save_calls == []


def test_chat_with_valid_auth_header_saves_the_turn(monkeypatch):
    app.dependency_overrides = {}
    get_provider.cache_clear()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    save_calls = []
    monkeypatch.setattr("app.api.v1.chat.save_turn", lambda *a, **kw: save_calls.append((a, kw)))

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}]},
        headers={"Authorization": _bearer_token("user-123")},
    )

    assert response.status_code == 200
    assert save_calls == [(("user-123", "Hi DOST", "Hey, good to hear from you."), {})]


def test_chat_with_invalid_auth_header_still_replies_without_saving(monkeypatch):
    app.dependency_overrides = {}
    get_provider.cache_clear()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    save_calls = []
    monkeypatch.setattr("app.api.v1.chat.save_turn", lambda *a, **kw: save_calls.append((a, kw)))

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}]},
        headers={"Authorization": "Bearer not-a-real-token"},
    )

    assert response.status_code == 200
    assert save_calls == []


def test_chat_save_failure_does_not_break_the_reply(monkeypatch):
    """save_turn raising MemoryError must not turn an already-generated
    reply into a 500 — see chat.py's try/except around it."""
    app.dependency_overrides = {}
    get_provider.cache_clear()
    monkeypatch.setattr("app.api.v1.chat.get_provider", lambda: FakeProvider())
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)

    from services.memory import MemoryError

    def _boom(*a, **kw):
        raise MemoryError("db is down")

    monkeypatch.setattr("app.api.v1.chat.save_turn", _boom)

    response = client.post(
        "/api/v1/chat",
        json={"messages": [{"role": "user", "content": "Hi DOST"}]},
        headers={"Authorization": _bearer_token("user-123")},
    )

    assert response.status_code == 200
    assert response.json()["reply"] == "Hey, good to hear from you."
