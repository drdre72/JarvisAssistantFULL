# Jarvis's offline Obsidian brain

Jarvis writes and reads ordinary Markdown files. Obsidian is an optional
viewer/editor of the same directory; no plugin, local API server, cloud
account, sync service, or network connection is required by Jarvis.

## Choose a vault

By default Jarvis creates `memory/obsidian-vault/` inside this checkout on its
first memory operation. `memory/` is gitignored; personal notes never belong
in a commit. Open `memory/obsidian-vault/` as a vault in Obsidian if desired.
The old `memory/conversations.json` is **not** deleted or overwritten: existing
conversations are read as unverified context alongside new Markdown entries.
Any old `scripts/memory/notes_log.txt` also remains untouched; it is not
automatically imported or treated as approved knowledge.

To use an existing vault instead, set `JARVIS_OBSIDIAN_VAULT` to its **existing
absolute directory** before launching Jarvis. Jarvis creates and owns only a
`Jarvis/` subfolder there. A missing/relative/symlinked vault fails closed
rather than writing to an unintended location. Jarvis never scans other vault
folders. No files are copied out of your previous vault automatically.

Disable Obsidian Sync and any network-connected community plugins if you
also want the *Obsidian application* to remain offline. Jarvis itself makes
no network calls for memory operations.

## Trust and review

| Folder | Who writes | Jarvis reads it as |
| --- | --- | --- |
| `Jarvis/Conversations/` | Jarvis, after a reply | Unverified dialogue. Model output is never a fact. |
| `Jarvis/Notes/` | Explicit "write this down" | User note; not automatically used as a fact. |
| `Jarvis/Review/` | Explicit "remember that" | Pending candidate; not used as approved knowledge. |
| `Jarvis/Knowledge/` | User in Obsidian | Reviewed context, only with `review_status: approved`. |
| `Jarvis/Core/Purpose.md` | User only | Optional self-purpose record, only with `jarvis_type: purpose` and `review_status: approved`. |

The local vault is Jarvis's inspectable memory; Obsidian is only one way to
view and edit it. Jarvis never creates `Core/Purpose.md` or fills in its
contents. To define his purpose, create `Jarvis/Core/Purpose.md` yourself,
write your own statement beneath the frontmatter, review it, then change
`pending` to `approved`:

```markdown
---
jarvis_type: purpose
review_status: pending
---

<Your reviewed purpose statement here>
```

Only the approved note at that exact path is read for self-purpose questions.
It is a user-authored goal, not an instruction granting tools, network access,
or permission to edit other files. No self-purpose is inferred from dialogue,
generated answers or linked notes when the profile is missing.

To approve a candidate, *you* move/copy/edit the note into
`Jarvis/Knowledge/`, change its frontmatter to `review_status: approved`,
and correct the content. Example:

```markdown
---
review_status: approved
---

My preferred name is Alex.
```

Jarvis does not automatically promote speech or generated answers into
Knowledge. Approval means user-reviewed, **not independently verified**
objective truth. Retrieval starts with a lexical match against approved
Knowledge, then may follow relevant approved outgoing wikilinks to depth 2.
It does not use embeddings or model-generated "facts." Selected notes are
re-read to confirm approval before use. Context preserves source file paths,
optional IDs, relationships and indented note excerpts; recent dialogue and legacy JSON
remain separately labelled unverified. Obsidian review is manual.

## Linked Knowledge

Approved files directly under `Jarvis/Knowledge/` can use ordinary Obsidian
`[[wikilinks]]`. An optional `id` and relationship properties make the
connection meaningful to Jarvis:

```markdown
---
id: memory.airport_accessibility.001
type: knowledge
review_status: approved
importance: high
related:
  - "[[Airport Navigation]]"
depends_on:
  - "[[Mobility Requirements]]"
derived_from:
  - "[[Reviewed Evidence]]"
used_by:
  - "[[Route Planner]]"
contradicts:
  - "[[Conflicting Note]]"
---

# Airport Accessibility

See [[Airport Navigation]] for related context.
```

