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
objective truth. Retrieval is lexical (matching words in file names/text),
not embeddings or model-generated "facts." Relevant approved notes are
quoted with their source path in the model prompt; recent dialogue and
legacy JSON are separately labelled unverified. Obsidian review is manual.

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

The conversation model remains available for ordinary dialogue. It cannot
issue an action request into this gate; a generated sentence is never
reparsed as a command. Further NLP intents require explicit patterns,
typed validation, a permission policy, and regression tests.

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
