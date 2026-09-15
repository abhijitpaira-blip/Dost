"""
The resource footer appended to a reply when detector.py fires. Kept in
English regardless of the conversation's language, deliberately: DOST's
own reply already carries the empathetic, in-language response (see
services/ai/prompts/core.md Section 9), so this footer's only job is to
get exact phone numbers in front of the user without any risk of a
translation error creeping into safety-critical information.

Sources, verified via web search in September 2026 — re-verify
periodically, helplines occasionally change:
  - Tele MANAS (Ministry of Health and Family Welfare's national tele
    mental health programme): 14416 or 1800-891-4416, free, 24/7, multiple
    Indian languages. https://telemanas.mohfw.gov.in
  - KIRAN (Ministry of Social Justice and Empowerment): 1800-599-0019,
    free, 24/7, 13 languages.
  - 112: India's unified emergency number (police/medical/fire).
"""
from __future__ import annotations

CRISIS_RESOURCE_FOOTER = (
    "\n\nIt sounds like things feel really heavy right now — you don't have "
    "to go through this alone. Please reach out to a trusted adult, or call "
    "Tele MANAS (14416 or 1800-891-4416 — free, 24/7, Govt. of India) or "
    "KIRAN (1800-599-0019). If you're in immediate danger, please call 112 "
    "right now."
)

# Used to avoid appending a second copy if the AI's own reply already
# included these numbers (it's prompted to point toward real support, so
# this does happen).
_ALREADY_PRESENT_MARKERS = ("14416", "1800-891-4416", "1800-599-0019")


def reply_already_has_resources(reply: str) -> bool:
    return any(marker in reply for marker in _ALREADY_PRESENT_MARKERS)
