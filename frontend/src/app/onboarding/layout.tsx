import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

/**
 * /onboarding only needs to know someone is signed in — it does NOT check
 * onboarding_completed_at (unlike (app)/layout.tsx), because this IS the
 * page that sets it. Checking that here would redirect a user straight
 * back into the guardian-consent flow they're already completing.
 */
export default async function OnboardingLayout({
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

  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-center px-6 py-12">
      {children}
    </main>
  );
}
