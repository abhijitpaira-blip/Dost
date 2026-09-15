import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import pytest

from services.ai.prompt_loader import (
    PromptUser,
    UnknownAgeBandError,
    age_to_band,
    build_system_prompt,
    load_age_band,
)


def test_age_to_band_covers_full_range():
    assert age_to_band(5) == "5-7"
    assert age_to_band(7) == "5-7"
    assert age_to_band(11) == "11-13"
    assert age_to_band(25) == "18-25"
    assert age_to_band(60) == "41-60"
    assert age_to_band(61) == "61-80+"
    assert age_to_band(90) == "61-80+"


def test_age_to_band_rejects_out_of_range():
    with pytest.raises(UnknownAgeBandError):
        age_to_band(4)


def test_load_age_band_returns_only_that_block():
    text = load_age_band("11-13")
    assert "Growth Explorer" in text
    assert "Little Explorer" not in text
    assert "Life Companion" not in text


def test_load_age_band_unknown_id_raises():
    with pytest.raises(UnknownAgeBandError):
        load_age_band("not-a-band")


def test_build_system_prompt_onboarding_path_excludes_age_band():
    user = PromptUser(onboarding_complete=False, age=11)
    prompt = build_system_prompt(user)
    assert "FIRST SCREEN" in prompt  # from onboarding_and_consent.md
    assert "Growth Explorer" not in prompt  # age-band content not sent yet


def test_build_system_prompt_post_onboarding_includes_only_matching_band():
    user = PromptUser(onboarding_complete=True, age=30)
    prompt = build_system_prompt(user)
    assert "Growth Partner" in prompt  # 26-40 block
    assert "Little Explorer" not in prompt  # other bands excluded
    assert "FIRST SCREEN" not in prompt  # onboarding file not sent post-onboarding


def test_build_system_prompt_accepts_explicit_age_band():
    user = PromptUser(onboarding_complete=True, age_band="61-80+")
    prompt = build_system_prompt(user)
    assert "Life Companion" in prompt


def test_build_system_prompt_requires_age_or_age_band():
    user = PromptUser(onboarding_complete=True)
    with pytest.raises(UnknownAgeBandError):
        build_system_prompt(user)


def test_core_always_present():
    for user in (
        PromptUser(onboarding_complete=False, age=9),
        PromptUser(onboarding_complete=True, age=45),
    ):
        prompt = build_system_prompt(user)
        assert "You are DOST" in prompt
        assert "trusted adult they feel safe with" in prompt  # corrected safety line


def test_build_system_prompt_without_coach_scenario_excludes_coach_content():
    user = PromptUser(onboarding_complete=True, age=30, coach_scenario=None)
    prompt = build_system_prompt(user)
    assert "Communication Coach Mode" not in prompt
    assert "CURRENT PRACTICE SCENARIO" not in prompt


def test_build_system_prompt_with_coach_scenario_appends_coach_content_and_scenario():
    user = PromptUser(onboarding_complete=True, age=30, coach_scenario="asking my manager for a raise")
    prompt = build_system_prompt(user)
    assert "Communication Coach Mode" in prompt
    assert "CURRENT PRACTICE SCENARIO" in prompt
    assert "asking my manager for a raise" in prompt
    assert "Growth Partner" in prompt  # age-band content still included underneath


def test_build_system_prompt_coach_scenario_suppressed_during_onboarding():
    """A coach_scenario set mid-onboarding must not open roleplay early —
    onboarding still takes priority (see build_system_prompt's docstring)."""
    user = PromptUser(onboarding_complete=False, age=11, coach_scenario="asking my manager for a raise")
    prompt = build_system_prompt(user)
    assert "FIRST SCREEN" in prompt
    assert "Communication Coach Mode" not in prompt
    assert "CURRENT PRACTICE SCENARIO" not in prompt
