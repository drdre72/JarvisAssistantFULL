# AGENTS.md — Jarvis Agent Knowledge Cache

Persistent, hand-maintained notes for AI agents working on this repo.
Stable facts live here; dynamic state belongs in `JARVIS_STATE.md`;
session-scoped notes belong in `.devin-context/memory.md`.

## GOVERNING RULES

1. **Jarvis is fully offline at runtime.** No cloud inference, no vendor
   wake-word keys, no model downloads inside application code paths. Build-time
   asset staging (wheelhouse, models, binaries) is a separate, approved step.
   Outward APIs are deferred until the local brain/controller, security,
   functionality and UI have been validated. No network tools are enabled.
2. **No credentials in the repo.** The historical Picovoice key is compromised;
   `scripts/wake_listener.py` is deliberately disabled and must not be revived.
   `JARVIS_PICOVOICE_ACCESS_KEY` must not be reintroduced.
3. **Memory, imagination, and facts are separate.** Retrieved memory,
   generated content, and verified facts must not silently mix. This governs
   the future Obsidian memory layer.
4. **Prefer repository state over model memory.** Check files and run the
   verification loop before asserting something is done.
5. **Intent-to-fulfillment is the target, not phrase matching.** Interpret
   the user's goal, constraints and needed evidence; define what would
   satisfy the request; choose permitted capabilities; verify the outcome.
   Reply with a supported result, or a concise explanation of missing
   inputs, unavailable capabilities, failed checks or required permission.
   Label partial results as partial. Current keyword responses are temporary
   testing safeguards, not the long-term decision architecture. Model text
   may propose a plan but never authorize side effects.

## Communication failure contract (target; not yet implemented)

- A voice turn passes through capture, transcription, semantic intent
  interpretation, and fulfillment. Each stage should return a typed outcome
  with stage, reason category, supporting measurements or observations,
  uncertainty, and a suitable retry or clarification action. Text input
  enters at interpretation. Do not collapse every empty transcription into
  "the user was silent," or confuse a known goal with unavailable tools.
- Candidate categories include no speech detected; speech too quiet relative
  to a calibrated noise floor; clipped/saturated samples; background
  interference with measured speech-to-noise evidence; recording cut short;
  uncertain transcription; ambiguous intent; missing critical inputs;
  unavailable capability or permission; device/model failure; and unknown
  cause. Classify only when the relevant evidence exists. Loudness alone
  cannot prove background noise or clipping; a failed intent parse does not
  establish an audio fault. If evidence conflicts, report uncertainty.
- Audio diagnosis first needs correct normalized sample metrics, clipping
  fraction, recording stop reason, and a calibrated speech/noise estimate.
  The current `speech_recognition.py` squares `int16` samples before widening:
  this overflows (samples at amplitude 30000 can yield RMS 0). Its current
  numeric thresholds must be recalibrated along with any arithmetic fix.
  Transcription quality signals require validation against real recordings
  before being treated as calibrated confidence.
- A constrained offline response renderer should turn the typed outcome into
  a brief, polite explanation and one actionable retry hint. It may vary
  wording but cannot invent an acoustic cause or change the reason category;
  avoid a table of canned category-to-sentence responses. If language
  generation is unavailable, the UI can show the structured category and
  hint without pretending to know more. Diagnostics in local logs should
  store reason codes/metrics, not raw audio or transcripts. Uncertain speech
  never authorizes a memory write or tool action without normal validation.

## Stack and runtime

- Windows-only desktop app: Python 3.11 x64 + Flet 0.21.2 UI.
- Inference: `bin/llama-completion.exe` (llama.cpp b11985, win-cpu-x64) driven
  by `scripts/reasoning.py`. `llama-cli.exe` is **chat-mode only** in modern
  llama.cpp — always use `llama-completion.exe` for raw prompt completion.
- STT: `scripts/speech_recognition.py` → faster-whisper loading
  `models/whisper-small/` with `local_files_only=True`. Never pass a bare model
  name — that silently downloads.
