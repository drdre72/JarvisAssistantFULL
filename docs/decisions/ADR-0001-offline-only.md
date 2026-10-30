# ADR-0001: Jarvis is fully offline at runtime

**Status:** accepted · **Date:** 2026-10-28

## Decision

Jarvis performs no network operations at runtime: no cloud inference, no vendor
API keys, no model downloads inside application code. Build-time asset staging
(wheelhouse, GGUF model, whisper model, llama.cpp binaries) is a separate,
user-approved step that never runs during app operation.

## Context

- The repo previously contained a hard-coded Picovoice key (compromised,
  external revocation pending) and a faster-whisper path that would download a
  model on first use.
- The user's explicit requirement: "Jarvis will be all offline."
- Long-term direction is an Obsidian-backed local memory layer — incompatible
  with hidden network egress.

## Consequences

- STT must load `models/whisper-small/` with `local_files_only=True`; bare
  model names are rejected by the bundle checker.
- `wake_listener.py` is dead code and stays dead.
- pip resolution uses `--no-index` + `wheelhouse/`; `wheelhouse.sha256` is the
  tracked integrity manifest.
- Any future feature needing network must be designed as an explicit,
  user-consented, opt-in boundary - never a silent fallback.
- Runtime network capabilities remain deferred until the local brain and
  decision controller, permission security, functionality and UI have been
  validated. The current controller may report that fresh data is needed,
  but it cannot fetch it.
