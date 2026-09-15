from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.admin.stats import compute_admin_stats


class FakeResult:
    def __init__(self, data=None, count=None):
        self.data = data
        self.count = count


class FakeQuery:
    """Records every chained call and returns a pre-set FakeResult from
    execute() — enough to exercise compute_admin_stats without a real
    Supabase project. Mirrors tests/services/test_memory_store.py's
    FakeQuery pattern."""

    calls: list[tuple[str, str, tuple, dict]] = []
    # One canned result per table, keyed by table name — compute_admin_stats
    # queries both "profiles" and "messages" in the same run, so a single
    # shared result (as test_memory_store.py uses) isn't enough here.
    results: dict[str, list[FakeResult]] = {}

    def __init__(self, table_name: str):
        self.table_name = table_name

    def _record(self, name, *args, **kwargs):
        FakeQuery.calls.append((self.table_name, name, args, kwargs))
        return self

    def select(self, *columns, count=None, head=False):
        return self._record("select", columns, count=count, head=head)

    def gte(self, field, value):
        return self._record("gte", field, value)

    def execute(self):
        self._record("execute")
        queue = FakeQuery.results.get(self.table_name, [])
        if not queue:
            return FakeResult()
        return queue.pop(0)


class FakeSupabaseClient:
    def table(self, name):
        return FakeQuery(name)


def _reset(profiles_results, messages_results):
    FakeQuery.calls = []
    FakeQuery.results = {"profiles": list(profiles_results), "messages": list(messages_results)}


def test_compute_admin_stats_returns_all_five_numbers():
    # Order of execute() calls inside compute_admin_stats, per table:
    # profiles -> [total_users, new_signups_7d], messages -> [total_messages,
    # messages_today, active_users_7d (a row-returning query, not a count)].
    _reset(
        profiles_results=[FakeResult(count=42), FakeResult(count=3)],
        messages_results=[
            FakeResult(count=500),
            FakeResult(count=12),
            FakeResult(data=[{"auth_user_id": "u1"}, {"auth_user_id": "u2"}, {"auth_user_id": "u1"}]),
        ],
    )

    stats = compute_admin_stats(FakeSupabaseClient(), now=datetime(2026, 9, 15, tzinfo=timezone.utc))

    assert stats == {
        "total_users": 42,
        "total_messages": 500,
        "messages_today": 12,
        "active_users_7d": 2,  # de-duplicated: u1 appears twice
        "new_signups_7d": 3,
    }


def test_compute_admin_stats_treats_none_count_as_zero():
    _reset(
        profiles_results=[FakeResult(count=None), FakeResult(count=None)],
        messages_results=[FakeResult(count=None), FakeResult(count=None), FakeResult(data=None)],
    )

    stats = compute_admin_stats(FakeSupabaseClient(), now=datetime(2026, 9, 15, tzinfo=timezone.utc))

    assert stats == {
        "total_users": 0,
        "total_messages": 0,
        "messages_today": 0,
        "active_users_7d": 0,
        "new_signups_7d": 0,
    }


def test_compute_admin_stats_filters_messages_today_and_signups_by_gte():
    _reset(
        profiles_results=[FakeResult(count=1), FakeResult(count=0)],
        messages_results=[FakeResult(count=1), FakeResult(count=0), FakeResult(data=[])],
    )

    compute_admin_stats(FakeSupabaseClient(), now=datetime(2026, 9, 15, 10, 30, tzinfo=timezone.utc))

    gte_calls = [c for c in FakeQuery.calls if c[1] == "gte"]
    # profiles.gte("created_at", <7 days ago>) and messages.gte("created_at", <today start>)
    assert ("profiles", "gte", ("created_at", "2026-09-08T10:30:00+00:00"), {}) in gte_calls
    assert ("messages", "gte", ("created_at", "2026-09-15T00:00:00+00:00"), {}) in gte_calls
