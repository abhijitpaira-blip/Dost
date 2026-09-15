"""
services.safety — a deterministic safety net that sits alongside (never
instead of) the AI's own judgment.

services/ai/prompts/core.md Section 9 already instructs the AI to respond
to serious distress with care and point the user toward real support — but
prompt-following can be imperfect, and a missed safety response is not an
acceptable failure mode. This package guarantees that when the user's own
message contains an explicit, unambiguous crisis signal (self-harm,
suicide, "I want to die"), a verified resource footer (real, government
helpline numbers) is appended to DOST's reply regardless of what the AI
itself said.

What this is NOT: a moderation system, a clinical risk assessment, or a
machine-learned classifier. detector.py is a narrow keyword net over
explicit phrasing (see its docstring for exactly what it does and doesn't
catch — indirect language and regional-language slang are known gaps).
This package never blocks or replaces DOST's own reply; it only appends
information, and only when the pattern actually matches.

First (and currently only) use: backend/app/api/v1/chat.py, on the user's
latest message, right before the reply is returned/saved.
"""
from .detector import detect_crisis_signal
from .resources import CRISIS_RESOURCE_FOOTER, reply_already_has_resources

__all__ = ["detect_crisis_signal", "CRISIS_RESOURCE_FOOTER", "reply_already_has_resources"]
