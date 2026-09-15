"""
services.admin — aggregate usage stats for an admin-only dashboard.

Not a stub package: compute_admin_stats() below is the whole feature —
a handful of counts (total users, total messages, messages today, active
users this week, new signups this week) read with the service-role
Supabase client. See stats.py's docstring for exactly what's counted and
why this stays deliberately small.

Access control (deciding *who* is allowed to call it) is NOT this
package's job — that lives in services.auth.get_current_admin_user_id,
checked against the ADMIN_USER_IDS allow-list. This module only computes
numbers for a caller the route has already verified is an admin.
"""
from .stats import AdminStats, compute_admin_stats

__all__ = ["AdminStats", "compute_admin_stats"]
