"""Read-only integrity checks for approved local Knowledge relationships."""

import argparse
from collections import defaultdict
from dataclasses import dataclass

from obsidian_memory import ObsidianBrain


@dataclass(frozen=True)
class GraphIssue:
    code: str
    source: str
    target: str = ""


def validate_graph(brain):
    graph = brain._get_graph()
    issues = set()
    ids = defaultdict(list)
    incoming = defaultdict(int)
    outgoing = defaultdict(int)
    dependencies = defaultdict(set)
    for label, filenames in graph.labels.items():
        if len(filenames) > 1:
            for filename in filenames:
                issues.add(GraphIssue("ambiguous_label", filename, label))
    for node in graph.nodes.values():
        if node.note_id:
            ids[node.note_id.casefold()].append(node.filename)
        for link in node.links:
            linked = graph.resolve(link.target)
            if linked is None:
                candidate = link.target + ".md"
                if brain._read_approved_node(candidate) is None and (
                    brain.knowledge / candidate
                ).is_file():
                    code = "unapproved_target"
                else:
                    code = "missing_target"
                issues.add(GraphIssue(code, node.filename, link.target))
                continue
            outgoing[node.filename] += 1
            incoming[linked.filename] += 1
            if link.relation == "depends_on":
                dependencies[node.filename].add(linked.filename)
            if link.relation == "contradicts":
                issues.add(GraphIssue("claim_conflict", node.filename, linked.filename))
    for filenames in ids.values():
        if len(filenames) > 1:
            for filename in filenames:
                issues.add(GraphIssue("duplicate_id", filename))
    for node in graph.nodes.values():
        if (node.properties.get("importance") or ("",))[0] == "high":
            if not incoming[node.filename] and not outgoing[node.filename]:
                issues.add(GraphIssue("important_orphan", node.filename))
            if not node.note_id:
                issues.add(GraphIssue("important_missing_id", node.filename))
    state = {}
    stack = []

    def visit(filename):
        state[filename] = 1
        stack.append(filename)
        for target in sorted(dependencies[filename]):
            if state.get(target) == 1:
                cycle = stack[stack.index(target):] + [target]
                issues.add(GraphIssue("dependency_cycle", filename, " -> ".join(cycle)))
            elif state.get(target, 0) == 0:
                visit(target)
        stack.pop()
        state[filename] = 2

    for filename in sorted(graph.nodes):
        if state.get(filename, 0) == 0:
            visit(filename)
    return sorted(issues, key=lambda issue: (issue.code, issue.source, issue.target))


def main():
    parser = argparse.ArgumentParser(description="Inspect approved local Knowledge links")
    parser.add_argument("--vault", help="Existing absolute local Obsidian vault")
    args = parser.parse_args()
    brain = ObsidianBrain(vault_path=args.vault, create=False)
    issues = validate_graph(brain)
    for issue in issues:
        print(f"{issue.code}: {issue.source}" + (f" -> {issue.target}" if issue.target else ""))
    print(f"{len(issues)} graph issue(s); no files modified")
    return 1 if issues else 0


if __name__ == "__main__":
    raise SystemExit(main())
