"use client";

import { useCallback, useEffect, useRef, useState } from "react";

/**
 * Wraps the browser's built-in Web Speech API (SpeechRecognition) for
 * DOST's mic input. This is a deliberate MVP choice — it's free and needs
 * no backend round trip — but only Chromium-based browsers implement it
 * (Chrome, Edge; not Firefox, not Safari/iOS). Swapping in a server-side
 * STT provider for broader support is a later-phase decision — see
 * services/voice/__init__.py's docstring on the backend side.
 */

// Minimal shape of the (non-standard, vendor-prefixed) SpeechRecognition
// API — no @types package ships one, so this is typed just enough to use.
interface SpeechRecognitionResultEvent extends Event {
  results: { [index: number]: { [index: number]: { transcript: string } }; length: number };
}

interface SpeechRecognitionLike extends EventTarget {
  lang: string;
  interimResults: boolean;
  continuous: boolean;
  start: () => void;
  stop: () => void;
  onresult: ((event: SpeechRecognitionResultEvent) => void) | null;
  onerror: ((event: Event) => void) | null;
  onend: (() => void) | null;
}

type SpeechRecognitionConstructor = new () => SpeechRecognitionLike;

declare global {
  interface Window {
    SpeechRecognition?: SpeechRecognitionConstructor;
    webkitSpeechRecognition?: SpeechRecognitionConstructor;
  }
}

// Matches the three languages services/ai/prompts/core.md supports — keep
// in sync with speak.ts's copy of this table (see its comment on why
// "english" is en-IN, not en-US).
const LANGUAGE_LOCALES: Record<string, string> = {
  english: "en-IN",
  hindi: "hi-IN",
  bengali: "bn-IN",
};

export function useSpeechRecognition(language: string = "english") {
  const [supported, setSupported] = useState(false);
  const [listening, setListening] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const recognitionRef = useRef<SpeechRecognitionLike | null>(null);

  useEffect(() => {
    const Ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
    setSupported(!!Ctor);
  }, []);

  const start = useCallback(
    (onResult: (transcript: string) => void) => {
      const Ctor = window.SpeechRecognition ?? window.webkitSpeechRecognition;
      if (!Ctor) {
        setError("Voice input isn't supported in this browser — try Chrome or Edge, or type instead.");
        return;
      }

      setError(null);
      const recognition = new Ctor();
      recognition.lang = LANGUAGE_LOCALES[language.toLowerCase()] ?? "en-IN";
      recognition.interimResults = false;
      recognition.continuous = false;

      recognition.onresult = (event: SpeechRecognitionResultEvent) => {
        const transcript = event.results[event.results.length - 1][0].transcript;
        onResult(transcript);
      };
      recognition.onerror = () => {
        setError("Didn't catch that — try again, or type your message.");
        setListening(false);
      };
      recognition.onend = () => setListening(false);

      recognitionRef.current = recognition;
      recognition.start();
      setListening(true);
    },
    [language]
  );

  const stop = useCallback(() => {
    recognitionRef.current?.stop();
    setListening(false);
  }, []);

  return { supported, listening, error, start, stop };
}
