const API_URL = process.env.NEXT_PUBLIC_API_URL ?? "http://localhost:8000";

/**
 * Sends `text` to POST /api/v1/voice/speak and plays the returned MP3.
 * The Speechma API key never reaches the browser — the backend proxies
 * the call (see backend/app/api/v1/voice.py). Returns the HTMLAudioElement
 * so callers can stop() playback if needed (e.g. a new message arrives).
 */
export async function speak(text: string, language: string = "english"): Promise<HTMLAudioElement> {
  const res = await fetch(`${API_URL}/api/v1/voice/speak`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ text, language }),
  });

  if (!res.ok) {
    let detail = `DOST's voice isn't set up yet (${res.status})`;
    try {
      const body = await res.json();
      if (body?.detail) detail = body.detail;
    } catch {
      // ignore — use the generic message above
    }
    throw new Error(detail);
  }

  const blob = await res.blob();
  const url = URL.createObjectURL(blob);
  const audio = new Audio(url);
  audio.addEventListener("ended", () => URL.revokeObjectURL(url), { once: true });
  await audio.play();
  return audio;
}
