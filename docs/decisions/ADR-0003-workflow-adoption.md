# ADR-0003: Agent workflow adopted from the Lute project

**Status:** accepted · **Date:** 2026-10-28

## Decision

Port the Lute project's agent-facing workflow into Jarvis:

- `AGENTS.md` — stable knowledge cache (rules, layout, env vars, gotchas).
- `JARVIS_STATE.md` — single-page "what is true right now".
- `PROGRESS_LOG.md` — append-only work log (supersedes unreliable
  `progress.txt`), appended via `tools/append_progress.py`.
- `CURRENT_ISSUES.md` — numbered buglist with ACTIVE/OPEN/PENDING VERIFY states.
- `.devin-context/memory.md` — rolling session memory re-injected by
  `.devin/hooks.v1.json` (SessionStart/PostCompaction full, UserPromptSubmit
  compact), plus `byte-tracker.ps1` context-budget nudge.
- `.devin/rules/` — core + workflow rules for agents.
- `tools/verify.ps1` — verification loop writing `reports/verify_<ts>.txt`.
- `tools/checklist_tool.py` — on-disk checklist for multi-step tasks.
- `docs/decisions/` — ADRs (this file is the first of them).

## Rationale

Jarvis had a contradictory `progress.txt`, no agent memory, no issue tracker,
and no repeatable verification loop. Lute's pattern was proven on this machine
across many agent sessions and maps cleanly onto this repo.

## Consequences

- Multiple canonical truth files exist; the priority order in
  `.devin/rules/jarvis-agent-workflow.md` resolves disagreements.
- `reports/` and `.devin-context/tally_*.txt` are gitignored.
- `progress.txt` remains in the tree as historical record only.
