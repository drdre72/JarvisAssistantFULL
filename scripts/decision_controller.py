import re
from dataclasses import dataclass

from capability_registry import CapabilityRegistry


@dataclass(frozen=True)
class Decision:
    strategy: str
    reason_code: str
    capability: str | None = None
    reply: str | None = None
    memory_query: str | None = None
    sources: tuple[str, ...] = ()


_LIVE_DATA = re.compile(
    r"\b(?:(?:has|did|is|what is) my flight gate|flight status|"
    r"(?:current|live|today'?s) (?:weather|traffic|news)|"
    r"(?:weather|traffic)\b.{0,30}\b(?:today|now|right now)|"
    r"latest news)\b",
    re.I,
)
_METRICS = re.compile(
    r"\b(?:cpu (?:usage|use|load)|ram (?:usage|use)|"
    r"(?:computer|system) memory (?:usage|use)|system metrics)\b",
    re.I,
)
_CAPABILITIES = re.compile(
    r"\b(?:which tools can you use|what tools are available|"
    r"which capabilities do you have)\b",
    re.I,
)
_EXPLICIT_MEMORY = re.compile(
    r"^(?:what do (?:my|your) (?:approved )?(?:notes|knowledge) say about|"
    r"according to (?:my|your) (?:approved )?(?:notes|knowledge) about)"
    r"\b[\s:,.!?-]*(.*)$",
    re.I | re.S,
)
_PERSONAL = re.compile(
    r"\b(?:my|our)\s+(?:favorite|preferred|preference|name|birthday|project)\b",
    re.I,
)


class OfflineDecisionController:
    def __init__(self, registry=None, search_knowledge=None):
        self.registry = registry if registry is not None else CapabilityRegistry()
        self.search_knowledge = search_knowledge

    def _search(self, query):
        if self.search_knowledge is None:
            from obsidian_memory import get_brain
            return get_brain().search_knowledge(query, limit=2)
        return self.search_knowledge(query, limit=2)

    def decide(self, text):
        text = text.strip() if text else ""
        if not text:
            return Decision("respond", "empty_input", reply="What would you like to ask, sir?")
        if _LIVE_DATA.search(text):
            return Decision(
                "respond", "fresh_data_unavailable",
                reply=(
                    "I cannot check live flight, weather, news, or traffic information "
                    "while offline. Please confirm current details with an authoritative "
                    "source; I can help reason from information you provide."
                ),
            )
        if _METRICS.search(text):
            if self.registry.supports("system_metrics"):
                return Decision("local_metrics", "metrics_requested", "system_metrics")
            return Decision(
                "respond", "metrics_unavailable",
                reply="Local system metrics are not available right now, sir.",
            )
        if _CAPABILITIES.search(text):
            return Decision(
                "respond", "capability_query", reply=self.registry.describe(),
            )

        explicit = _EXPLICIT_MEMORY.fullmatch(text)
        personal = bool(
            _PERSONAL.search(text)
            and re.match(r"^(?:what|who|when|where|how|is|do|did|can|tell me)\b", text, re.I)
        )
        if explicit or personal:
            topic = explicit.group(1).strip(" \t\r\n.,?!:") if explicit else text
            if not topic:
                return Decision(
                    "respond", "missing_memory_topic",
                    reply="What topic should I look for in your approved notes, sir?",
                )
            if not self.registry.supports("recall_approved"):
                return Decision(
                    "respond", "approved_memory_unavailable",
                    reply="Approved local memory retrieval is unavailable, sir.",
                )
            try:
                matches = self._search(topic)
            except (OSError, ValueError):
                return Decision(
                    "respond", "memory_read_failed",
                    reply="I could not read approved local memory, so I cannot verify that answer.",
                )
            if matches and (explicit or matches[0][0] >= 3):
                return Decision(
                    "retrieve_approved", "approved_memory_match",
                    "recall_approved", memory_query=topic,
                    sources=tuple(filename for _, filename, _ in matches),
                )
            return Decision(
                "respond", "no_approved_memory_match",
                reply="No approved local note confirms that, sir. I won't guess.",
            )
        if not self.registry.supports("local_conversation"):
            return Decision(
                "respond", "conversation_unavailable",
                reply="The local conversational model is not available, sir.",
            )
        return Decision("conversation", "ordinary_conversation", "local_conversation")
