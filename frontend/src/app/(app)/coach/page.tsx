"use client";

import { FormEvent, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useSpeechRecognition } from "@/lib/voice/useSpeechRecognition";
import { speak, stopSpeaking } from "@/lib/voice/speak";
import { useProfile } from "@/lib/profile/useProfile";

// (app)/layout.tsx redirects anyone without onboarding_completed_at to
// /onboarding before they can reach this page — see chat/page.tsx's same
// comment. Coach mode additionally needs `age` specifically (not just
// onboarding_complete) because build_system_prompt only appends
// communication_coach.md on the age-band path — see
// backend/app/api/v1/chat.py's docstring and services/ai/prompt_loader.py.

interface Message {
  role: "user" | "assistant";
  content: string;
  // The very first turn is a silent "go ahead and start" nudge so the AI
  // begins the roleplay immediately (see communication_coach.md §4) without
  // making the user type an opening line themselves. It's still sent to
  // the backend as part of the conversation, just not rendered as a bubble.
  hidden?: boolean;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";
const STARTER_MESSAGE = "(Let's begin — you can start.)";

const EXAMPLE_SCENARIOS = [
  "Asking my manager for a raise",
  "Setting a boundary with a friend who keeps cancelling plans",
  "Asking a teacher for an extension on an assignment",
  "Negotiating a price at a shop",
  "Telling a family member I disagree with them",
];

export default function CoachPage() {
  const [scenario, setScenario] = useState<string | null>(null);
  const [scenarioInput, setScenarioInput] = useState("");
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceRepliesOn, setVoiceRepliesOn] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const { age, language, loading: profileLoading } = useProfile();
  const { supported: micSupported, listening, error: micError, start: startListening, stop: stopListening } =
    useSpeechRecognition(language);

