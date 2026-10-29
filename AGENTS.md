# AGENTS.md — Jarvis Agent Knowledge Cache

Persistent, hand-maintained notes for AI agents working on this repo.
Stable facts live here; dynamic state belongs in `JARVIS_STATE.md`;
session-scoped notes belong in `.devin-context/memory.md`.

## GOVERNING RULES

1. **Jarvis is fully offline at runtime.** No cloud inference, no vendor
   wake-word keys, no model downloads inside application code paths. Build-time
   asset staging (wheelhouse, models, binaries) is a separate, approved step.
2. **No credentials in the repo.** The historical Picovoice key is compromised;
   `scripts/wake_listener.py` is deliberately disabled and must not be revived.
   `JARVIS_PICOVOICE_ACCESS_KEY` must not be reintroduced.
3. **Memory, imagination, and facts are separate.** Retrieved memory,
   generated content, and verified facts must not silently mix. This governs
   the future Obsidian memory layer.
4. **Prefer repository state over model memory.** Check files and run the
   verification loop before asserting something is done.

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
- Voice dispatcher: only local note-taking is registered. Legacy macOS
  commands and avatar playback are not supported on Windows; do not re-add
  them before implementing and testing a sandboxed local replacement.
- Dispatcher recognizes only an explicit leading "write this down" (optional
  "Jarvis" prefix) before conversation. Never let model output authorize
  tool execution; future tool intents require deterministic validation.
- `scripts/intent_gate.py` adapts Lute's ordered parse -> typed intent ->
  authorization -> domain authority pattern. "Remember that" goes to Review,
  never Knowledge; only manually approved Knowledge files are retrieved.
- `JARVIS_OBSIDIAN_VAULT` - optional existing absolute Obsidian vault path;
  omit for ignored project-local default. No network/plugin calls for memory.
- Current time/date and UI/tool visibility questions are answered from the
  local clock and declared capabilities, not model recollection. Do not ask
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
- `scripts/` — app modules (`jarvis_app.py` UI, `reasoning.py`, `dispatcher.py`,
  `jarvis_commands.py`, `speech_recognition.py`, `speaker.py`,
  `runtime_log.py` (rotating stage diagnostics), `memory_system.py`,
  `wake_listener.py` DISABLED, `llama_trigger.py` legacy).
- `bin/` — llama.cpp binaries (gitignored DLLs/exes; `bin/README.md` tracked).
- `models/` — GGUF + whisper-small (gitignored; Vosk dir is legacy).
- `wheelhouse/` + `wheelhouse.sha256` — offline deps (dir ignored, manifest tracked).
- `tools/` - `check_offline_bundle.py`, `test_offline_bundle.py`,
  `test_runtime_flow.py`, `test_obsidian_brain.py`, `verify.ps1`,
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
