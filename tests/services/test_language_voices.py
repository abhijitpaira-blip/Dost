import pytest

from services.voice import SpeechmaError, voice_id_for_language


def test_resolves_language_specific_voice(monkeypatch):
    monkeypatch.setenv("SPEECHMA_VOICE_HINDI", "voice-hi-1")
    assert voice_id_for_language("Hindi") == "voice-hi-1"
    assert voice_id_for_language("hindi") == "voice-hi-1"  # case-insensitive


def test_falls_back_to_default_voice(monkeypatch):
    monkeypatch.delenv("SPEECHMA_VOICE_BENGALI", raising=False)
    monkeypatch.setenv("SPEECHMA_VOICE_DEFAULT", "voice-default")
    assert voice_id_for_language("Bengali") == "voice-default"


def test_raises_when_nothing_configured(monkeypatch):
    for var in ("SPEECHMA_VOICE_ENGLISH", "SPEECHMA_VOICE_DEFAULT"):
        monkeypatch.delenv(var, raising=False)
    with pytest.raises(SpeechmaError, match="SPEECHMA_VOICE"):
        voice_id_for_language("English")