  // `scenarioOverride` exists only for the very first turn: setScenario(...)
  // in startPractice() hasn't re-rendered yet when it calls this in the same
  // tick, so the kickoff turn can't rely on reading `scenario` from state.
  async function sendTurn(
    text: string,
    opts: { hidden?: boolean; scenarioOverride?: string; baseMessages?: Message[] } = {}
  ) {
    const trimmed = text.trim();
    const activeScenario = opts.scenarioOverride ?? scenario;
    if (!trimmed || sending || !activeScenario || age == null) return;

    const base = opts.baseMessages ?? messages;
    const nextMessages: Message[] = [...base, { role: "user", content: trimmed, hidden: opts.hidden }];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setSending(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          messages: nextMessages.map(({ role, content }) => ({ role, content })),
          age,
          onboarding_complete: true,
          scenario: activeScenario,
        }),
      });

      if (!res.ok) {
        throw new Error(`DOST couldn't reply (${res.status})`);
      }

      const data: { reply: string } = await res.json();
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);

      if (voiceRepliesOn) {
        await speak(data.reply, language);
      }
    } catch {
      setError("Couldn't reach DOST just now — check the backend is running and try again.");
    } finally {
      setSending(false);
      requestAnimationFrame(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
      });
    }
  }

  async function startPractice(text: string) {
    const trimmed = text.trim();
    if (!trimmed || age == null) return;
    setScenario(trimmed);
    setError(null);
    await sendTurn(STARTER_MESSAGE, { hidden: true, scenarioOverride: trimmed, baseMessages: [] });
  }

  function changeScenario() {
    stopSpeaking();
    setScenario(null);
    setMessages([]);
    setScenarioInput("");
    setError(null);
  }

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await sendTurn(input);
  }

  async function handleStartSubmit(e: FormEvent) {
    e.preventDefault();
    await startPractice(scenarioInput);
  }

  function handleMicClick() {
    if (listening) {
      stopListening();
      return;
    }
    startListening((transcript) => {
      setInput(transcript);
      void sendTurn(transcript);
    });
  }

  // Setup screen: no scenario chosen yet.
  if (!scenario) {
    return (
      <div className="flex flex-col gap-6">
        <div className="space-y-1">
          <p className="font-body text-sm text-clay-500">DOST</p>
          <h1 className="font-display text-2xl text-ink-900">Communication Coach</h1>
          <p className="font-body text-sm text-ink-600">
            Practice a real conversation before you have it for real. Describe who you&apos;re talking to
            and what it&apos;s about — DOST will play that person so you can try out what you want to say.
          </p>
        </div>

        {profileLoading ? (
          <p className="font-body text-sm text-ink-600">Loading your profile…</p>
        ) : age == null ? (
          <p role="alert" className="font-body text-sm text-clay-500">
            Couldn&apos;t load your profile just now — try reloading the page.
          </p>
        ) : (
          <>
            <form onSubmit={handleStartSubmit} className="space-y-3">
              <textarea
                value={scenarioInput}
                onChange={(e) => setScenarioInput(e.target.value)}
                placeholder="e.g. Asking my manager for a raise"
                rows={3}
                className="w-full resize-none rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
              />
              <Button type="submit" variant="primary" disabled={!scenarioInput.trim()}>
                Start practice
              </Button>
            </form>

            <div className="space-y-2">
              <p className="font-body text-xs text-ink-600">Or try one of these:</p>
              <div className="flex flex-wrap gap-2">
                {EXAMPLE_SCENARIOS.map((example) => (
                  <button
                    key={example}
                    type="button"
                    onClick={() => setScenarioInput(example)}
                    className="rounded-full border border-linen-200 bg-linen-100 px-3 py-2 font-body text-xs text-ink-700 hover:bg-linen-200"
                  >
                    {example}
                  </button>
                ))}
              </div>
            </div>
          </>
        )}
      </div>
    );
  }

  // Roleplay screen: mirrors chat/page.tsx's layout and voice controls.
  const visibleMessages = messages.filter((m) => !m.hidden);

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col">
      <div className="flex items-start justify-between gap-3 pb-4">
        <div className="min-w-0 space-y-1">
          <p className="font-body text-sm text-clay-500">DOST Coach</p>
          <h1 className="truncate font-display text-2xl text-ink-900">{scenario}</h1>
        </div>
        <div className="flex shrink-0 gap-2">
          <button
            type="button"
            onClick={() => {
              setVoiceRepliesOn((v) => {
                const next = !v;
                if (!next) stopSpeaking();
                return next;
              });
            }}
            aria-pressed={voiceRepliesOn}
            className={`rounded-full px-3 py-2 font-body text-xs transition-colors ${
              voiceRepliesOn ? "bg-ink-800 text-linen-50" : "bg-linen-100 text-ink-600 hover:bg-linen-200"
            }`}
            title={voiceRepliesOn ? "Voice replies on" : "Voice replies off"}
          >
            {voiceRepliesOn ? "🔊" : "🔈"}
          </button>
          <button
            type="button"
            onClick={changeScenario}
            className="rounded-full bg-linen-100 px-3 py-2 font-body text-xs text-ink-600 hover:bg-linen-200"
            title="Change scenario"
          >
            New scenario
          </button>
        </div>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto py-2">
        {visibleMessages.length === 0 && !sending && (
          <p className="font-body text-sm text-ink-600">DOST is getting into character…</p>
        )}

        {visibleMessages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-2xl px-4 py-3 font-body text-sm leading-relaxed ${
              m.role === "user" ? "ml-auto bg-ink-800 text-linen-50" : "mr-auto bg-linen-100 text-ink-800"
            }`}
          >
            {m.content}
          </div>
        ))}

        {sending && (
          <div className="mr-auto max-w-[85%] rounded-2xl bg-linen-100 px-4 py-3 font-body text-sm text-ink-600">
            DOST is thinking…
          </div>
        )}

        {(error || micError) && (
          <p role="alert" className="font-body text-sm text-clay-500">
            {error || micError}
          </p>
        )}

        <div ref={scrollRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 pt-3">
        {micSupported && (
          <Button
            type="button"
            variant={listening ? "primary" : "secondary"}
            onClick={handleMicClick}
            aria-pressed={listening}
            title={listening ? "Stop listening" : "Speak your reply"}
          >
            {listening ? "🎙️…" : "🎤"}
          </Button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={listening ? "Listening…" : "Say your line…"}
          disabled={listening}
          className="flex-1 rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500 disabled:opacity-60"
        />
        <Button type="submit" variant="primary" disabled={sending || listening || !input.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
