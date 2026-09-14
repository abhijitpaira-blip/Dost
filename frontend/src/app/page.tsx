import Link from "next/link";
import { Button } from "@/components/ui/Button";

export default function LandingPage() {
  return (
    <main className="mx-auto flex min-h-screen max-w-md flex-col justify-between px-6 py-12 sm:max-w-lg">
      <div />

      <div className="space-y-6">
        <p className="font-body text-sm tracking-wide text-clay-500">DOST</p>
        <h1 className="font-display text-4xl italic leading-[1.15] text-ink-900 sm:text-5xl">
          A friend who listens, understands &amp; helps you grow.
        </h1>
        <p className="max-w-sm font-body text-base leading-relaxed text-ink-600">
          Talk through your day, practice hard conversations, and build small
          habits that stick — with someone who remembers what matters to you.
        </p>
      </div>

      <div className="mt-12 flex flex-col gap-3">
        <Link href="/signup">
          <Button variant="primary" className="w-full">
            Get started
          </Button>
        </Link>
        <Link href="/login">
          <Button variant="secondary" className="w-full">
            I already have an account
          </Button>
        </Link>
      </div>
    </main>
  );
}
