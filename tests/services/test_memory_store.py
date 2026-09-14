from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from services.memory import store
from services.memory.store import MemoryError, load_history, save_turn


class FakeResult:
    def __init__(self, data):
        self.data = data


class FakeQuery:
    """Records every chained call (insert/select/eq/order/limit) and
    returns a pre-set FakeResult from execute() — enough to exercise
    store.py without a real Supabase project."""

    calls: list[tuple[str, tuple, dict]] = []
    result: FakeResult = FakeResult([])
    raise_on_execute: Exception | None = None

    def __init__(self, table_name: str):
        self.table_name = table_name

    def _record(self, name, *args, **kwargs):
        FakeQuery.calls.append((name, args, kwargs))
        return self

    def insert(self, rows):
        return self._record("insert", rows)

    def select(self, columns):
        return self._record("select", columns)

    def eq(self, field, value):
        return self._record("eq", field, value)

    def order(self, field, desc=False):
        return self._record("order", field, desc=desc)

    def limit(self, n):
        return self._record("limit", n)

    def execute(self):
        self._record("execute")
        if FakeQuery.raise_on_execute is not None:
            raise FakeQuery.raise_on_execute
        return FakeQuery.result


class FakeSupabaseClient:
    def table(self, name):
        return FakeQuery(name)


@pytest.fixture(autouse=True)
def _reset(monkeypatch):
    store._client.cache_clear()
    FakeQuery.calls = []
    FakeQuery.result = FakeResult([])
    FakeQuery.raise_on_execute = None
    monkeypatch.setenv("SUPABASE_URL", "https://example.supabase.co")
    monkeypatch.setenv("SUPABASE_SERVICE_ROLE_KEY", "test-service-role-key")
    monkeypatch.setattr(store, "create_client", lambda url, key: FakeSupabaseClient())
    yield
    store._client.cache_clear()


def test_save_turn_inserts_user_and_assistant_rows():
    save_turn("user-123", "Hi DOST", "Hey, good to hear from you.")

    insert_calls = [c for c in FakeQuery.calls if c[0] == "insert"]
    assert len(insert_calls) == 1
    rows = insert_calls[0][1][0]
    assert rows == [
        {"auth_user_id": "user-123", "role": "user", "content": "Hi DOST"},
        {"auth_user_id": "user-123", "role": "assistant", "content": "Hey, good to hear from you."},
    ]


def test_save_turn_raises_memory_error_on_failure():
    FakeQuery.raise_on_execute = RuntimeError("connection refused")
    with pytest.raises(MemoryError, match="connection refused"):
        save_turn("user-123", "Hi", "Hello")


def test_save_turn_is_a_no_op_without_supabase_configured(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    store._client.cache_clear()

    save_turn("user-123", "Hi", "Hello")  # must not raise

    assert FakeQuery.calls == []


def test_load_history_returns_oldest_first():
    # Supabase returns newest-first (order(desc=True)) - load_history must
    # reverse it back to chronological order for the caller.
    FakeQuery.result = FakeResult(
        [
            {"role": "assistant", "content": "second"},
            {"role": "user", "content": "first"},
        ]
    )

    history = load_history("user-123", limit=10)

    assert history == [
        {"role": "user", "content": "first"},
        {"role": "assistant", "content": "second"},
    ]
    limit_calls = [c for c in FakeQuery.calls if c[0] == "limit"]
    assert limit_calls[0][1] == (10,)


def test_load_history_without_supabase_configured_returns_empty(monkeypatch):
    monkeypatch.delenv("SUPABASE_URL", raising=False)
    store._client.cache_clear()

    assert load_history("user-123") == []


def test_load_history_raises_memory_error_on_failure():
    FakeQuery.raise_on_execute = RuntimeError("timeout")
    with pytest.raises(MemoryError, match="timeout"):
        load_history("user-123")
