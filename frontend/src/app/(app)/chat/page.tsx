"use client";

import { FormEvent, useEffect, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useSpeechRecognition } from "@/lib/voice/useSpeechRecognition";
import { speak, stopSpeaking } from "@/lib/voice/speak";
import { useProfile } from "@/lib/profile/useProfile";
import { useChatHistory } from "@/lib/chat/useChatHistory";
import { createClient } from "@/lib/supabase/client";

// (app)/layout.tsx redirects anyone without onboarding_completed_at to
// /onboarding before they can reach this page, so getting here means
// onboarding is done — see database/migrations/0002_guardian_consent.sql.

interface Message {
  role: "user" | "assistant";
  content: string;
}

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceRepliesOn, setVoiceRepliesOn] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  // "english" until the profile loads — useSpeechRecognition/speak() both
  // default to English too, so mic/voice-reply just briefly assume English
  // for the instant before the real preferred_language (set in
  // /onboarding) comes back.
  const { age, language } = useProfile();
  const { supported: micSupported, listening, error: micError, start: startListening, stop: stopListening } =
    useSpeechRecognition(language);
  const { history, loading: historyLoading } = useChatHistory();
  const historyAppliedRef = useRef(false);

  // Apply the loaded conversation once, and only if the user hasn't
  // already started typing/sending in the brief window before it
  // resolves — an unlikely race, but overwriting an in-progress send
  // would be a worse bug than a rare no-op here.
  useEffect(() => {
    if (!historyLoading && !historyAppliedRef.current) {
      historyAppliedRef.current = true;
      if (history.length > 0) setMessages(history);
    }
  }, [historyLoading, history]);

  async function sendMessage(text: string) {
    const trimmed = text.trim();
    if (!trimmed || sending) return;

    const nextMessages: Message[] = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setSending(true);

    try {
      // `age` is included only once we actually have it — an omitted field
      // makes the backend fall back to the flat, all-ages DOST_SYSTEM_PROMPT
      // (see backend/app/api/v1/chat.py), never a wrong age band.
      // `onboarding_complete: true` is safe to send unconditionally here —
      // (app)/layout.tsx already guarantees it before this page is reachable.
      const body: { messages: Message[]; age?: number; onboarding_complete: boolean } = {
        messages: nextMessages,
        onboarding_complete: true,
      };
      if (age != null) body.age = age;

      // Included when we have a session so the backend can save this turn
      // (services.memory.save_turn, see chat.py) — omitted entirely just
      // means this turn isn't remembered, chat still works either way.
      const headers: Record<string, string> = { "Content-Type": "application/json" };
      const supabase = createClient();
      const {
        data: { session },
      } = await supabase.auth.getSession();
      if (session?.access_token) {
        headers.Authorization = `Bearer ${session.access_token}`;
      }

      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers,
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`DOST couldn't reply (${res.status})`);
      }

      const data: { reply: string } = await res.json();
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);

      if (voiceRepliesOn) {
        // speak() cancels any speech already in progress before starting —
        // no need to stop it ourselves first.
        await speak(data.reply, language);
        // Not checking the result here on purpose: if voice replies aren't
        // supported in this browser, DOST just stays silent for this turn
        // rather than blocking the (already-shown) text reply.
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

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    await sendMessage(input);
  }

  function handleMicClick() {
    if (listening) {
      stopListening();
      return;
    }
    startListening((transcript) => {
      setInput(transcript);
      void sendMessage(transcript);
    });
  }

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col">
      <div className="flex items-start justify-between gap-3 pb-4">
        <div className="space-y-1">
          <p className="font-body text-sm text-clay-500">DOST</p>
          <h1 className="font-display text-2xl text-ink-900">Talk it through</h1>
        </div>
        <button
          type="button"
          onClick={() => {
            setVoiceRepliesOn((v) => {
              const next = !v;
              // Turning voice off should also stop whatever's playing right
              // now, not just skip future replies.
              if (!next) stopSpeaking();
              return next;
            });
          }}
          aria-pressed={voiceRepliesOn}
          className={`shrink-0 rounded-full px-3 py-2 font-body text-xs transition-colors ${
            voiceRepliesOn
              ? "bg-ink-800 text-linen-50"
              : "bg-linen-100 text-ink-600 hover:bg-linen-200"
          }`}
          title={voiceRepliesOn ? "Voice replies on" : "Voice replies off"}
        >
          {voiceRepliesOn ? "🔊 Voice on" : "🔈 Voice off"}
        </button>
      </div>

      <div className="flex-1 space-y-4 overflow-y-auto py-2">
        {messages.length === 0 && (
          <p className="font-body text-sm text-ink-600">
            Say whatever&apos;s on your mind — DOST is listening.
          </p>
        )}

        {messages.map((m, i) => (
          <div
            key={i}
            className={`max-w-[85%] rounded-2xl px-4 py-3 font-body text-sm leading-relaxed ${
              m.role === "user"
                ? "ml-auto bg-ink-800 text-linen-50"
                : "mr-auto bg-linen-100 text-ink-800"
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
            title={listening ? "Stop listening" : "Speak to DOST"}
          >
            {listening ? "🎙️…" : "🎤"}
          </Button>
        )}
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder={listening ? "Listening…" : "Type a message…"}
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
