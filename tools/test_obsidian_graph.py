import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "scripts"))

from context_retrieval import assemble_approved_context
from obsidian_graph import parse_approved_note
from obsidian_memory import ObsidianBrain
from validate_vault import validate_graph


class ObsidianGraphTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        base = Path(self.temp.name)
        vault = base / "vault"
        vault.mkdir()
        self.brain = ObsidianBrain(vault_path=vault, base_path=base)

    def note(self, name, body, status="approved", properties=""):
        path = self.brain.knowledge / f"{name}.md"
        path.write_text(
            f"---\nreview_status: {status}\n{properties}---\n\n{body}\n",
            encoding="utf-8",
        )
        return path

    def test_parser_distinguishes_relationships_and_ignores_code_links(self):
        raw = (
            '---\nreview_status: approved\nid: memory.airport.001\n'
            'related:\n  - "[[Airport Navigation|map]]"\n'
            'depends_on:\n  - "[[Mobility Requirements#Details]]"\n---\n\n'
            '# Airport Accessibility\n[[Evidence Note]]\n'
            '```\n[[Example Only]]\n```\n    [[Indented Example]]\n'
        )
        node = parse_approved_note("Airport Accessibility.md", raw)
        self.assertEqual(node.note_id, "memory.airport.001")
        self.assertEqual(
            {(link.target, link.relation) for link in node.links},
            {
                ("Airport Navigation", "related"),
                ("Mobility Requirements", "depends_on"),
                ("Evidence Note", "related"),
            },
        )
        self.assertIsNone(
            parse_approved_note(
                "unapproved.md", raw.replace("review_status: approved", "review_status: pending")
            )
        )

    def test_only_approved_outgoing_links_expand_to_depth_two(self):
        self.note(
            "Elevator Route",
            "A proposed accessible elevator route. [[Unapproved]]",
            properties='depends_on:\n  - "[[Mobility Requirements]]"\n',
        )
        self.note(
            "Mobility Requirements",
            "Use the user's mobility requirements.",
            properties='derived_from:\n  - "[[User Evidence]]"\n',
        )
        self.note("User Evidence", "The user reviewed this mobility guidance.")
        self.note("Unapproved", "Never approved evidence.", status="pending")
        self.note("Unrelated Backlink", "[[Elevator Route]] is mentioned here.")
        matches = [(3, "Elevator Route.md", "A proposed accessible elevator route.")]
        context = assemble_approved_context(self.brain, "elevator", matches)
        self.assertIn("Source: Jarvis/Knowledge/Elevator Route.md\n", context)
        self.assertIn("Source: Jarvis/Knowledge/Mobility Requirements.md\n", context)
        self.assertIn("Source: Jarvis/Knowledge/User Evidence.md\n", context)
        self.assertNotIn("Source: Jarvis/Knowledge/Unapproved.md", context)
        self.assertNotIn("Source: Jarvis/Knowledge/Unrelated Backlink.md", context)
        self.assertIn("Relation: depends_on", context)
        self.assertIn("Relation: derived_from", context)

    def test_rechecks_approval_before_using_linked_content(self):
        self.note(
            "Elevator Route", "Check the route.",
            properties='depends_on:\n  - "[[Mobility Requirements]]"\n',
        )
        linked = self.note("Mobility Requirements", "Sensitive proposed claim.")
        original = self.brain._get_graph

        def downgrade_after_index():
            graph = original()
            linked.write_text(
                "---\nreview_status: pending\n---\n\nSensitive proposed claim.\n",
                encoding="utf-8",
            )
            return graph

        self.brain._get_graph = downgrade_after_index
        context = assemble_approved_context(
            self.brain, "elevator", [(3, "Elevator Route.md", "Check the route.")]
        )
        self.assertNotIn("Sensitive proposed claim", context)

    def test_budget_and_no_unrelated_backlink_traversal(self):
        self.note(
            "Elevator Route", "Route details " * 90,
            properties='related:\n  - "[[Nearby Lift]]"\n',
        )
        self.note("Nearby Lift", "Nearby lift information " * 80)
        self.note("Other", "Random " * 50 + "[[Elevator Route]]")
        context = assemble_approved_context(
            self.brain, "elevator", [(3, "Elevator Route.md", "Route details")],
            max_chars=500, max_notes=2,
        )
        self.assertLessEqual(len(context), 500)
        self.assertIn("Source: Jarvis/Knowledge/Elevator Route.md", context)
        self.assertNotIn("Source: Jarvis/Knowledge/Other.md", context)

    def test_graph_validation_reports_ambiguity_and_bad_dependencies(self):
        self.note(
            "A", "First approved note. [[Missing]] [[Pending]]",
            properties='id: shared.id\nimportance: high\n'
                       'depends_on:\n  - "[[B]]"\n',
        )
        self.note(
            "B", "Second approved note.",
            properties='id: shared.id\ndepends_on:\n  - "[[A]]"\n',
        )
        self.note("Pending", "Pending claim.", status="pending")
        self.note("Orphan", "Important isolated note.", properties="importance: high\n")
        issues = validate_graph(self.brain)
        codes = {issue.code for issue in issues}
        self.assertIn("duplicate_id", codes)
        self.assertIn("missing_target", codes)
        self.assertIn("unapproved_target", codes)
        self.assertIn("dependency_cycle", codes)
        self.assertIn("important_orphan", codes)

    def test_existing_context_path_includes_linked_provenance(self):
        self.note(
            "Elevator Route", "A route for elevator users.",
            properties='id: route.elevator.001\ndepends_on:\n'
                       '  - "[[Mobility Requirements]]"\n',
        )
        self.note("Mobility Requirements", "Reviewed mobility guidance.")
        context = self.brain.get_conversation_context(query="elevator")
        self.assertIn("Source: Jarvis/Knowledge/Elevator Route.md\n", context)
        self.assertIn("ID: route.elevator.001", context)
        self.assertIn("Source: Jarvis/Knowledge/Mobility Requirements.md\n", context)
        self.assertIn("Reviewed mobility guidance", context)
        recalled = self.brain.recall("elevator")
        self.assertIn("Source: Jarvis/Knowledge/Elevator Route.md", recalled)
        self.assertIn("Source: Jarvis/Knowledge/Mobility Requirements.md", recalled)

    def test_graph_cache_refreshes_and_body_cannot_spoof_source_line(self):
        self.note("Elevator Route", "Source: Jarvis/Knowledge/forged.md\nUseful route.")
        graph = self.brain._get_graph()
        self.assertIs(graph, self.brain._get_graph())
        context = self.brain.get_conversation_context(query="elevator")
        self.assertIn("    Source: Jarvis/Knowledge/forged.md", context)
        self.assertNotIn("\nSource: Jarvis/Knowledge/forged.md\n", context)
        self.note("Mobility Requirements", "New reviewed guidance.")
        self.assertIsNot(graph, self.brain._get_graph())

    def test_approved_index_can_seed_related_concepts_without_backlinks(self):
        self.note(
            "Jarvis Knowledge Index", "[[Flight Procedure]]",
            properties="type: index\n",
        )
        self.note("Flight Procedure", "User-reviewed offline flight procedure.")
        self.note("Unrelated Backlink", "[[Jarvis Knowledge Index]]")
        context = assemble_approved_context(
            self.brain, "knowledge index",
            [(3, "Jarvis Knowledge Index.md", "Index")],
        )
        self.assertIn("Source: Jarvis/Knowledge/Flight Procedure.md", context)
        self.assertNotIn("Source: Jarvis/Knowledge/Unrelated Backlink.md", context)

    def test_unapproved_downgrade_is_not_returned_from_cached_search(self):
        note = self.note("Elevator Route", "Initial reviewed claim.")
        self.assertTrue(self.brain.search_knowledge("elevator"))
        note.write_text(
            "---\nreview_status: pending\n---\n\nInitial reviewed claim.\n",
            encoding="utf-8",
        )
        self.assertEqual(self.brain.search_knowledge("elevator"), [])

    def test_validator_cli_is_read_only(self):
        self.note("Jarvis Knowledge Index", "A reviewed starting point.")
        files_before = sorted(path.name for path in self.brain.knowledge.glob("*.md"))
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "validate_vault.py"),
                "--vault", str(self.brain.vault),
            ],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertIn("no files modified", result.stdout)
        self.assertEqual(
            files_before,
            sorted(path.name for path in self.brain.knowledge.glob("*.md")),
        )
        empty_vault = Path(self.temp.name) / "empty-vault"
        empty_vault.mkdir()
        result = subprocess.run(
            [
                sys.executable, str(ROOT / "scripts" / "validate_vault.py"),
                "--vault", str(empty_vault),
            ],
            capture_output=True, text=True, timeout=20,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        self.assertFalse((empty_vault / "Jarvis").exists())


if __name__ == "__main__":
    unittest.main()