`review_status: approved` is required; `status: approved` alone is not
recognized. Each linked target must itself be an approved Knowledge note;
linking to a pending note cannot approve it. Targets resolve by filename
stem, `title` or `id`; ambiguous names are not followed. Links in indented
or fenced code are ignored. Relationships describe context, not proof that
either note is true. Only `depends_on` cycles are flagged as invalid;
ordinary related-topic cycles are allowed.

The local graph index caches approved metadata and refreshes when file
timestamps/sizes change; selected notes are re-read before entering
context. Expansion follows outgoing links, not arbitrary backlinks, and
stops after two hops, six notes or a 3500-character Knowledge budget.
Time-sensitive notes can declare `freshness: time_sensitive` and an ISO
`updated` date; older notes rank lower, but this never makes historical
information live. A manually authored approved
`Jarvis/Knowledge/Jarvis Knowledge Index.md` with `type: index` can serve
as a map of content. Jarvis does not create or edit index notes.

Run `.\.venv\Scripts\python.exe scripts\validate_vault.py` to inspect the
default vault, or pass `--vault` with an existing absolute vault path. This
read-only checker reports unresolved/unapproved links, duplicate IDs,
ambiguous labels, isolated `importance: high` notes, explicit contradictions
and dependency cycles. It cannot independently verify claims or infer
unrecorded conflicts. This first slice reads at most 200 flat Knowledge
notes of up to 32 KB each; nested files and full YAML/Obsidian alias syntax
are not yet indexed.

## Deterministic logic gate

Adapted from Lute's `NlpParser`/`GrammarParser` and typed
`NpcActionDispatcher` boundary, **not** Lute's NPC rule forbidding LLM
conversation. `scripts/intent_gate.py` parses the original user text into a
typed `Intent` (verb, topic, payload, confidence, negation) without an LLM.
The gate authorizes only explicit, leading high-confidence phrases from
user voice/text, and the memory authority performs the allowed I/O.

- `write this down: <text>` saves an unverified local note.
- `remember that <text>` creates a pending memory in Review.
- `what do you remember about <topic>` reads only approved Knowledge.
- `forget <topic>` refuses deletion; edit your vault directly.
- Questions, negated forms, ambiguous clauses, and model-generated text
  **cannot** authorize a write. A missing payload asks for clarification.

The conversation model remains available for ordinary dialogue. For uncanned
requests it proposes a typed local interpretation; self-purpose and
capability answers are grounded in the approved profile or registry rather
than model-authored claims. Its draft for ordinary dialogue remains generated,
unverified content. The model cannot issue an action request into the gate;
a generated sentence is never reparsed as a command. Further tool intents
still require typed validation, permissions and regression tests.

The separate local decision controller consults approved Knowledge only
when an explicit memory request or a strong match to a personal question
justifies retrieval. Linked approved context is bounded and provenance
labelled. Ordinary conversation can include recent unverified dialogue but
does not automatically insert every Knowledge note. Local CPU and memory
readings are obtained without a model call. Requests for changing flight,
weather, news or traffic information receive an explicit offline limitation,
never a fabricated live lookup. This is not autonomous planning or simulation.

## Boundaries and next work

This is a **memory/command authorization gate**, not a general process or
filesystem sandbox. A malicious local process with your filesystem access
can modify vault files. Retrieved Markdown may contain prompt-injection
text; it is labelled as data and cannot trigger Jarvis tool execution, but
the model may still repeat or be influenced by it. Evaluate a sandboxed
tool executor before adding more commands.

No bulk legacy JSON migration occurs. The old JSON remains read-only in
Jarvis's runtime context, and a separate, user-reviewed migration may be
added later. Multi-intent and conditional utterances are deliberately not
executed as actions. Runtime voice behavior still needs a live microphone
test after this change; unit tests exercise the local files and logic gate.
