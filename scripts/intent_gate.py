"""Deterministic NLP for the small set of authorized Jarvis memory actions.

Adapted from Lute's parse -> typed intent -> domain authority boundary.
Conversational model output never passes through this gate.
"""

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class Intent:
    verb: str
    topic: str
    payload: str
    confidence: float
    negated: bool
    original_text: str


_PREFIX = re.compile(r"^(?:(?:hey\s+)?jarvis[\s,.:!?-]+)?(?:please\s+)?", re.I)
_NEGATION = re.compile(
    r"^(?:don't|dont|do not|never|no|stop|please don't|please dont|please do not)\b",
    re.I,
)
_PATTERNS = (
    ("note", "notes", re.compile(r"^write\s+this\s+down\b[\s:,.!?-]*(.*)$", re.I | re.S)),
    ("candidate", "memory", re.compile(r"^remember\s+that\b[\s:,.!?-]*(.*)$", re.I | re.S)),
    (
        "recall",
        "memory",
        re.compile(
            r"^(?:what\s+do\s+you\s+remember\s+about|"
            r"recall\s+(?:memory\s+about|about))\b[\s:,.!?-]*(.*)$",
            re.I | re.S,
        ),
    ),
    ("delete_denied", "memory", re.compile(r"^forget\b[\s:,.!?-]*(.*)$", re.I | re.S)),
)


def parse_intent(text):
    """Parse explicit first-clause requests; ambiguous speech stays dialogue."""
    original = text.strip() if text else ""
    clause = _PREFIX.sub("", original, count=1).strip()
    if _NEGATION.match(clause):
        return Intent("dialogue", "dialogue", "", 0.2, True, original)

    for verb, topic, pattern in _PATTERNS:
        match = pattern.fullmatch(clause)
        if match:
            payload = match.group(1).strip()
            return Intent(verb, topic, payload, 1.0, False, original)
    return Intent("dialogue", "dialogue", "", 0.2, False, original)


def authorized(intent, source):
    """Reject forged/model-derived or ambiguous action requests before I/O."""
    return (
        source == "user_voice_or_text"
        and intent.verb in {"note", "candidate", "recall"}
        and intent.confidence >= 0.9
        and not intent.negated
        and bool(intent.payload)
        and parse_intent(intent.original_text) == intent
    )
