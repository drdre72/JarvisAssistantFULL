import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from capability_registry import CapabilityRegistry
from decision_controller import OfflineDecisionController
from obsidian_memory import ObsidianBrain


class CapabilityRegistryTests(unittest.TestCase):
    def test_declared_capabilities_are_local_and_have_source_evidence(self):
        registry = CapabilityRegistry()
        for capability in registry.all():
            with self.subTest(capability=capability.key):
                self.assertEqual(capability.availability, "local")
                self.assertTrue((ROOT / capability.implementation).is_file())
                if capability.verification:
                    self.assertTrue((ROOT / capability.verification).is_file())
        self.assertTrue(registry.supports("system_metrics"))
        self.assertTrue(registry.supports("recall_approved"))
        self.assertFalse(registry.supports("network_lookup"))

    def test_summary_reflects_registered_capabilities_only(self):
        registry = CapabilityRegistry()
        self.assertIn("save a note", registry.describe())
        self.assertIn("reviewed knowledge", registry.describe())
        self.assertIn("cannot view my screen", registry.describe())
        self.assertIn("cannot edit arbitrary Obsidian notes", registry.describe())
        without_notes = CapabilityRegistry(
            tuple(item for item in registry.all() if item.key != "save_note")
        )
        self.assertNotIn("save a note", without_notes.describe())

    def test_vault_description_does_not_claim_unregistered_actions(self):
        registry = CapabilityRegistry()
        self.assertIn("declared local capabilities", registry.describe_vault_access())
        self.assertIn("approved Knowledge", registry.describe_vault_access())
        self.assertIn("cannot edit arbitrary", registry.describe_vault_access())
        self.assertIn("offline", registry.describe_vault_access())
        without_writes = CapabilityRegistry(
            tuple(
                item for item in registry.all()
                if item.key not in {"save_note", "queue_memory"}
            )
        )
        self.assertNotIn("save a note", without_writes.describe_vault_access())
        self.assertNotIn("queue a memory", without_writes.describe_vault_access())


class OfflineDecisionTests(unittest.TestCase):
    def setUp(self):
        self.search = Mock(return_value=[])
        self.controller = OfflineDecisionController(search_knowledge=self.search)

    def test_conversation_does_not_scan_knowledge_or_require_classifier(self):
        decision = self.controller.decide("How are you doing?")
        self.assertEqual(decision.strategy, "conversation")
        self.assertEqual(decision.reason_code, "ordinary_conversation")
        self.assertIsNone(decision.memory_query)
        self.search.assert_not_called()

    def test_explicit_memory_uses_only_reviewed_local_knowledge(self):
        self.search.return_value = [(3, "pixel.md", "Pixel is my cat.")]
        decision = self.controller.decide("What do my approved notes say about Pixel?")
        self.assertEqual(decision.strategy, "retrieve_approved")
        self.assertEqual(decision.capability, "recall_approved")
        self.assertEqual(decision.memory_query, "Pixel")
        self.assertEqual(decision.sources, ("pixel.md",))
        self.search.assert_called_once_with("Pixel", limit=2)
        self.assertNotIn("Pixel", decision.reason_code)

    def test_statement_about_my_project_remains_conversation(self):
        decision = self.controller.decide("My project is going well.")
        self.assertEqual(decision.strategy, "conversation")
        self.search.assert_not_called()

    def test_missing_approved_note_does_not_guess(self):
        decision = self.controller.decide("What do my approved notes say about Pixel?")
        self.assertEqual(decision.strategy, "respond")
        self.assertIn("no approved", decision.reply.lower())
        self.search.assert_called_once()

    def test_missing_topic_and_unreadable_vault_fail_closed(self):
        decision = self.controller.decide("What do my approved notes say about?")
        self.assertEqual(decision.reason_code, "missing_memory_topic")
        self.search.assert_not_called()
        self.search.side_effect = OSError("vault unavailable")
        decision = self.controller.decide("What do my approved notes say about Pixel?")
        self.assertEqual(decision.strategy, "respond")
        self.assertEqual(decision.reason_code, "memory_read_failed")
        self.assertIn("could not read", decision.reply.lower())

    def test_personal_question_uses_relevant_approved_note_only(self):
        self.search.return_value = [(3, "favorite-color.md", "I prefer blue.")]
        decision = self.controller.decide("What is my favorite color?")
        self.assertEqual(decision.strategy, "retrieve_approved")
        self.assertEqual(decision.memory_query, "What is my favorite color?")
        self.search.return_value = [(1, "random.md", "A passing mention.")]
        low_confidence = self.controller.decide("What is my favorite color?")
        self.assertEqual(low_confidence.strategy, "respond")
        self.assertIn("won't guess", low_confidence.reply)

    def test_missing_local_conversation_capability_cannot_be_selected(self):
        registry = CapabilityRegistry(
            tuple(
                item for item in CapabilityRegistry().all()
                if item.key != "local_conversation"
            )
        )
        controller = OfflineDecisionController(registry=registry, search_knowledge=self.search)
        decision = controller.decide("How are you doing?")
        self.assertEqual(decision.strategy, "respond")
        self.assertEqual(decision.reason_code, "conversation_unavailable")
        self.search.assert_not_called()

    def test_local_metrics_are_selected_without_inference(self):
        decision = self.controller.decide("What is my CPU usage?")
        self.assertEqual(decision.strategy, "local_metrics")
        self.assertEqual(decision.capability, "system_metrics")
        self.search.assert_not_called()

    def test_live_flight_information_is_not_invented_or_fetched(self):
        decision = self.controller.decide("Has my flight gate changed?")
        self.assertEqual(decision.strategy, "respond")
        self.assertEqual(decision.reason_code, "fresh_data_unavailable")
        self.assertIn("offline", decision.reply.lower())
        self.search.assert_not_called()

    def test_fresh_data_is_distinct_from_general_information(self):
        for text in (
            "What's the weather like today?",
            "Is my flight gate still the same?",
            "What is the latest news?",
        ):
            with self.subTest(text=text):
                self.assertEqual(self.controller.decide(text).strategy, "respond")
        self.assertEqual(
            self.controller.decide("How do flight gates change?").strategy,
            "conversation",
        )
        self.search.assert_not_called()

    def test_capability_fallback_is_registry_backed(self):
        decision = self.controller.decide("Which tools can you use?")
        self.assertEqual(decision.strategy, "respond")
        self.assertEqual(decision.reply, CapabilityRegistry().describe())
        self.search.assert_not_called()

    def test_real_vault_approval_is_the_only_memory_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            vault = Path(directory) / "vault"
            vault.mkdir()
            with patch("obsidian_memory.get_runtime_logger", return_value=Mock()):
                brain = ObsidianBrain(vault_path=vault, base_path=Path(directory))
                brain.propose_memory("Pixel is my cat")
                controller = OfflineDecisionController(search_knowledge=brain.search_knowledge)
                self.assertEqual(
                    controller.decide("What do my approved notes say about Pixel?").strategy,
                    "respond",
                )
                (brain.knowledge / "pixel.md").write_text(
                    "---\nreview_status: approved\n---\nPixel is my cat.\n",
                    encoding="utf-8",
                )
                decision = controller.decide("What do my approved notes say about Pixel?")
                self.assertEqual(decision.strategy, "retrieve_approved")
                context = brain.get_conversation_context(3, query=decision.memory_query)
                self.assertIn("Source: Jarvis/Knowledge/pixel.md", context)
                self.assertNotIn("Proposed memory", context)


if __name__ == "__main__":
    unittest.main()
