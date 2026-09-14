"""
POST /api/v1/voice/speak — text -> MP3 audio via Speechma.

Proxied server-side (never called from the frontend directly) so the
Speechma API key never reaches the browser — see services/voice/__init__.py.
"""
from fastapi import APIRouter, HTTPException
from fastapi.responses import Response

from app.api.v1.schemas.voice import SpeakRequest
from services.voice import SpeechmaError, synthesize, voice_id_for_language

router = APIRouter(prefix="/voice", tags=["voice"])


@router.post("/speak")
async def speak(request: SpeakRequest) -> Response:
    if not request.text.strip():
        raise HTTPException(status_code=400, detail="text must not be empty")

    try:
        voice = request.voice or voice_id_for_language(request.language)
        audio_bytes = await synthesize(request.text, voice, pitch=request.pitch, rate=request.rate)
    except SpeechmaError as exc:
        raise HTTPException(status_code=502, detail=f"Voice error: {exc}") from exc

    return Response(content=audio_bytes, media_type="audio/mpeg")
