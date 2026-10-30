import json
import re
from dataclasses import dataclass


_KINDS = {"capability_inventory", "self_purpose", "purpose_status", "dialogue", "unclear"}
_SELF_CLAIM = re.compile(
    r"\b(?:I (?:can|manage|edit|update|organize|notify|search|create|have access to)\b"
    r"|I(?:'m| am) (?:working|functioning|online|able to)\b"
    r"|My (?:intent|purpose|role|goal) is\b"
    r"|Jarvis (?:can|manages|edits|updates|organizes|notifies|searches|creates)\b)",
    re.I,
)
INTENT_SCHEMA = {
    "type": "object",
    "properties": {
        "kind": {"type": "string", "enum": sorted(_KINDS)},
        "goal": {"type": "string"},
        "draft": {"type": "string"},
    },
    "required": ["kind", "goal", "draft"],
    "additionalProperties": False,
}


@dataclass(frozen=True)
class IntentHypothesis:
    kind: str
    goal: str
    draft: str


@dataclass(frozen=True)
class Fulfillment:
    status: str
    content: str
    evidence: tuple[str, ...]
    reason_code: str


_FILE_REFERENCE = re.compile(r"\b(?:purpose\.md|file|note|document)\b", re.I)


def parse_hypothesis(raw, original_text=None):
    try:
        data = json.loads(raw)
    except (TypeError, ValueError) as error:
        raise ValueError("Invalid semantic interpretation") from error
    if (
        not isinstance(data, dict)
        or set(data) != {"kind", "goal", "draft"}
        or not isinstance(data["kind"], str)
        or data["kind"] not in _KINDS
        or not isinstance(data["goal"], str)
        or len(data["goal"]) > 240
        or not isinstance(data["draft"], str)
        or len(data["draft"]) > 1200
    ):
        raise ValueError("Invalid semantic interpretation")
    goal = original_text if original_text is not None else data["goal"]
    if not isinstance(goal, str) or not 1 <= len(goal.strip()) <= 2000:
        raise ValueError("Invalid semantic interpretation")
    return IntentHypothesis(data["kind"], goal.strip(), data["draft"].strip())


def _self_purpose(purpose_reader, status_reader):
    purpose = purpose_reader()
    if (
        purpose is None
        or purpose.review_status != "approved"
        or purpose.source != "Jarvis/Core/Purpose.md"
    ):
        if status_reader and status_reader() == "pending":
            return Fulfillment(
                "unverified",
                "I found a purpose draft awaiting your approval, sir. I will "
                "adopt it as my purpose only after its review status is approved.",
                ("Jarvis/Core/Purpose.md",), "purpose_pending_review",
            )
        return Fulfillment(
            "unverified",
            "I don't have a user-approved local purpose profile yet, sir. "
            "Please review a purpose note in my local vault first.",
            (), "missing_approved_purpose",
        )
    return Fulfillment(
        "satisfied",
        f"{purpose.preamble} My full axioms are recorded in {purpose.source}; "
        "they describe a goal, not permission to use unavailable capabilities.",
        (purpose.source,), "reviewed_purpose",
    )


def fulfill(hypothesis, registry, purpose_reader, status_reader=None):
    if hypothesis.kind == "capability_inventory":
        return Fulfillment(
            "satisfied", registry.describe(), ("capability_registry",),
            "declared_local_capabilities",
        )
    if hypothesis.kind == "purpose_status":
        if not _FILE_REFERENCE.search(hypothesis.goal):
            return _self_purpose(purpose_reader, status_reader)
        state = status_reader() if status_reader else "missing"
        path = "Jarvis/Core/Purpose.md"
        if state == "approved":
            return Fulfillment(
                "satisfied",
                f"My purpose note at {path} is present and marked approved, sir.",
                (path,), "purpose_note_approved",
            )
        if state == "pending":
            return Fulfillment(
                "satisfied",
                f"I found my purpose note at {path}, sir, but its review status is "
                "still pending. I have not adopted it as my purpose.",
                (path,), "purpose_note_pending",
            )
        if state == "invalid":
            return Fulfillment(
                "unverified",
                f"I found a purpose note at {path} but could not validate its "
                "format, sir. Please check its frontmatter and length.",
                (path,), "purpose_note_invalid",
            )
        return Fulfillment(
            "unverified",
            f"I could not find a purpose note at {path}, sir.",
            (), "purpose_note_missing",
        )
    if hypothesis.kind == "self_purpose":
        return _self_purpose(purpose_reader, status_reader)
    if hypothesis.kind == "dialogue" and hypothesis.draft:
        if re.search(r"\b(?:you|your|jarvis)\b", hypothesis.goal, re.I) and _SELF_CLAIM.search(
            hypothesis.draft.replace("\u2019", "'")
        ):
            return Fulfillment(
                "unverified",
                "I cannot verify that model-generated claim about my purpose or abilities, "
                "sir. Please ask about my reviewed purpose or declared local capabilities.",
                (), "ungrounded_self_claim",
            )
        return Fulfillment(
            "generated", hypothesis.draft, ("model_generated",),
            "ordinary_conversation",
        )
    return Fulfillment(
        "needs_clarification",
        "I could not determine what you would like me to do, sir. "
        "Could you clarify your request?",
        (), "ambiguous_intent",
    )