- TTS: `scripts/speaker.py` → `pyttsx3` (Windows SAPI). Do not shell out with
  interpolated text (previous code had a command-injection bug here).
- Memory: `scripts/obsidian_memory.py` writes Markdown to the default ignored
  `memory/obsidian-vault/` or a deliberately chosen existing vault. Old
  `scripts/memory_system.py` JSON is read-only legacy context in the live app.
  `OBSIDIAN_BRAIN.md` explains approval and provenance.
- The Markdown vault is part of Jarvis's local identity and memory; Obsidian
  is an optional viewer/editor, not an external vault-management tool.
  `Jarvis/Core/Purpose.md` is an optional user-authored, manually approved
  self-purpose record. Jarvis never creates or promotes it, and purpose text
  cannot grant permissions or override the offline policy.
- Voice dispatcher: only local note-taking is registered. Legacy macOS
  commands and avatar playback are not supported on Windows; do not re-add
  them before implementing and testing a sandboxed local replacement.
- Dispatcher recognizes explicit leading "write this down" and "remember
  that" requests, approved-memory recall and refused deletion before
  conversation. Never let model output authorize tool execution; future tool
  intents require deterministic validation.
- `scripts/intent_gate.py` adapts Lute's ordered parse -> typed intent ->
  authorization -> domain authority pattern. "Remember that" goes to Review,
  never Knowledge; only manually approved Knowledge files are retrieved.
- `scripts/capability_registry.py` declares actual local capabilities and
  evidence; `scripts/decision_controller.py` chooses only read-only local
  metrics, relevant approved-memory context, ordinary conversation, or a
  truthful offline/unknown response. This is not a general agent or sandbox.
- For uncanned conversation, `scripts/semantic_intent.py` validates a
  constrained local-model hypothesis. Capability and purpose answers ignore
  model drafts and use registry/profile data; ordinary dialogue remains
  generated and unverified. This is a first slice, not a general planner or
  independently verified intent classifier.
- `scripts/obsidian_graph.py` indexes only approved flat Knowledge notes;
  `scripts/context_retrieval.py` follows relevant outgoing wikilinks at
  most two hops under a context budget; `scripts/validate_vault.py` checks
  graph integrity without writing notes. No link promotes an unapproved
  note, no backlinks are traversed automatically, and relationship edges
  never prove a claim. Source paths remain in assembled context.
- `JARVIS_OBSIDIAN_VAULT` - optional existing absolute Obsidian vault path;
  omit for ignored project-local default. No network/plugin calls for memory.
- Current time/date and UI/tool visibility questions are answered from the
  local clock and capability registry, not model recollection. Do not ask
  the model to invent operational state or timestamps.
- Model: `models/qwen2.5-7b-instruct-q4_k_m.gguf` (Apache-2.0, ungated).
  ~7.5 tok/s on this CPU.

## Environment variables

- `JARVIS_BASE_PATH`, `JARVIS_APP_PATH` — set by `main.py`; STT respects
  `JARVIS_BASE_PATH` for the models dir.
- `JARVIS_GPU_LAYERS` — default `0` (CPU build staged). Raise only when a
  GPU llama.cpp build is staged in `bin/`.
- `JARVIS_LLAMA_THREADS` — default `min(8, cpu_count)`.
- `JARVIS_LLAMA_TIMEOUT` — seconds, default `120`.

## Running

- Always launch via `launch_jarvis.bat` (uses `.venv\Scripts\python.exe`).
- Bare `python` resolves to the **system** Python 3.11 with no deps — or the
  Windows Store alias on a stale PATH. This was a real failure mode.
- Dev commands must use `.\.venv\Scripts\python.exe` explicitly; this terminal's
  PATH was created before Python was installed.

## Verification loop (run after every change)

```powershell
powershell -File tools\verify.ps1
```

Writes `reports\verify_<timestamp>.txt` (gitignored) covering: offline bundle
check, unit tests, `compileall`, and git hygiene. Individual pieces:

