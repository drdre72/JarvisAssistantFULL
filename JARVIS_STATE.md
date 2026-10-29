# Jarvis — Current State

> Single-page source of truth for what is true **right now**.
> Keep it current. Stable knowledge belongs in `AGENTS.md`.
> Historical reasoning belongs in `docs/decisions/`.

## Project

- Windows-only Python 3.11 desktop companion (Flet UI), fully offline.
- LLM: llama.cpp `llama-completion.exe` + Qwen2.5-7B Q4_K_M (Apache-2.0), CPU.
- STT: faster-whisper `models/whisper-small/` (local-only).
- TTS: pyttsx3 / Windows SAPI.
- No vendor keys, no cloud calls, no wake word yet.
- Launch: `launch_jarvis.bat`.
- Active memory: local Obsidian-compatible Markdown vault under ignored
  `memory/obsidian-vault/`; an existing absolute vault can be opted in via
  `JARVIS_OBSIDIAN_VAULT`. Old JSON conversations remain read-only context.

## Verified working

- Offline bundle checker: passes end-to-end (exit 0) — all required assets
  staged, wheels hash-verified, deps resolve with `--no-index`.
- Real LLM inference through `LlamaReasoning` (`'2+2'` → `'4'`, ~7.5 tok/s CPU).
- Real faster-whisper load of `models/whisper-small/` via `WhisperSTT`.
- Core dependency imports (flet, pyaudio, pyttsx3, pygame, numpy, websockets).
- Flet UI launches (after `page.window_*` API fix) — first reply succeeded,
  Whisper mic input worked.
- Legacy Picovoice path disabled even when a key is supplied (tested).
- Wheelhouse: 73 wheels staged + installed offline into `.venv`.
- Direct replay of the first uncanned request: intent classification 16.7s,
  conversational reply 9.2s; both completed locally with no deadlock.
- Unit tests cover UI stage feedback; inference writes stage timings (no raw
  prompts) to ignored `logs/runtime.log`. User verified multi-turn voice chat.
- Supported voice command registry currently contains only local note-taking;
  unsupported macOS actions and avatar playback are not advertised.
- Dispatcher now matches a leading "write this down" phrase locally and sends
  other uncanned text directly to conversation. User log confirms there is
  no intent stage; two CPU replies took 18.4s and 18.9s.
- Unit tests cover current time/date from the local clock and accurate UI/tool
  capability answers. Both avoid the model; live voice retest is pending.
- Voice idle prompt points to the microphone button (keyless wake word is not
  implemented); persona now distinguishes supported note-taking and monitoring
  from unavailable arbitrary tool/screen access. User confirmed idle wording;
  prompt-only tool wording still failed, so the capability answer is now local.
- A parentless `llama-completion.exe` holding ~7.1 GiB RAM was stopped after
  user approval; available memory increased to ~21.8 GiB.
- Local vault and typed Lute-inspired NLP gate pass temporary-vault unit
  tests (notes, review proposals, approved retrieval, legacy JSON continuity,
  negation, provenance, rejected actions). No real vault/user microphone
  runtime test has occurred after this change.
- Required UI module imports now fail visibly instead of silently switching
  to no-op speech and memory functions; covered by regression tests.

## Active issues (see CURRENT_ISSUES.md for the full list)

1. **Latency:** the former 16s intent-classification pass has been removed
   from the dispatch path; live voice retest is pending. CPU reply still
   loads the model once per turn.
2. Obsidian memory and action gate need live UI/microphone validation,
   including user-edited Knowledge approval and note-taking.
3. Dead code: `ollama.Client()` in `jarvis_commands.py`, macOS `osascript`
   commands, `download_binaries.py`, legacy Vosk/WebSocket path.
4. Dependencies not pinned to exact versions; `requirements.txt` bounds only.
5. PyInstaller build unexercised; one-file layout vs launcher's beside-exe
   asset check is a known mismatch.
6. `flet-video` optional and unstaged → avatar video placeholder.
7. No LICENSE file despite README claim (MIT).

## Next architectural targets

1. Validate default vault creation, note-taking, review, and recalled approved
   Knowledge in a live voice session; no user vault data was migrated.
2. Test a real external Obsidian vault only after the user selects its path.
3. Pin exact dependency versions (lockfile from staged wheelhouse).
4. Improve lexical retrieval and optional reviewed legacy JSON migration;
   keep memory, imagination, and facts separate per `AGENTS.md` rule 3.
5. Sandboxed tool/thought execution boundary for commands.
6. PyInstaller packaging once the app is stable in dev mode.

## Rules of interpretation

- Prefer repository state over model memory.
- `AGENTS.md` = stable facts; this file = current status; `CURRENT_ISSUES.md`
  = buglist; `PROGRESS_LOG.md` = history; `.devin-context/memory.md` = session.
- `progress.txt` is historical and unreliable — do not trust it.
- A fix marked "applied" is not resolved until `tools\verify.ps1` (or the real
  runtime path) passes.
- Never reintroduce vendor keys or runtime downloads.
