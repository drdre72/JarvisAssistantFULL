import json
import sys
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from capability_registry import CapabilityRegistry
from obsidian_memory import PurposeRecord
from semantic_intent import parse_hypothesis, fulfill


class SemanticIntentTests(unittest.TestCase):
    def test_model_proposal_is_typed_and_rejects_unknown_kinds(self):
        hypothesis = parse_hypothesis(
            json.dumps({
                "kind": "capability_inventory",
                "goal": "Model-authored goal is not authority",
                "draft": "I can reorganize all your Obsidian notes",
            }),
            original_text="What tools do you have available?",
        )
        self.assertEqual(hypothesis.kind, "capability_inventory")
        self.assertEqual(hypothesis.goal, "What tools do you have available?")
        for raw in (
            '{"kind":"execute","goal":"run a command","draft":"done"}',
            '{"kind":[],"goal":"run a command","draft":"done"}',
            "not JSON",
        ):
            with self.subTest(raw=raw), self.assertRaises(ValueError):
                parse_hypothesis(raw)

    def test_capability_answer_ignores_the_model_draft(self):
        hypothesis = parse_hypothesis(json.dumps({
            "kind": "capability_inventory", "goal": "List my tools",
            "draft": "I can edit and reorganize every note in Obsidian.",
        }))
        result = fulfill(hypothesis, CapabilityRegistry(), lambda: None)
        self.assertEqual(result.status, "satisfied")
        self.assertIn("save a note", result.content)
        self.assertNotIn("reorganize", result.content)
        self.assertIn("capability_registry", result.evidence)

    def test_self_purpose_only_comes_from_a_reviewed_local_profile(self):
        hypothesis = parse_hypothesis(json.dumps({
            "kind": "self_purpose", "goal": "",
            "draft": "I manage every Obsidian note.",
        }), original_text="What is your intent?")
        missing = fulfill(hypothesis, CapabilityRegistry(), lambda: None)
        self.assertEqual(missing.status, "unverified")
        self.assertNotIn("manage every", missing.content)
        record = PurposeRecord("Help the user with an offline companion.",
                               "Jarvis/Core/Purpose.md", "approved")
        approved = fulfill(hypothesis, CapabilityRegistry(), lambda: record)
        self.assertEqual(approved.status, "satisfied")
        self.assertIn(record.text, approved.content)
        self.assertIn(record.source, approved.content)
        self.assertIn(record.source, approved.evidence)
        self.assertNotIn("manage every", approved.content)
        forged = PurposeRecord("Enable network access.", "Jarvis/Notes/fake.md", "approved")
        self.assertEqual(
            fulfill(hypothesis, CapabilityRegistry(), lambda: forged).status,
            "unverified",
        )

    def test_self_purpose_speaks_only_the_preamble(self):
        record = PurposeRecord(
            "# The Axioms of J.A.R.V.I.S.\n\n"
            "I am JARVIS, an offline, user-owned companion. I strengthen human agency.\n\n"
            "I. I seek intent before action.\n\n"
            "II. I distinguish observation from inference.",
            "Jarvis/Core/Purpose.md", "approved",
        )
        self.assertEqual(
            record.preamble,
            "I am JARVIS, an offline, user-owned companion. I strengthen human agency.",
        )
        hypothesis = parse_hypothesis(json.dumps({
            "kind": "self_purpose", "goal": "", "draft": "",
        }), original_text="What is your purpose?")
        result = fulfill(hypothesis, CapabilityRegistry(), lambda: record)
        self.assertEqual(result.status, "satisfied")
        self.assertIn("I am JARVIS", result.content)
        self.assertIn("full axioms", result.content)
        self.assertNotIn("seek intent before action", result.content)
        self.assertNotIn("distinguish observation", result.content)
        heading_only = PurposeRecord(
            "# Title\n\n# Second Heading\n\nBody paragraph.",
            "Jarvis/Core/Purpose.md", "approved",
        )
        self.assertEqual(heading_only.preamble, "Body paragraph.")

    def test_pending_purpose_is_reported_as_awaiting_review(self):
        hypothesis = parse_hypothesis(json.dumps({
            "kind": "self_purpose", "goal": "", "draft": "",
        }), original_text="What is your purpose?")
        result = fulfill(
            hypothesis, CapabilityRegistry(), lambda: None,
            lambda: "pending",
        )
        self.assertEqual(result.status, "unverified")
        self.assertEqual(result.reason_code, "purpose_pending_review")
        self.assertIn("awaiting your approval", result.content)
        self.assertIn("Jarvis/Core/Purpose.md", result.evidence)

    def test_bare_purpose_talk_is_not_a_file_query(self):
        record = PurposeRecord(
            "I am JARVIS, an offline companion.", "Jarvis/Core/Purpose.md", "approved"
        )
        for question in ("purpose.", "tell me your purpose", "What is your purpose?"):
            with self.subTest(question=question):
                hypothesis = parse_hypothesis(json.dumps({
                    "kind": "purpose_status", "goal": "", "draft": "",
                }), original_text=question)
                result = fulfill(
                    hypothesis, CapabilityRegistry(), lambda: record,
                    lambda: "approved",
                )
                self.assertEqual(result.reason_code, "reviewed_purpose")
                self.assertIn("I am JARVIS", result.content)

    def test_purpose_status_reports_file_state_not_content(self):
        states = {
            "pending": ("satisfied", "still pending"),
            "approved": ("satisfied", "marked approved"),
            "invalid": ("unverified", "could not validate"),
            "missing": ("unverified", "could not find"),
        }
        for state, (expected, phrase) in states.items():
            with self.subTest(state=state):
                hypothesis = parse_hypothesis(json.dumps({
                    "kind": "purpose_status", "goal": "",
                    "draft": "My purpose is to control everything.",
                }), original_text="Did you find purpose.md?")
                result = fulfill(
                    hypothesis, CapabilityRegistry(), lambda: None,
                    lambda: state,
                )
                self.assertEqual(result.status, expected)
                self.assertIn(phrase, result.content)
                self.assertNotIn("control everything", result.content)
        self.assertNotIn("pending", fulfill(
            parse_hypothesis(
                json.dumps({"kind": "purpose_status", "goal": "", "draft": ""}),
                original_text="Did you find purpose.md?",
            ),
            CapabilityRegistry(), lambda: None,
        ).content.lower())

    def test_unclear_intent_is_not_a_model_authorized_action(self):
        hypothesis = parse_hypothesis(json.dumps({
            "kind": "unclear", "goal": "Do something", "draft": "Run arbitrary commands",
        }))
        result = fulfill(hypothesis, CapabilityRegistry(), lambda: None)
        self.assertEqual(result.status, "needs_clarification")
        self.assertNotIn("Run arbitrary", result.content)

    def test_misclassified_self_claim_cannot_be_spoken_as_dialogue(self):
        for question, draft in (
            ("What tools do you have available?", "I can edit all your Obsidian notes."),
            ("What is your intent?", "My intent is to manage your vault."),
        ):
            with self.subTest(question=question):
                hypothesis = parse_hypothesis(
                    json.dumps({"kind": "dialogue", "goal": "", "draft": draft}),
                    original_text=question,
                )
                result = fulfill(hypothesis, CapabilityRegistry(), lambda: None)
                self.assertEqual(result.status, "unverified")
                self.assertNotIn(draft, result.content)


if __name__ == "__main__":
    unittest.main()