```powershell
.\.venv\Scripts\python.exe tools\check_offline_bundle.py
.\.venv\Scripts\python.exe -m unittest discover -s tools -p 'test_*.py' -v
.\.venv\Scripts\python.exe -m compileall -q main.py scripts tools
```

## Known gotchas (learned the hard way)

- **flet 0.21 API**: `page.window` does not exist — use `page.window_*`
  attributes (`page.window_width`, `page.window_maximized`, ...). The code was
  written against the newer `page.window.*` API once; 0.21.2 is the pin.
- **`page.window.*` vs `page.window_*`** was the first-launch crash.
- **Shell quoting**: this repo runs under PowerShell — `2>'$env:TEMP\x'`
  (single quotes) does not expand. Use double quotes for env paths.
- **PowerShell `curl`** is an alias for `Invoke-WebRequest`; use `curl.exe`
  for real downloads.
- **`[IO.File]::ReadAllBytes` fails on files >2 GB** — use a FileStream to
  read headers of GGUF files.
- **llama.cpp output**: `-v` writes logs to stderr; response stats lines look
  like `[ Prompt: ... t/s ]` on stdout — `reasoning.py` filters them.
- **Stale docs**: `progress.txt` and older README/SETUP claims are historical
  and partially false. `PROGRESS_LOG.md` + `JARVIS_STATE.md` are canonical now.
- **Garbled emoji**: several files (`launch_jarvis_full.command`,
  `tools/build_package.py`, `test_llama.py`) contain mojibake from earlier
  encoding issues; replace rather than matching on emoji in patches.

## Repository layout

- `main.py` — launcher: env setup, dependency check, asset check, Flet start.
- `launch_jarvis.bat` — correct entry point (venv-aware).
- `scripts/` - app modules (`jarvis_app.py` UI, `reasoning.py`, `dispatcher.py`,
  `capability_registry.py`, `decision_controller.py`, `semantic_intent.py`,
  `obsidian_graph.py`, `context_retrieval.py`, `validate_vault.py`,
  `jarvis_commands.py`,
  `speech_recognition.py`, `speaker.py`,
  `runtime_log.py` (rotating stage diagnostics), `memory_system.py`,
  `wake_listener.py` DISABLED, `llama_trigger.py` legacy).
- `bin/` — llama.cpp binaries (gitignored DLLs/exes; `bin/README.md` tracked).
- `models/` — GGUF + whisper-small (gitignored; Vosk dir is legacy).
- `wheelhouse/` + `wheelhouse.sha256` — offline deps (dir ignored, manifest tracked).
- `tools/` - `check_offline_bundle.py`, `test_offline_bundle.py`,
  `test_runtime_flow.py`, `test_obsidian_brain.py`,
  `test_decision_controller.py`, `test_semantic_intent.py`,
  `test_obsidian_graph.py`, `verify.ps1`,
  `append_progress.py`, `checklist_tool.py`, `test_portable.py`, `build_package.py`.
- `OFFLINE_BUNDLE.md` — offline distribution baseline + readiness states.
- `JARVIS_STATE.md` — single-page current truth. `AGENTS.md` — stable facts.
- `PROGRESS_LOG.md` — append-only work log. `CURRENT_ISSUES.md` — buglist.
- `docs/decisions/` — ADRs for architectural choices.
- `.devin-context/` — rolling agent memory re-injected by `.devin/hooks.v1.json`.
- `reports/` — gitignored verification output.
- `logs/runtime.log` — gitignored rotating inference stage diagnostics;
  timestamps and outcomes only, never prompts or transcripts.

## Non-goals / dead paths

- `scripts/wake_listener.py`, `scripts/llama_trigger.py`, `launch_jarvis_full.command`,
  `download_binaries.py`, Vosk model dir — legacy, not part of the release path.
- `ollama.Client()` reference in `scripts/jarvis_commands.py` — dead code.
- AppleScript/`osascript` commands in the registry — macOS leftovers.
