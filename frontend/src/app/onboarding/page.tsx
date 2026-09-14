"use client";

import { FormEvent, useMemo, useState } from "react";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";

type Language = "english" | "hindi" | "bengali";

const MIN_AGE = 5;
const MAX_AGE = 120;
const GUARDIAN_CONSENT_AGE_CUTOFF = 18; // India's DPDP Act treats anyone
// under 18 as a "child" requiring verifiable guardian consent — see
// services/ai/prompts/onboarding_and_consent.md and
// database/migrations/0002_guardian_consent.sql.

const EMAIL_PATTERN = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

/**
 * First-run flow for every new DOST account: name, age, preferred
 * language, and — for anyone under 18 — a guardian's name, email, and a
 * self-attested consent checkbox before we'll let them into the app.
 *
 * This is deliberately the ONLY place onboarding_completed_at gets set,
 * and (app)/layout.tsx redirects here until it is — see that file and
 * database/migrations/0002_guardian_consent.sql for the enforcement side.
 *
 * SCOPE NOTE: guardian_consent_given is self-attested, not identity
 * verified (no email confirmation link is sent, no ID check happens).
 * That's a real gap, called out in the migration and left as-is here —
 * closing it (e.g. emailing the guardian a confirmation link) is future
 * work, not something this first pass does.
 */
export default function OnboardingPage() {
  const [name, setName] = useState("");
  const [ageInput, setAgeInput] = useState("");
  const [language, setLanguage] = useState<Language>("english");
  const [guardianName, setGuardianName] = useState("");
  const [guardianEmail, setGuardianEmail] = useState("");
  const [guardianConsent, setGuardianConsent] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [saving, setSaving] = useState(false);

  const parsedAge = Number(ageInput);
  const ageIsValid =
    ageInput.trim() !== "" &&
    Number.isInteger(parsedAge) &&
    parsedAge >= MIN_AGE &&
    parsedAge <= MAX_AGE;

  // Only treated as a minor once a valid age has actually been entered —
  // an empty/invalid age shouldn't flash the guardian fields.
  const isMinor = useMemo(
    () => ageIsValid && parsedAge < GUARDIAN_CONSENT_AGE_CUTOFF,
    [ageIsValid, parsedAge]
  );

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    setError(null);

    if (!name.trim()) {
      setError("Let us know what to call you.");
      return;
    }
    if (!ageIsValid) {
      setError(`Enter an age between ${MIN_AGE} and ${MAX_AGE}.`);
      return;
    }
    if (isMinor) {
      if (!guardianName.trim()) {
        setError("We need a parent or guardian's name.");
        return;
      }
      if (!EMAIL_PATTERN.test(guardianEmail.trim())) {
        setError("Enter a valid email for your parent or guardian.");
        return;
      }
      if (!guardianConsent) {
        setError("A parent or guardian needs to confirm they're okay with this.");
        return;
      }
    }

    setSaving(true);
    const supabase = createClient();
    const {
      data: { user },
    } = await supabase.auth.getUser();

    if (!user) {
      // Shouldn't happen — onboarding/layout.tsx already gates on this —
      // but if the session dropped mid-form, send them back to sign in
      // rather than fail silently.
      window.location.href = "/login";
      return;
    }

    const now = new Date().toISOString();
    const { error: updateError } = await supabase
      .from("profiles")
      .update({
        name: name.trim(),
        age: parsedAge,
        preferred_language: language,
        guardian_name: isMinor ? guardianName.trim() : null,
        guardian_email: isMinor ? guardianEmail.trim() : null,
        guardian_consent_given: isMinor ? guardianConsent : false,
        guardian_consented_at: isMinor ? now : null,
        onboarding_completed_at: now,
      })
      .eq("auth_user_id", user.id);

    setSaving(false);
    if (updateError) {
      setError(updateError.message);
      return;
    }

    // Full reload (not router.push) so (app)/layout.tsx — a server
    // component — re-checks onboarding_completed_at with fresh data
    // instead of stale cached state, matching login/page.tsx's pattern.
    window.location.href = "/dashboard";
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="font-display text-3xl text-ink-900">Tell DOST about you</h1>
        <p className="font-body text-sm text-ink-600">
          A couple of quick questions so DOST can talk to you the right way.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor="name" className="font-body text-sm text-ink-700">
            What should DOST call you?
          </label>
          <input
            id="name"
            type="text"
            required
            value={name}
            onChange={(e) => setName(e.target.value)}
            className="w-full rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="age" className="font-body text-sm text-ink-700">
            How old are you?
          </label>
          <input
            id="age"
            type="number"
            min={MIN_AGE}
            max={MAX_AGE}
            required
            value={ageInput}
            onChange={(e) => setAgeInput(e.target.value)}
            className="w-28 rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="language" className="font-body text-sm text-ink-700">
            Which language should DOST speak?
          </label>
          <select
            id="language"
            value={language}
            onChange={(e) => setLanguage(e.target.value as Language)}
            className="w-full rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
          >
            <option value="english">English</option>
            <option value="hindi">हिन्दी (Hindi)</option>
            <option value="bengali">বাংলা (Bengali)</option>
          </select>
        </div>

        {isMinor && (
          <div className="space-y-4 rounded-xl border border-linen-200 bg-linen-100 px-4 py-4">
            <p className="font-body text-sm text-ink-700">
              Since you&apos;re under 18, we need a parent or guardian to
              say it&apos;s okay before you can use DOST.
            </p>

            <div className="space-y-1">
              <label htmlFor="guardianName" className="font-body text-sm text-ink-700">
                Parent or guardian&apos;s name
              </label>
              <input
                id="guardianName"
                type="text"
                required={isMinor}
                value={guardianName}
                onChange={(e) => setGuardianName(e.target.value)}
                className="w-full rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
              />
            </div>

            <div className="space-y-1">
              <label htmlFor="guardianEmail" className="font-body text-sm text-ink-700">
                Their email
              </label>
              <input
                id="guardianEmail"
                type="email"
                required={isMinor}
                value={guardianEmail}
                onChange={(e) => setGuardianEmail(e.target.value)}
                className="w-full rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
              />
            </div>

            <label className="flex items-start gap-2 font-body text-sm text-ink-700">
              <input
                type="checkbox"
                checked={guardianConsent}
                onChange={(e) => setGuardianConsent(e.target.checked)}
                className="mt-1"
              />
              <span>
                I am this person&apos;s parent or guardian, and I&apos;m okay
                with them using DOST.
              </span>
            </label>
          </div>
        )}

        {error && (
          <p role="alert" className="font-body text-sm text-clay-500">
            {error}
          </p>
        )}

        <Button type="submit" variant="primary" className="w-full" disabled={saving}>
          {saving ? "Saving…" : "Continue"}
        </Button>
      </form>
    </div>
  );
}
