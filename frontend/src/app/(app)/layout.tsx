import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";
import { BottomNav } from "@/components/nav/BottomNav";

/**
 * Every screen under (app) — dashboard, chat, and anything later — requires
 * both a signed-in user AND a completed onboarding (name/age/language, plus
 * guardian consent for under-18 users — see
 * services/ai/prompts/onboarding_and_consent.md and
 * database/migrations/0002_guardian_consent.sql). Gating it once here,
 * rather than per-page, is what stops a page from accidentally shipping
 * without the guardian-consent check — see /onboarding for where an
 * incomplete profile gets sent.
 */
export default async function AppLayout({
  children,
}: {
  children: React.ReactNode;
}) {
  const supabase = createClient();
  const {
    data: { user },
  } = await supabase.auth.getUser();

  if (!user) {
    redirect("/login");
  }

  const { data: profile } = await supabase
    .from("profiles")
    .select("onboarding_completed_at")
    .eq("auth_user_id", user.id)
    .single();

  if (!profile?.onboarding_completed_at) {
    redirect("/onboarding");
  }

  return (
    <div className="min-h-screen pb-20">
      <main className="mx-auto max-w-md px-6 py-10 sm:max-w-lg">{children}</main>
      <BottomNav />
    </div>
  );
}
