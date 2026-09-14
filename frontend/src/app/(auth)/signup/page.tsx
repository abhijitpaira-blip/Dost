"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";

export default function SignupPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [sent, setSent] = useState(false);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    // A public.profiles row is created automatically by the database trigger
    // in database/migrations/0001_init_profiles.sql — nothing else to do here.
    const { error: signUpError } = await supabase.auth.signUp({ email, password });

    setLoading(false);
    if (signUpError) {
      setError(signUpError.message);
      return;
    }
    setSent(true);
  }

  if (sent) {
    return (
      <div className="space-y-3">
        <h1 className="font-display text-3xl text-ink-900">Check your inbox</h1>
        <p className="font-body text-sm text-ink-600">
          We sent a confirmation link to {email}. Follow it to finish setting up your account.
        </p>
      </div>
    );
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="font-display text-3xl text-ink-900">Let&apos;s get started</h1>
        <p className="font-body text-sm text-ink-600">
          Create your account — it takes a minute.
        </p>
      </div>

      <form onSubmit={handleSubmit} className="space-y-4">
        <div className="space-y-1">
          <label htmlFor="email" className="font-body text-sm text-ink-700">
            Email
          </label>
          <input
            id="email"
            type="email"
            required
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
          />
        </div>

        <div className="space-y-1">
          <label htmlFor="password" className="font-body text-sm text-ink-700">
            Password
          </label>
          <input
            id="password"
            type="password"
            required
            minLength={8}
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
          />
        </div>

        {error && (
          <p role="alert" className="font-body text-sm text-clay-500">
            {error}
          </p>
        )}

        <Button type="submit" variant="primary" className="w-full" disabled={loading}>
          {loading ? "Creating account…" : "Create account"}
        </Button>
      </form>

      <p className="text-center font-body text-sm text-ink-600">
        Already have an account?{" "}
        <Link href="/login" className="text-clay-500 underline underline-offset-2">
          Sign in
        </Link>
      </p>
    </div>
  );
}
