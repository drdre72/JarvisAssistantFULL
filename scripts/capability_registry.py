from dataclasses import dataclass


@dataclass(frozen=True)
class Capability:
    key: str
    claim: str
    implementation: str
    verification: str | None
    permission: str
    status: str
    availability: str = "local"


_LOCAL_CAPABILITIES = (
    Capability(
        "local_conversation", "converse using a local model",
        "scripts/reasoning.py", "tools/test_runtime_flow.py", "read", "live_observed",
    ),
    Capability(
        "voice_input", "listen using the microphone button",
        "scripts/speech_recognition.py", "tools/test_offline_bundle.py", "read", "live_observed",
    ),
    Capability(
        "voice_output", "speak through local Windows TTS",
        "scripts/speaker.py", "tools/test_offline_bundle.py", "read", "live_observed",
    ),
    Capability(
        "local_clock", "report the local time and date",
        "scripts/dispatcher.py", "tools/test_runtime_flow.py", "read", "unit_tested",
    ),
    Capability(
        "system_metrics", "display CPU and memory status",
        "scripts/jarvis_app.py", "tools/test_runtime_flow.py", "read", "unit_tested",
    ),
    Capability(
        "save_note", "save a note when you say write this down",
        "scripts/jarvis_commands.py", "tools/test_obsidian_brain.py",
        "explicit_user_write", "unit_tested",
    ),
    Capability(
        "queue_memory", "queue a proposed memory for review",
        "scripts/obsidian_memory.py", "tools/test_obsidian_brain.py",
        "explicit_user_write", "unit_tested",
    ),
    Capability(
        "recall_approved", "recall reviewed knowledge from the local vault",
        "scripts/obsidian_memory.py", "tools/test_obsidian_brain.py",
        "read", "unit_tested",
    ),
)


class CapabilityRegistry:
    def __init__(self, capabilities=None):
        capabilities = _LOCAL_CAPABILITIES if capabilities is None else tuple(capabilities)
        self._capabilities = {capability.key: capability for capability in capabilities}
        if len(self._capabilities) != len(capabilities):
            raise ValueError("Duplicate capability key")

    def all(self):
        return tuple(self._capabilities.values())

    def supports(self, key):
        return key in self._capabilities

    def describe(self):
        claims = [capability.claim for capability in self.all()]
        supported = "I can " + ", ".join(claims) + ". " if claims else ""
        return (
            supported
            + "I cannot view my screen, inspect arbitrary tools, run arbitrary commands, "
            "or retrieve live online information while offline. "
            "I cannot edit arbitrary Obsidian notes. A listed capability "
            "does not guarantee its device is working right now, sir."
        )

    def describe_vault_access(self):
        actions = []
        if self.supports("recall_approved"):
            actions.append("read approved Knowledge notes in my local Jarvis vault")
        if self.supports("save_note"):
            actions.append("save a note when you explicitly say write this down")
        if self.supports("queue_memory"):
            actions.append("queue a memory for your review when you say remember that")
        supported = " I can " + ", ".join(actions) + "." if actions else ""
        return (
            "I can identify my declared local capabilities, but I cannot visually "
            "see Obsidian or inspect your screen or arbitrary tools."
            + supported
            + " I cannot edit arbitrary Obsidian notes or access online services "
            "while offline, sir."
        )
