"use client";

/**
 * Speaks text aloud using the browser's built-in SpeechSynthesis (the
 * text-to-speech half of the Web Speech API) — free forever, no API key,
 * no backend round trip. This mirrors the free-by-design choice already
 * made for mic input in useSpeechRecognition.ts.
 *
 * Tradeoff (the reason this isn't a strict upgrade): unlike a hosted
 * voice API, which language/voices are available depends on the user's
 * own device and OS, so Hindi/Bengali voice quality can vary — better on
 * some phones/browsers than others, occasionally missing entirely on
 * older or unusual setups. backend/app/api/v1/voice.py's Speechma proxy
 * (services/voice/speechma_client.py) is left in place, unused for now,
 * as a paid, more consistent fallback if that variability ever becomes a
 * real problem worth paying to fix.
 */

// Matches the three languages services/ai/prompts/core.md supports —
// keep in sync with useSpeechRecognition.ts's copy of this table.
const LANGUAGE_LOCALES: Record<string, string> = {
  english: "en-US",
  hindi: "hi-IN",
  bengali: "bn-IN",
};

export interface SpeakResult {
  supported: boolean;
  error?: string;
}

let cachedVoices: SpeechSynthesisVoice[] = [];

// Chrome (and some other browsers) load voices asynchronously — the very
// first call to getVoices() can return an empty list until the
// `voiceschanged` event fires. This waits for that once, then reuses the
// cached list for every later call.
function loadVoices(): Promise<SpeechSynthesisVoice[]> {
  return new Promise((resolve) => {
    const synth = window.speechSynthesis;
    const existing = synth.getVoices();
    if (existing.length > 0) {
      resolve(existing);
      return;
    }

    let settled = false;
    const finish = (voices: SpeechSynthesisVoice[]) => {
      if (settled) return;
      settled = true;
      synth.removeEventListener("voiceschanged", handleVoicesChanged);
      resolve(voices);
    };
    const handleVoicesChanged = () => finish(synth.getVoices());

    synth.addEventListener("voiceschanged", handleVoicesChanged);
    // Fallback in case voiceschanged never fires on this browser/OS —
    // don't leave the caller waiting forever.
    setTimeout(() => finish(synth.getVoices()), 1000);
  });
}

function pickVoice(voices: SpeechSynthesisVoice[], locale: string): SpeechSynthesisVoice | undefined {
  const lower = locale.toLowerCase();
  const exact = voices.find((v) => v.lang.toLowerCase() === lower);
  if (exact) return exact;
  const languagePrefix = lower.split("-")[0];
  return voices.find((v) => v.lang.toLowerCase().startsWith(languagePrefix));
}

/**
 * Speaks `text` in the given DOST language ("english" | "hindi" |
 * "bengali"). Cancels whatever was already being said first, so a new
 * reply always interrupts the previous one rather than overlapping it.
 */
export async function speak(text: string, language: string = "english"): Promise<SpeakResult> {
  if (typeof window === "undefined" || !("speechSynthesis" in window)) {
    return { supported: false, error: "Voice replies aren't supported in this browser." };
  }

  const synth = window.speechSynthesis;
  synth.cancel();

  if (cachedVoices.length === 0) {
    cachedVoices = await loadVoices();
  }

  const locale = LANGUAGE_LOCALES[language.toLowerCase()] ?? LANGUAGE_LOCALES.english;
  const utterance = new SpeechSynthesisUtterance(text);
  utterance.lang = locale;
  const voice = pickVoice(cachedVoices, locale);
  if (voice) utterance.voice = voice;

  synth.speak(utterance);
  return { supported: true };
}

/** Stops whatever DOST is currently saying (e.g. the user sent a new message). */
export function stopSpeaking() {
  if (typeof window !== "undefined" && "speechSynthesis" in window) {
    window.speechSynthesis.cancel();
  }
}
