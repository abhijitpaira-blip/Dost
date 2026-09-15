"""
A narrow, deterministic keyword net over explicit, low-ambiguity crisis
phrases — self-harm, suicide, and "I want to die" style language. This is
intentionally simple: a regex scan, not a classifier, and it does not try
to catch indirect phrasing, regional slang, or anything requiring
judgment. See services/safety/__init__.py's docstring for what this
package is (and is explicitly not) a substitute for.

Biased on purpose toward false positives over false negatives: showing
crisis resources to someone who didn't need them is a mild, harmless
annoyance; missing a real signal is not an acceptable trade the other way.
"""
from __future__ import annotations

import re

# English phrases are the most reliable part of this list — well-trodden,
# unambiguous crisis-line vocabulary. The Hindi/Bengali entries are
# limited to single, dictionary-verified words (आत्महत्या / আত্মহত্যা,
# both meaning "suicide") plus the common Hinglish spellings — not full
# translated sentences, since a mistranslated safety phrase would be worse
# than no phrase at all. Regional-language *indirect* crisis language is a
# known, real gap this package does not close.
_CRISIS_PATTERNS = [
    r"\bsuicide\b",
    r"\bsuicidal\b",
    r"\bkill(?:ing)? myself\b",
    r"\bend(?:ing)? my life\b",
    r"\bwant(?:ed)? to die\b",
    r"\b(?:don'?t|do not) want to live\b",
    r"\bno reason to live\b",
    r"\bself[- ]harm(?:ing)?\b",
    r"\b(?:hurt|hurting|cut|cutting) myself\b",
    r"आत्महत्या",
    r"আত্মহত্যা",
    r"\bkhudkushi\b",
    r"\bkhudkashi\b",
]

_COMPILED = [re.compile(pattern, re.IGNORECASE) for pattern in _CRISIS_PATTERNS]


def detect_crisis_signal(text: str) -> bool:
    """True if `text` contains an explicit crisis-language match. Call this
    on the user's own message, not DOST's reply — see chat.py."""
    if not text:
        return False
    return any(pattern.search(text) for pattern in _COMPILED)
