"""Read-only wikilink graph over manually approved Jarvis Knowledge notes."""

import re
from dataclasses import dataclass
from pathlib import Path


_LINK = re.compile(r"(?<!!)\[\[([^\[\]\r\n]{1,200})\]\]")
_PROPERTY = re.compile(r"^([a-z][a-z0-9_-]*):\s*(.*)$", re.I)
_RELATIONS = ("related", "depends_on", "derived_from", "used_by", "contradicts")


@dataclass(frozen=True)
class Link:
    target: str
    relation: str


@dataclass(frozen=True)
class KnowledgeNode:
    filename: str
    note_id: str
    title: str
    body: str
    links: tuple[Link, ...]
    properties: dict[str, tuple[str, ...]]


def _link_target(raw):
    target = raw.split("|", 1)[0].split("#", 1)[0].strip()
    if target.startswith("Jarvis/Knowledge/"):
        target = target[len("Jarvis/Knowledge/"):]
    if target.lower().endswith(".md"):
        target = target[:-3]
    if not target or target in {".", ".."} or "/" in target or "\\" in target:
        return None
    if "\x00" in target or ":" in target:
        return None
    return target


def _active_body_links(body):
    fence = None
    for line in body.splitlines():
        trimmed = line.lstrip()
        if trimmed.startswith(("```", "~~~")):
            marker = trimmed[:3]
            fence = None if fence == marker else marker if fence is None else fence
            continue
        if fence or line.startswith(("    ", "\t")):
            continue
        for match in _LINK.finditer(line):
            yield match.group(1)


def parse_approved_note(filename, raw):
    if not filename.lower().endswith(".md") or not raw.startswith("---\n"):
        return None
    try:
        header, body = raw[4:].split("\n---\n", 1)
    except ValueError:
        return None
    properties = {}
    active = None
    for line in header.splitlines():
        field = _PROPERTY.fullmatch(line)
        if field:
            key = field.group(1).lower()
            if key in properties:
                return None
            value = field.group(2).strip()
            properties[key] = [value] if value else []
            active = key
        elif active and line.lstrip().startswith("- "):
            properties[active].append(line.lstrip()[2:].strip())
        elif line.strip():
            active = None
    if properties.get("review_status") != ["approved"]:
        return None
    links = []
    for relation in _RELATIONS:
        for value in properties.get(relation, ()):
            for match in _LINK.finditer(value):
                target = _link_target(match.group(1))
                if target:
                    links.append(Link(target, relation))
    for raw_link in _active_body_links(body):
        target = _link_target(raw_link)
        if target:
            links.append(Link(target, "related"))
    return KnowledgeNode(
        filename=filename,
        note_id=(properties.get("id") or [""])[0].strip("\"'"),
        title=(properties.get("title") or [Path(filename).stem])[0].strip("\"'"),
        body=body.strip(),
        links=tuple(dict.fromkeys(links)),
        properties={key: tuple(values) for key, values in properties.items()},
    )


class VaultGraph:
    def __init__(self, nodes):
        self.nodes = {node.filename: node for node in nodes}
        labels = {}
        for node in self.nodes.values():
            for label in (Path(node.filename).stem, node.title, node.note_id):
                if label:
                    labels.setdefault(label.casefold(), set()).add(node.filename)
        self.labels = labels

    def resolve(self, target):
        label = _link_target(target)
        if label is None:
            return None
        filenames = self.labels.get(label.casefold(), ())
        if len(filenames) != 1:
            return None
        return self.nodes[next(iter(filenames))]

    def outgoing(self, node):
        for link in node.links:
            linked = self.resolve(link.target)
            if linked is not None and linked.filename != node.filename:
                yield link, linked

    def backlinks(self, node):
        for source in self.nodes.values():
            for link, linked in self.outgoing(source):
                if linked.filename == node.filename:
                    yield link, source
