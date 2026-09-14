"""
Assembles DOST's system prompt for a given user/turn, instead of sending one
monolithic document (or, since Phase 2, the single flat `DOST_SYSTEM_PROMPT`
in `personality.py`) on every request regardless of who's asking.

`services/ai/prompts/` holds three source files:
  - core.md                  — always included (identity, safety, response
                                style, scope/boundaries, etc.)
  - age_bands.md              — one delimited block per age band; only the
                                block matching the user's own band is used
  - onboarding_and_consent.md — used only while the user hasn't finished
                                first-run onboarding

Relationship to `personality.py`: `DOST_SYSTEM_PROMPT` there is the
Phase 2 MVP prompt and stays as the fallback for a request that doesn't
know the user's age yet (see `backend/app/api/v1/chat.py`). Once the
frontend/backend know a user's age (from onboarding or the `profiles`
table), route through `build_system_prompt` instead — it supersedes
`DOST_SYSTEM_PROMPT` with the same voice, plus age-appropriate behavior,
a corrected safety rule, and per-turn token savings from only sending one
age-band block.

This module has no FastAPI/Supabase imports on purpose, so it can be unit
tested and reused (e.g. by a voice pipeline) without pulling in the web
layer — see docs/ARCHITECTURE.md for the services/ -> backend/ dependency
direction this follows.
"""
from __future__ import annotations

import re
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

PROMPTS_DIR = Path(__file__).resolve().parent / "prompts"

# Age-band boundaries, inclusive. "61-80+" has no upper bound.
_AGE_BAND_BOUNDS: list[tuple[str, int, int | None]] = [
    ("5-7", 5, 7),
    ("8-10", 8, 10),
    ("11-13", 11, 13),
    ("14-17", 14, 17),
    ("18-25", 18, 25),
    ("26-40", 26, 40),
    ("41-60", 41, 60),
    ("61-80+", 61, None),
]

_AGE_BAND_IDS = {band_id for band_id, _, _ in _AGE_BAND_BOUNDS}

_BLOCK_PATTERN = re.compile(
    r"<!--\s*AGE_BAND:\s*(?P<id>[\w+-]+)\s*-->(?P<body>.*?)<!--\s*/AGE_BAND\s*-->",
    re.DOTALL,
)


class UnknownAgeBandError(ValueError):
    """Raised when an age or age_band doesn't match any known band."""


@dataclass(frozen=True)
class PromptUser:
    """
    The minimal shape prompt assembly needs. Build this from wherever the
    caller has the user profile (request body, Supabase row, JWT claims,
    etc.) — this module deliberately doesn't know about any of those.
    """
    onboarding_complete: bool
    age: int | None = None
    age_band: str | None = None

    def resolved_age_band(self) -> str:
        if self.age_band:
            if self.age_band not in _AGE_BAND_IDS:
                raise UnknownAgeBandError(f"Unknown age_band: {self.age_band!r}")
            return self.age_band
        if self.age is not None:
            return age_to_band(self.age)
        raise UnknownAgeBandError("PromptUser needs either age or age_band set")


def age_to_band(age: int) -> str:
    """Map a numeric age to one of the DOST age-band ids."""
    for band_id, low, high in _AGE_BAND_BOUNDS:
        if age >= low and (high is None or age <= high):
            return band_id
    raise UnknownAgeBandError(f"No age band covers age {age}")


@lru_cache(maxsize=1)
def _read_core() -> str:
    return (PROMPTS_DIR / "core.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _read_onboarding() -> str:
    return (PROMPTS_DIR / "onboarding_and_consent.md").read_text(encoding="utf-8")


@lru_cache(maxsize=1)
def _age_band_blocks() -> dict[str, str]:
    raw = (PROMPTS_DIR / "age_bands.md").read_text(encoding="utf-8")
    blocks = {match.group("id"): match.group("body").strip() for match in _BLOCK_PATTERN.finditer(raw)}
    missing = _AGE_BAND_IDS - blocks.keys()
    if missing:
        raise ValueError(f"age_bands.md is missing block(s): {sorted(missing)}")
    return blocks


def load_age_band(band_id: str) -> str:
    """Return just the text for one age-band block (no surrounding markers)."""
    blocks = _age_band_blocks()
    if band_id not in blocks:
        raise UnknownAgeBandError(f"Unknown age_band: {band_id!r}")
    return blocks[band_id]


def build_system_prompt(user: PromptUser) -> str:
    """
    The main entry point: returns the exact system prompt text to send for
    this user's next turn.

    - Always includes core.md.
    - Includes onboarding_and_consent.md ONLY while onboarding isn't done —
      once onboarding_complete is True, that file is never sent again.
    - Otherwise includes exactly one age-band block, resolved from
      user.age_band if set, else derived from user.age.

    Callers are still responsible for actually gating account creation on
    guardian consent for minors (see onboarding_and_consent.md §1) — this
    function only assembles prompt text, it doesn't enforce consent.
    """
    parts = [_read_core()]

    if not user.onboarding_complete:
        parts.append(_read_onboarding())
    else:
        parts.append(load_age_band(user.resolved_age_band()))

    return "\n\n".join(parts)
