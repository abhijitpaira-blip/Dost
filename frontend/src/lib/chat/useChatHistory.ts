"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

export interface StoredMessage {
  role: "user" | "assistant";
  content: string;
}

/**
 * Loads this user's past conversation from public.messages
 * (database/migrations/0003_messages.sql) so a page reload doesn't lose
 * it. Read directly via the browser Supabase client — RLS
 * (messages_select_own) scopes this to the signed-in user, same pattern
 * already used for profiles (see useProfile.ts). There's no backend
 * endpoint for this on purpose (see backend/app/api/v1/chat.py's
 * docstring).
 *
 * Read-only: writing happens server-side instead — chat.py calls
 * services.memory.save_turn() after every reply.
 */
export function useChatHistory() {
  const [history, setHistory] = useState<StoredMessage[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        if (!cancelled) setLoading(false);
        return;
      }

      const { data } = await supabase
        .from("messages")
        .select("role, content")
        .eq("auth_user_id", user.id)
        .order("created_at", { ascending: true });

      if (!cancelled) {
        setHistory((data ?? []) as StoredMessage[]);
        setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { history, loading };
}
