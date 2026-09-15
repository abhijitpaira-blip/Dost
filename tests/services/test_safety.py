from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from services.safety import detect_crisis_signal, reply_already_has_resources
from services.safety.resources import CRISIS_RESOURCE_FOOTER


def test_detects_explicit_english_phrases():
    assert detect_crisis_signal("I want to kill myself")
    assert detect_crisis_signal("sometimes I think about suicide")
    assert detect_crisis_signal("I've been cutting myself")
    assert detect_crisis_signal("I don't want to live anymore")


def test_detects_hindi_and_bengali_word_for_suicide():
    assert detect_crisis_signal("mujhe lagta hai aatmahatya... आत्महत्या karna chahta hoon")
    assert detect_crisis_signal("আত্মহত্যা niye bhabchi")
    assert detect_crisis_signal("kabhi kabhi khudkushi ka khayal aata hai")


def test_is_case_insensitive():
    assert detect_crisis_signal("I WANT TO DIE")


def test_ignores_empty_or_none_text():
    assert not detect_crisis_signal("")
    assert not detect_crisis_signal(None)  # type: ignore[arg-type]


def test_does_not_flag_ordinary_distress_or_unrelated_text():
    # Ordinary frustration/sadness should NOT trip the net — it's a narrow
    # keyword match on explicit crisis phrasing, not a mood detector.
    assert not detect_crisis_signal("I'm so stressed about my exam tomorrow")
    assert not detect_crisis_signal("I'm dying to watch the new movie this weekend")
    assert not detect_crisis_signal("Feeling really down about my grades lately")
    assert not detect_crisis_signal("Good morning DOST, how are you?")


def test_reply_already_has_resources_matches_any_known_number():
    assert reply_already_has_resources("please call 14416 for support")
    assert reply_already_has_resources("KIRAN is 1800-599-0019")
    assert not reply_already_has_resources("I'm here for you, tell me more")


def test_footer_contains_the_three_verified_resources():
    assert "14416" in CRISIS_RESOURCE_FOOTER
    assert "1800-891-4416" in CRISIS_RESOURCE_FOOTER
    assert "1800-599-0019" in CRISIS_RESOURCE_FOOTER
    assert "112" in CRISIS_RESOURCE_FOOTER
