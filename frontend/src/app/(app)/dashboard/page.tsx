import { redirect } from "next/navigation";
import { createClient } from "@/lib/supabase/server";

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

  return (
    <div className="space-y-4">
      <p className="font-body text-sm text-clay-500">DOST</p>
      <h1 className="font-display text-3xl text-ink-900">
        {profile?.name ? `Hey, ${profile.name}` : "Hey there"}
      </h1>
      <p className="font-body text-ink-600">
        This is the app shell. Chat, coaching, and everything else in the
        DOST spec ships in the next phases.
      </p>
    </div>
  );
}
