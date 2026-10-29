# Jarvis Agent Workflow

This workflow governs substantive Devin coding sessions on Jarvis.

## Before coding

For any task involving architecture, memory, inference, audio, packaging, or
the offline bundle:

1. Read `AGENTS.md` for stable project knowledge and gotchas.
2. Read `JARVIS_STATE.md` for current truth.
3. Read `CURRENT_ISSUES.md` before assuming something is unbroken or unbuilt.
4. Inspect the actual implementation and tests before changing it.
5. `progress.txt` and old README claims are unreliable — do not trust them.

Do not rely on model memory when repository state can answer the question.

## During coding

- Make the smallest coherent change that advances the active target.
- Preserve offline guarantees: no runtime downloads, no vendor keys.
- Keep memory, imagination, and verified facts separate — generated content
  never silently becomes durable memory.
- Fix root causes, not symptoms. Never apply shotgun fixes; trace the failure
  path first (logs, stack traces, state).
- Do not duplicate knowledge into rolling memory that belongs in `AGENTS.md`,
  `JARVIS_STATE.md`, `CURRENT_ISSUES.md`, or an ADR.

## Verification gate

Before reporting work as complete:

1. Run `powershell -File tools\verify.ps1` (bundle check + tests + compileall
   + git hygiene, saved to `reports\verify_<ts>.txt`).
2. If runtime behavior changed, exercise the real path (module-level or app
   run), not just mocks.
3. Confirm the result came from the current run, not stale state.
4. If verification fails, report the failure and fix it — do not mark done.

## After coding

Update durable project knowledge only when it changed:

- `JARVIS_STATE.md` — implementation status, blockers, next target.
- `CURRENT_ISSUES.md` — issue states (ACTIVE/OPEN/PENDING VERIFY/RESOLVED).
- `PROGRESS_LOG.md` — one line per completed task
  (`.\.venv\Scripts\python.exe tools\append_progress.py --task X --result Y`).
- `docs/decisions/ADR-*.md` — durable architectural decisions and rationale.
- `.devin-context/memory.md` — short-lived session notes and live TODOs.

Prefer canonical files over memory append operations for durable facts.

## Task handoff format

When a task reaches a stable stopping point, leave enough state for another
agent to continue:

- what changed;
- what was verified;
- what remains broken;
- exact next target;
- any new decision or constraint.

## Priority order

When sources disagree, use this order and reconcile conflicts instead of
guessing:

`AGENTS.md` → `JARVIS_STATE.md` → `CURRENT_ISSUES.md` → ADRs → rolling memory
→ chat/model recollection.
