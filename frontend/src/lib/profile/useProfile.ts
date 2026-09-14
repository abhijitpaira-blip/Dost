"use client";

import { useEffect, useState } from "react";
import { createClient } from "@/lib/supabase/client";

/**
 * Reads the signed-in user's age and preferred_language from
 * public.profiles, so the chat page can send age to POST /api/v1/chat
 * (see services/ai/prompt_loader.py) and use the right locale for voice
 * input/output (see useSpeechRecognition.ts and lib/voice/speak.ts).
 *
 * Read-only on purpose: both fields are now set once, properly, by
 * /onboarding (including the guardian-consent gate for age < 18 — see
 * database/migrations/0002_guardian_consent.sql) — this hook used to also
 * expose a setAge() updater for an inline age-capture form on the chat
 * page itself, but that form bypassed guardian consent entirely and was
 * removed once /onboarding existed to do this properly.
 */
export function useProfile() {
  const [age, setAge] = useState<number | null>(null);
  const [language, setLanguage] = useState<string>("english");
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
        .select("age, preferred_language")
        .eq("auth_user_id", user.id)
        .single();

      if (!cancelled) {
        setSignedIn(true);
        setAge(profile?.age ?? null);
        // preferred_language defaults to 'en' at the database level
        // (database/migrations/0001_init_profiles.sql, pre-onboarding);
        // onboarding always writes the full word ("english"/"hindi"/
        // "bengali" — see the LANGUAGE_LOCALES tables voice code keys off
        // of), so only fall back to "english" for that short pre-onboarding
        // default, not silently rewrite whatever onboarding actually saved.
        const raw = profile?.preferred_language;
        setLanguage(raw && raw !== "en" ? raw : "english");
        setLoading(false);
      }
    }

    void load();
    return () => {
      cancelled = true;
    };
  }, []);

  return { age, language, loading, signedIn };
}
