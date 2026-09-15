"""
services.admin.stats — aggregate usage numbers for the admin-only
dashboard (backend/app/api/v1/admin.py, frontend's /admin screen).

Uses the same service-role Supabase client as services.memory.store (see
backend/app/core/supabase.py) because these are cross-user aggregate
reads that no per-user RLS policy on profiles/messages should ever need
to allow directly from the frontend — both tables' policies are scoped to
"a user may only ever see their own row" (see
database/migrations/0001_init_profiles.sql and 0003_messages.sql). The
only thing standing between this module and every user's data is the
access check in front of it — services.auth.get_current_admin_user_id,
gated by the ADMIN_USER_IDS allow-list — not anything in this file.

Deliberately a handful of simple counts, not a general analytics/BI
layer: total users, total messages, messages sent today, distinct users
active in the last 7 days, and new signups in the last 7 days. Enough to
answer "is anyone actually using this," not meant to grow into per-user
drill-down or retention cohorts without revisiting this design.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import TypedDict

from supabase import Client


class AdminStats(TypedDict):
    total_users: int
    total_messages: int
    messages_today: int
    active_users_7d: int
    new_signups_7d: int


def compute_admin_stats(client: Client, now: datetime | None = None) -> AdminStats:
    """
    Runs a handful of independent count queries against the service-role
    client and assembles them into one snapshot. `now` is injectable so
    tests don't depend on the real clock; callers should leave it unset.
    """
    now = now or datetime.now(timezone.utc)
    today_start_iso = datetime(now.year, now.month, now.day, tzinfo=timezone.utc).isoformat()
    seven_days_ago_iso = (now - timedelta(days=7)).isoformat()

    total_users = _count(client, "profiles")
    new_signups_7d = _count(client, "profiles", gte=("created_at", seven_days_ago_iso))
    total_messages = _count(client, "messages")
    messages_today = _count(client, "messages", gte=("created_at", today_start_iso))

    # Needs the actual rows (not just a count) to de-duplicate by user —
    # one person sending 50 messages in a week is still one active user.
    active_rows = (
        client.table("messages")
        .select("auth_user_id")
        .gte("created_at", seven_days_ago_iso)
        .execute()
    )
    active_users_7d = len({row["auth_user_id"] for row in (active_rows.data or [])})

    return {
        "total_users": total_users,
        "total_messages": total_messages,
        "messages_today": messages_today,
        "active_users_7d": active_users_7d,
        "new_signups_7d": new_signups_7d,
    }


def _count(client: Client, table: str, gte: tuple[str, str] | None = None) -> int:
    query = client.table(table).select("*", count="exact", head=True)
    if gte is not None:
        field, value = gte
        query = query.gte(field, value)
    result = query.execute()
    return result.count or 0
