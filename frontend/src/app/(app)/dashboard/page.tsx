import Link from "next/link";
import { redirect } from "next/navigation";
import { Button } from "@/components/ui/Button";
import { createClient } from "@/lib/supabase/server";

// Turns a past timestamp into "just now" / "3h ago" / "5d ago" — deliberately
// coarse (no library) since this is a one-line status, not a precise clock.
function timeAgo(iso: string): string {
  const diffMs = Date.now() - new Date(iso).getTime();
  const minutes = Math.floor(diffMs / 60000);
  if (minutes < 1) return "just now";
  if (minutes < 60) return `${minutes}m ago`;
  const hours = Math.floor(minutes / 60);
  if (hours < 24) return `${hours}h ago`;
  const days = Math.floor(hours / 24);
  if (days < 7) return `${days}d ago`;
  const weeks = Math.floor(days / 7);
  return `${weeks}w ago`;
}

export default async function DashboardPage() {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("name, preferred_language")
    .eq("auth_user_id", user.id)
    .single();

  // Both queries are scoped to this user by RLS (messages_select_own, see
  // database/migrations/0003_messages.sql) — no auth_user_id filter needed
  // here, same as useChatHistory.ts's read.
  const [{ count: turnCount }, { data: lastMessage }] = await Promise.all([
    supabase
      .from("messages")
      .select("id", { count: "exact", head: true })
      .eq("role", "user"),
    supabase
      .from("messages")
      .select("created_at")
      .order("created_at", { ascending: false })
      .limit(1)
      .maybeSingle(),
  ]);

  const hasTalked = (turnCount ?? 0) > 0;

  return (
    <div className="space-y-8">
      <div className="space-y-4">
        <p className="font-body text-sm text-clay-500">DOST</p>
        <h1 className="font-display text-3xl text-ink-900">
          {profile?.name ? `Hey, ${profile.name}` : "Hey there"}
        </h1>
        <p className="font-body text-ink-600">
          {hasTalked
            ? "Good to see you back. Whenever you're ready, DOST is listening."
            : "This is your space. Whenever you want to talk something through, DOST is here."}
        </p>
      </div>

      {hasTalked && (
        <div className="rounded-2xl bg-linen-100 px-5 py-4">
          <p className="font-body text-sm text-ink-700">
            {turnCount} {turnCount === 1 ? "message" : "messages"} shared so far
          </p>
          {lastMessage?.created_at && (
            <p className="font-body text-xs text-ink-500">
              Last chat {timeAgo(lastMessage.created_at)}
            </p>
          )}
        </div>
      )}

      <Link href="/chat">
        <Button variant="primary" className="w-full">
          {hasTalked ? "Continue talking" : "Start talking"}
        </Button>
      </Link>

      <p className="font-body text-xs text-ink-500">
        Communication coaching, daily challenges, and progress tracking are
        on their way — for now, Talk is where DOST lives.
      </p>
    </div>
  );
}
