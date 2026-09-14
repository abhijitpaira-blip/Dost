"use client";

import { FormEvent, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";
import { useSpeechRecognition } from "@/lib/voice/useSpeechRecognition";
import { speak } from "@/lib/voice/speak";
import { useProfileAge } from "@/lib/profile/useProfileAge";

interface Message {
  role: "user" | "assistant";
  content: string;
}

// Hardcoded until language selection exists in onboarding (see
// services/ai/prompts/onboarding_and_consent.md) — threading it through
// here now means that's a one-line change later, not a new feature.
const LANGUAGE = "english";

const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

export default function ChatPage() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState("");
  const [sending, setSending] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [voiceRepliesOn, setVoiceRepliesOn] = useState(false);
  const scrollRef = useRef<HTMLDivElement>(null);
  const currentAudioRef = useRef<HTMLAudioElement | null>(null);
  const { supported: micSupported, listening, error: micError, start: startListening, stop: stopListening } =
    useSpeechRecognition(LANGUAGE);
  const { age, loading: ageLoading, signedIn, setAge } = useProfileAge();
  const [ageInput, setAgeInput] = useState("");
  const [ageSaveError, setAgeSaveError] = useState<string | null>(null);
  const [savingAge, setSavingAge] = useState(false);

  async function handleSaveAge(e: FormEvent) {
    e.preventDefault();
    const parsed = Number(ageInput);
    if (!Number.isInteger(parsed) || parsed < 5 || parsed > 120) {
      setAgeSaveError("Enter an age between 5 and 120.");
      return;
    }
    setSavingAge(true);
    setAgeSaveError(null);
    const { error: saveError } = await setAge(parsed);
    setSavingAge(false);
    if (saveError) setAgeSaveError(saveError);
  }

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
      const body: { messages: Message[]; age?: number } = { messages: nextMessages };
      if (age != null) body.age = age;

      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(body),
      });

      if (!res.ok) {
        throw new Error(`DOST couldn't reply (${res.status})`);
      }

      const data: { reply: string } = await res.json();
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);

      if (voiceRepliesOn) {
        currentAudioRef.current?.pause();
        try {
          currentAudioRef.current = await speak(data.reply, LANGUAGE);
        } catch {
          // Voice playback failing shouldn't block the (already-shown) text
          // reply — DOST just stays silent for this turn.
        }
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
          onClick={() => setVoiceRepliesOn((v) => !v)}
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

      {signedIn && !ageLoading && age == null && (
        <form
          onSubmit={handleSaveAge}
          className="mb-3 flex flex-wrap items-center gap-2 rounded-xl border border-linen-200 bg-linen-100 px-4 py-3"
        >
          <p className="font-body text-sm text-ink-700">
            How old are you? This helps DOST talk to you the right way.
          </p>
          <input
            type="number"
            min={5}
            max={120}
            value={ageInput}
            onChange={(e) => setAgeInput(e.target.value)}
            placeholder="Age"
            className="w-20 rounded-lg border border-linen-200 bg-linen-50 px-2 py-1 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
          />
          <Button type="submit" variant="secondary" disabled={savingAge || !ageInput}>
            {savingAge ? "Saving…" : "Save"}
          </Button>
          {ageSaveError && (
            <p role="alert" className="w-full font-body text-xs text-clay-500">
              {ageSaveError}
            </p>
          )}
        </form>
      )}

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
