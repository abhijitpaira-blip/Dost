"use client";

import { FormEvent, useRef, useState } from "react";
import { Button } from "@/components/ui/Button";

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
  const scrollRef = useRef<HTMLDivElement>(null);

  async function handleSubmit(e: FormEvent) {
    e.preventDefault();
    const trimmed = input.trim();
    if (!trimmed || sending) return;

    const nextMessages: Message[] = [...messages, { role: "user", content: trimmed }];
    setMessages(nextMessages);
    setInput("");
    setError(null);
    setSending(true);

    try {
      const res = await fetch(`${API_URL}/api/v1/chat`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ messages: nextMessages }),
      });

      if (!res.ok) {
        throw new Error(`DOST couldn't reply (${res.status})`);
      }

      const data: { reply: string } = await res.json();
      setMessages([...nextMessages, { role: "assistant", content: data.reply }]);
    } catch {
      setError("Couldn't reach DOST just now — check the backend is running and try again.");
    } finally {
      setSending(false);
      requestAnimationFrame(() => {
        scrollRef.current?.scrollIntoView({ behavior: "smooth" });
      });
    }
  }

  return (
    <div className="flex h-[calc(100vh-9rem)] flex-col">
      <div className="space-y-1 pb-4">
        <p className="font-body text-sm text-clay-500">DOST</p>
        <h1 className="font-display text-2xl text-ink-900">Talk it through</h1>
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

        {error && (
          <p role="alert" className="font-body text-sm text-clay-500">
            {error}
          </p>
        )}

        <div ref={scrollRef} />
      </div>

      <form onSubmit={handleSubmit} className="flex gap-2 pt-3">
        <input
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type a message…"
          className="flex-1 rounded-xl border border-linen-200 bg-linen-50 px-4 py-3 font-body text-ink-800 focus-visible:outline-2 focus-visible:outline-amber-500"
        />
        <Button type="submit" variant="primary" disabled={sending || !input.trim()}>
          Send
        </Button>
      </form>
    </div>
  );
}
