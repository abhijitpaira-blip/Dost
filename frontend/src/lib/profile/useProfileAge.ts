"use client";

import { useCallback, useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

/**
 * Reads (and can set) the signed-in user's age from public.profiles, so
 * the chat page can send it to POST /api/v1/chat and get DOST's
 * age-appropriate system prompt (see services/ai/prompt_loader.py)
 * instead of the flat fallback.
 *
 * This is deliberately NOT the full onboarding conversation described in
 * services/ai/prompts/onboarding_and_consent.md — no guardian-consent gate,
 * just a plain profile field, same as `name` or `preferred_language`
 * already are. Building the real consent-gated onboarding flow for minors
 * is separate, larger work — this only wires the *plumbing* (age ->
 * request) so it's ready once that flow exists to populate it properly.
 */
export function useProfileAge() {
  const [age, setAgeState] = useState<number | null>(null);
  const [loading, setLoading] = useState(true);
  const [signedIn, setSignedIn] = useState(false);

  useEffect(() => {
    let cancelled = false;

    async function load() {
      const supabase = createClient();
      const {
        data: { user },
      } = await supabase.auth.getUser();

      if (!user) {
        if (!cancelled) {
          setSignedIn(false);
          setLoading(false);
        }
        return;
      }

      const { data: profile } = await supabase
        .from("profiles")
        .select("age")
        .eq("auth_user_id", user.id)
        .single();

      if (!cancelled) {
        setSignedIn(true);
        setAgeState(profile?.age ?? null);
        setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  const setAge = useCallback(async (nextAge: number): Promise<{ error: string | null }> => {
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      return { error: "You need to be signed in to save this." };
    }

    const { error } = await supabase
      .from("profiles")
      .update({ age: nextAge })
      .eq("auth_user_id", user.id);

    if (error) {
      return { error: error.message };
    }

    setAgeState(nextAge);
    return { error: null };
  }, []);

  return { age, loading, signedIn, setAge };
}
