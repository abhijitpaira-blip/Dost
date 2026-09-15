from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "backend"))

from fastapi.testclient import TestClient
from jose import jwt

from app.main import app

TEST_JWT_SECRET = "test-jwt-secret"
ADMIN_ID = "admin-user-1"
NON_ADMIN_ID = "regular-user-1"


def _bearer_token(user_id: str) -> str:
    token = jwt.encode({"sub": user_id}, TEST_JWT_SECRET, algorithm="HS256")
    return f"Bearer {token}"


class FakeAdminSupabaseClient:
    """Stands in for backend/app/core/supabase.get_supabase()'s return
    value — only ever reached once get_current_admin_user_id has already
    let a request through, so this doesn't need to simulate real data,
    just something compute_admin_stats can run against without erroring."""

    class _Query:
        def select(self, *a, **kw):
            return self

        def gte(self, *a, **kw):
            return self

        def execute(self):
            return type("Result", (), {"data": [], "count": 0})()

    def table(self, name):
        return self._Query()


client = TestClient(app)


def test_admin_stats_requires_auth_header():
    app.dependency_overrides = {}
    response = client.get("/api/v1/admin/stats")
    assert response.status_code == 401


def test_admin_stats_rejects_a_valid_but_non_admin_user(monkeypatch):
    app.dependency_overrides = {}
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("services.auth.verify.ADMIN_USER_IDS", ADMIN_ID)

    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": _bearer_token(NON_ADMIN_ID)},
    )

    assert response.status_code == 403


def test_admin_stats_returns_data_for_an_allow_listed_admin(monkeypatch):
    app.dependency_overrides = {}
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("services.auth.verify.ADMIN_USER_IDS", ADMIN_ID)
    monkeypatch.setattr("app.api.v1.admin.get_supabase", lambda: FakeAdminSupabaseClient())

    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": _bearer_token(ADMIN_ID)},
    )

    assert response.status_code == 200
    body = response.json()
    assert set(body.keys()) == {
        "total_users",
        "total_messages",
        "messages_today",
        "active_users_7d",
        "new_signups_7d",
    }


def test_admin_stats_accepts_any_id_in_a_multi_admin_allow_list(monkeypatch):
    app.dependency_overrides = {}
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("services.auth.verify.ADMIN_USER_IDS", f"{ADMIN_ID}, some-other-admin")
    monkeypatch.setattr("app.api.v1.admin.get_supabase", lambda: FakeAdminSupabaseClient())

    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": _bearer_token(ADMIN_ID)},
    )

    assert response.status_code == 200


def test_admin_stats_returns_503_when_supabase_not_configured(monkeypatch):
    app.dependency_overrides = {}
    monkeypatch.setattr("services.auth.verify.SUPABASE_JWT_SECRET", TEST_JWT_SECRET)
    monkeypatch.setattr("services.auth.verify.ADMIN_USER_IDS", ADMIN_ID)
    monkeypatch.setattr("app.api.v1.admin.get_supabase", lambda: None)

    response = client.get(
        "/api/v1/admin/stats",
        headers={"Authorization": _bearer_token(ADMIN_ID)},
    )

    assert response.status_code == 503
