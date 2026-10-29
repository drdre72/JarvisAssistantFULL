# ADR-0004: Offline Obsidian vault and deterministic memory gate

**Status:** accepted for local MVP

## Decision

Jarvis uses an inspectable local Markdown vault as the active conversation
memory store. The default vault is gitignored under `memory/obsidian-vault/`;
an existing absolute vault path may be selected explicitly with
`JARVIS_OBSIDIAN_VAULT`. Jarvis writes only within its `Jarvis/` subtree.
Old JSON conversations remain unmodified and available as read-only,
unverified context.

Dialogue, ordinary notes, pending memory candidates, and user-reviewed
Knowledge are separate folders. Only manually edited files in Knowledge
with `review_status: approved` enter approved retrieval; approval does
not imply independent factual verification.

We adapt Lute's ordered NLP parsing, negation check, typed intent and
validation-before-domain-authority pattern. Jarvis accepts only explicit
user-origin memory commands through this deterministic gate. The local LLM
can converse and read labelled context, but may not authorize actions or
silently promote its own output to knowledge.

## Alternatives rejected

- Giving the LLM write access to an entire vault would confuse imagination,
  dialogue and facts, and expose arbitrary note edits to prompt injection.
- Calling Obsidian plugins or an HTTP API would add needless processes and
  potentially violate the offline constraint.
- Replacing the old JSON in place risks losing existing user conversations.
- Porting Lute's S&Box/NPC domain rules into Jarvis is not appropriate;
  only the explicit parsing and action-authorization boundary applies.

## Consequences

The vault works with Obsidian closed and requires no new dependencies.
Lexical retrieval is limited and reviewed notes remain user-supplied, not
proven facts. This gate is not an OS sandbox; broader tools, conflict
resolution, encryption, multi-intent NLP and optional legacy migration are
future work. See `OBSIDIAN_BRAIN.md` for setup and review instructions.
