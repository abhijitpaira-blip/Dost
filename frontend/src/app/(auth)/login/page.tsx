"use client";

import { useState } from "react";
import Link from "next/link";
import { createClient } from "@/lib/supabase/client";
import { Button } from "@/components/ui/Button";

export default function LoginPage() {
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);

    const supabase = createClient();
    const { error: signInError } = await supabase.auth.signInWithPassword({
      email,
      password,
    });

    setLoading(false);
    if (signInError) {
      setError(signInError.message);
      return;
    }
    window.location.href = "/dashboard";
  }

  return (
    <div className="space-y-8">
      <div className="space-y-2">
        <h1 className="font-display text-3xl text-ink-900">Welcome back</h1>
        <p className="font-body text-sm text-ink-600">
          Good to see you again.
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
          {loading ? "Signing in…" : "Sign in"}
        </Button>
      </form>

      <p className="text-center font-body text-sm text-ink-600">
        New to DOST?{" "}
        <Link href="/signup" className="text-clay-500 underline underline-offset-2">
          Create an account
        </Link>
      </p>
    </div>
  );
}
