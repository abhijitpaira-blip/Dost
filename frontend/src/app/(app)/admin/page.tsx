import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

// (app)/layout.tsx already requires a signed-in, onboarded user to reach
// any route in this group — this page adds a second, admin-only gate on
// top of that: the backend checks the caller's auth_user_id against
// ADMIN_USER_IDS (see services/auth/verify.py) and this page just renders
// whatever it says (200 with real numbers, or 403). There's no link to
// this page anywhere in the app's nav on purpose — it's for the owner to
// open directly, not a feature the rest of the family should stumble into.

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

interface AdminStats {
  total_users: number;
  total_messages: number;
  messages_today: number;
  active_users_7d: number;
  new_signups_7d: number;
}

const STAT_LABELS: Array<[key: keyof AdminStats, label: string]> = [
  ["total_users", "Total users"],
  ["total_messages", "Total messages"],
  ["messages_today", "Messages today"],
  ["active_users_7d", "Active users (7d)"],
  ["new_signups_7d", "New signups (7d)"],
];

export default async function AdminPage() {
  const supabase = createClient();
  const {
    data: { session },
  } = await supabase.auth.getSession();

  if (!session) {
    redirect("/login");
  }

  let stats: AdminStats | null = null;
  let errorMessage: string | null = null;

  try {
    const res = await fetch(`${API_URL}/api/v1/admin/stats`, {
      headers: { Authorization: `Bearer ${session.access_token}` },
      cache: "no-store",
    });

    if (res.status === 403) {
      errorMessage = "This account doesn't have admin access.";
    } else if (!res.ok) {
      errorMessage = `Couldn't load admin stats (${res.status}).`;
    } else {
      stats = await res.json();
    }
  } catch {
    errorMessage = "Couldn't reach the backend just now — check it's running and try again.";
  }

  return (
    <div className="space-y-8">
      <div className="space-y-1">
        <p className="font-body text-sm text-clay-500">DOST</p>
        <h1 className="font-display text-2xl text-ink-900">Admin</h1>
      </div>

      {errorMessage && (
        <p role="alert" className="font-body text-sm text-clay-500">
          {errorMessage}
        </p>
      )}

      {stats && (
        <div className="grid grid-cols-2 gap-3">
          {STAT_LABELS.map(([key, label]) => (
            <div key={key} className="rounded-2xl bg-linen-100 px-4 py-4">
              <p className="font-display text-2xl text-ink-900">{stats![key]}</p>
              <p className="font-body text-xs text-ink-600">{label}</p>
            </div>
          ))}
        </div>
      )}
    </div>
  );
}
