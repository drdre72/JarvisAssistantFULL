"""Offline regression tests for the Obsidian vault and Lute-style action gate."""

import json
import sys
import tempfile
import unittest
from dataclasses import replace
from pathlib import Path
from unittest.mock import Mock, patch


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

import intent_gate
import obsidian_memory


class IntentGateTests(unittest.TestCase):
    def test_specific_actions_and_payloads_are_deterministic(self):
        cases = (
            ("Jarvis, write this down: Call Mom", "note", "notes", "Call Mom"),
            ("remember that the cat is named Pixel", "candidate", "memory", "the cat is named Pixel"),
            ("what do you remember about Pixel?", "recall", "memory", "Pixel?"),
        )
        for text, verb, topic, payload in cases:
            with self.subTest(text=text):
                intent = intent_gate.parse_intent(text)
                self.assertEqual((intent.verb, intent.topic, intent.payload), (verb, topic, payload))
                self.assertTrue(intent_gate.authorized(intent, "user_voice_or_text"))
                self.assertFalse(intent_gate.authorized(intent, "model"))

    def test_negation_questions_and_forged_intents_cannot_write(self):
        for text in (
            "Don't remember that the cat is named Pixel",
            "Jarvis, please don't write this down",
            "Should I write this down?",
            "If I say remember that, will you save it?",
            "I want you to write this down",
        ):
            with self.subTest(text=text):
                self.assertFalse(
                    intent_gate.authorized(intent_gate.parse_intent(text), "user_voice_or_text")
                )
        original = intent_gate.parse_intent("What tools do you have?")
        forged = replace(original, verb="note", topic="notes", payload="fake", confidence=1.0)
        self.assertFalse(intent_gate.authorized(forged, "user_voice_or_text"))
        self.assertFalse(intent_gate.authorized(intent_gate.parse_intent("write this down"), "user_voice_or_text"))
        self.assertEqual(intent_gate.parse_intent("forget the cat").verb, "delete_denied")


class ObsidianBrainTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.vault = self.root / "vault"
        self.vault.mkdir()
        self.base = self.root / "repo"
        self.base.mkdir()
        self.logger = patch.object(obsidian_memory, "get_runtime_logger", return_value=Mock())
        self.logger.start()
        self.addCleanup(self.logger.stop)
        self.brain = obsidian_memory.ObsidianBrain(self.vault, self.base)

    def test_vault_notes_are_reviewable_but_not_auto_approved(self):
        note = self.brain.save_note("Call Mom\n![remote](https://example.invalid/x)")
        candidate = self.brain.propose_memory("My cat is called Pixel")
        dialogue = self.brain.remember_conversation(
            "How are you?", "I imagine the cat is pink."
        )
        self.assertEqual(note.parent, self.brain.notes)
        self.assertEqual(candidate.parent, self.brain.review)
        self.assertEqual(dialogue.parent, self.brain.dialogue)
        self.assertIn("review_status: pending", candidate.read_text(encoding="utf-8"))
        self.assertIn(
            "    ![remote](https://example.invalid/x)",
            note.read_text(encoding="utf-8"),
        )
        self.assertEqual(self.brain.search_knowledge("Pixel"), [])
        context = self.brain.get_conversation_context(query="pink")
        self.assertIn("Recent dialogue (unverified", context)
        self.assertIn("Assistant (generated): I imagine the cat is pink.", context)
        self.assertNotIn("User-reviewed vault notes", context)

    def test_only_manually_approved_knowledge_is_retrieved(self):
        note = self.brain.knowledge / "pixel.md"
        note.write_text(
            "---\nreview_status: pending\n---\n\nPixel is a cat.\n",
            encoding="utf-8",
        )
        self.assertEqual(self.brain.search_knowledge("Pixel"), [])
        note.write_text(
            "---\nreview_status: approved\n---\n\nPixel is a cat.\n",
            encoding="utf-8",
        )
        self.assertEqual(self.brain.search_knowledge("Pixel")[0][1], "pixel.md")
        self.assertIn("Pixel is a cat.", self.brain.recall("Pixel"))
        self.assertIn("Source: Jarvis/Knowledge/pixel.md", self.brain.get_conversation_context(query="Pixel"))

    def test_purpose_requires_a_user_approved_note_and_never_bootstraps_itself(self):
        core = self.brain.jarvis / "Core"
        purpose = core / "Purpose.md"
        self.assertIsNone(self.brain.read_purpose())
        self.assertEqual(self.brain.purpose_status(), "missing")
        self.assertFalse(core.exists())
        core.mkdir()
        purpose.write_text(
            "---\njarvis_type: purpose\nreview_status: pending\n---\n\nHelp the user locally.\n",
            encoding="utf-8",
        )
        self.assertIsNone(self.brain.read_purpose())
        self.assertEqual(self.brain.purpose_status(), "pending")
        purpose.write_text(
            "---\njarvis_type: purpose\nreview_status: approved\n---\n\nHelp the user locally.\n",
            encoding="utf-8",
        )
        record = self.brain.read_purpose()
        self.assertEqual(record.text, "Help the user locally.")
        self.assertEqual(record.source, "Jarvis/Core/Purpose.md")
        self.assertEqual(record.review_status, "approved")
        self.assertEqual(self.brain.purpose_status(), "approved")
        purpose.write_text(
            "---\nreview_status: approved\n---\n\nHelp the user locally.\n",
            encoding="utf-8",
        )
        self.assertIsNone(self.brain.read_purpose())
        self.assertEqual(self.brain.purpose_status(), "invalid")
        purpose.write_text(
            "---\njarvis_type: purpose\nreview_status: pending\n"
            "review_status: approved\n---\n\nHelp the user locally.\n",
            encoding="utf-8",
        )
        self.assertIsNone(self.brain.read_purpose())
        self.assertEqual(self.brain.purpose_status(), "invalid")

    def test_purpose_status_reports_oversized_body_as_invalid(self):
        core = self.brain.jarvis / "Core"
        core.mkdir()
        purpose = core / "Purpose.md"
        purpose.write_text(
            "---\njarvis_type: purpose\nreview_status: pending\n---\n\n" + "x" * 2001 + "\n",
            encoding="utf-8",
        )
        self.assertIsNone(self.brain.read_purpose())
        self.assertEqual(self.brain.purpose_status(), "invalid")
        purpose.write_text(
            "---\njarvis_type: purpose\n---\n\nHelp the user locally.\n",
            encoding="utf-8",
        )
        self.assertIsNone(self.brain.read_purpose())
        self.assertEqual(self.brain.purpose_status(), "invalid")

    def test_legacy_json_is_read_only_and_context_is_chronological(self):
        memory_dir = self.base / "memory"
        memory_dir.mkdir()
        legacy = memory_dir / "conversations.json"
        record = [{
            "timestamp": "2024-01-01T00:00:00", "user_input": "Old question",
            "assistant_response": "Old reply",
        }]
        legacy.write_text(json.dumps(record), encoding="utf-8")
        before = legacy.read_bytes()
        self.brain.remember_conversation("New question", "New reply")
        context = self.brain.get_conversation_context(limit=2)
        self.assertLess(context.index("Old question"), context.index("New question"))
        self.assertIn("legacy-json-dialogue", context)
        self.assertEqual(legacy.read_bytes(), before)

    def test_external_vault_must_exist_and_be_absolute(self):
        with self.assertRaises(ValueError):
            obsidian_memory.ObsidianBrain("relative-vault", self.base)
        with self.assertRaises(ValueError):
            obsidian_memory.ObsidianBrain(self.root / "missing-vault", self.base)
        self.assertFalse((self.root / "missing-vault").exists())
        with patch.dict(
            "os.environ", {"JARVIS_OBSIDIAN_VAULT": str(self.vault)}
        ):
            selected = obsidian_memory.ObsidianBrain(base_path=self.base)
        self.assertEqual(selected.vault, self.vault)

    def test_write_this_down_saves_in_vault_not_legacy_log(self):
        import jarvis_commands

        with patch.object(obsidian_memory, "get_brain", return_value=self.brain):
            result = jarvis_commands.write_this_down({"content": "Call Mom tomorrow"})
        self.assertIn("Obsidian vault", result)
        notes = list(self.brain.notes.glob("*.md"))
        self.assertEqual(len(notes), 1)
        self.assertIn("Call Mom tomorrow", notes[0].read_text(encoding="utf-8"))
        self.assertFalse((self.base / "scripts" / "memory" / "notes_log.txt").exists())

    def test_dispatcher_memory_intents_are_gated_and_logged(self):
        import dispatcher

        with patch.object(dispatcher, "get_brain", return_value=self.brain):
            with patch.object(dispatcher, "speak") as speak:
                self.assertEqual(
                    dispatcher.process("remember that my cat is Pixel"), "EXIT_LOOP"
                )
                self.assertEqual(dispatcher.process("forget my cat"), "EXIT_LOOP")
                self.assertEqual(
                    dispatcher.process("What do you remember about Pixel?"), "EXIT_LOOP"
                )
        self.assertEqual(len(list(self.brain.review.glob("*.md"))), 1)
        self.assertEqual(len(list(self.brain.knowledge.glob("*.md"))), 0)
        self.assertIn("not a confirmed fact", speak.call_args_list[0].args[0])
        self.assertIn("cannot delete", speak.call_args_list[1].args[0])
        self.assertIn("No approved memory", speak.call_args_list[2].args[0])


if __name__ == "__main__":
    unittest.main()
