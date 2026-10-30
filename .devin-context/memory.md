# Jarvis — Agent Memory (rolling state)

> This file is the agent's **persistent working memory**. It survives context
> compaction and session restarts (re-injected by `.devin/hooks.v1.json`).
> Keep it concise and current — append to "Recent session activity", prune
> stale TODOs. For **stable** facts see `AGENTS.md`; this file is for the
> **dynamic** state: what we're doing right now, live TODOs, recent changes.

## Active TODOs

- [ ] Retest grounded time/date and UI/tool answers after latest dispatcher
      change. Classifier removal was verified live; CPU reply ~18-19s.
- [ ] Verify the narrowed command registry and disabled avatar button in the
      next live UI session; unit tests and a real classifier call already pass.
- [ ] Live-test the Obsidian vault with voice note-taking, candidate review,
      and an approved user-authored Knowledge note.
- [ ] Live-test the local-only decision controller for approved note retrieval,
      CPU/memory readings, and truthful offline responses.
- [ ] User can author `Jarvis/Core/Purpose.md` in Obsidian and manually mark
      it approved; Jarvis must not invent or create that identity statement.
- [ ] Live-test purpose/tool questions and linked approved Knowledge recall;
      only synthetic real-model/UI checks are done so far.
- [ ] Validate graph indexing and source paths on a representative real
      approved vault before relying on it for large-memory retrieval.
- [ ] Retest the exact recognition-phrased Obsidian/tools question and
      stopping voice during inference after restarting the app; gratitude
      was verified live, but these two paths remain unverified.
- [ ] Pin exact dependency versions from staged wheelhouse (issue #5).
- [ ] Decide PyInstaller layout (one-file vs beside-exe assets) (issue #6).
- [x] Obsidian memory design and ADR-0004 added (live UI test pending).
- [ ] Review the controller diff and verify the offline bundle. No commit or
      push was requested for this new milestone.

## Live runtime notes

- Python: `.venv\Scripts\python.exe` (3.11.9, x64). Bare `python` = system
  interpreter WITHOUT deps — always launch via `launch_jarvis.bat`.
- Inference binary is `bin\llama-completion.exe` (NOT llama-cli.exe — that is
  chat-mode only in b11985). Qwen2.5-7B Q4_K_M, ~7.5 tok/s CPU.
- STT loads `models\whisper-small\` only, `local_files_only=True`.
- Inference diagnostics: `logs\runtime.log` (ignored, rotating, stage-only);
  no raw transcript text is written there.
- Active memory: ignored `memory/obsidian-vault/Jarvis/` Markdown, or explicit
  `JARVIS_OBSIDIAN_VAULT` existing absolute directory. Legacy JSON is
  read-only context; Knowledge requires manually approved frontmatter.
- Offline-only runtime remains binding. Optional outward APIs are deferred
  until local brain/controller, security, functionality and UI are validated.
- Parentless `llama-completion.exe` PID 10700 from an earlier run occupied
  ~7.1 GiB; user approved stopping it and it exited. Available RAM ~21.8 GiB.
- 73 wheels in `wheelhouse/` installed into `.venv` via `--no-index`.
- Verify loop: `powershell -File tools\verify.ps1` → `reports\verify_*.txt`.

## Recent session activity (newest last; prune when >~15 entries)

- [2026-10-28] Git connection + onboarding audit; Python 3.11 + .venv restored.
- [2026-10-28] Picovoice key removed, legacy listener fully disabled; unsafe
  PowerShell TTS replaced with pyttsx3; offline bundle checker/tests added.
- [2026-10-28] Wheelhouse (73 wheels, hash-verified), llama.cpp b11985 CPU
  binaries, Qwen2.5-7B GGUF, whisper-small staged; all installed offline.
- [2026-10-28] Reasoning verified E2E via llama-completion.exe ('2+2'->'4');
  STT loads local model; first UI launch succeeded then stalled after 1 reply.
- [2026-10-28] Lute workflow ported: AGENTS/JARVIS_STATE/PROGRESS_LOG/
  CURRENT_ISSUES docs, .devin-context memory + hooks, verify.ps1,
  append_progress.py, checklist_tool.py, docs/decisions ADRs.
- [2026-10-29] Profiled uncanned voice request; classifier and reply completed
  in ~26s total. Added stage feedback, rotating local timing log, stdin
  isolation, and mocked regression coverage; user voice retest pending.
- [2026-10-29] Stopped parentless completion process PID 10700 after explicit
  user approval. No other process touched; origin and relevance to the
  voice stall are unknown.
- [2026-10-29] User confirmed multi-turn voice chat works. Log exposed two
  routing bugs: "Jarvis" anywhere triggered canned greeting, and "Can you
  see your tools?" falsely selected a macOS avatar command. Greeting/identity
  checks tightened; voice registry narrowed to local note-taking and avatar
  UI button disabled. Real classifier now returns unrecognized; UI retest pending.
- [2026-10-29] Removed the ~14s intent LLM call from dispatcher: explicit
  leading note command executes locally; other utterances route to the
  conversational model. Live timing after change still pending.
- [2026-10-29] User log confirmed no intent stage, ~18-19s CPU reply. Model
  fabricated October 2023 for "time and date" and denied any tools despite
  persona instructions. Added deterministic local-clock and tool/UI answers;
  unit tests pass, live retest pending.
- [2026-10-29 13:10] Implemented local Obsidian Markdown brain with separate
  Conversations/Notes/Review/Knowledge and legacy JSON read-only continuity.
  Ported Lute's parse -> typed intent -> authorization memory gate. Removed
  UI's critical no-op fallback; corrected public setup docs. Full verify
  passed (32 tests); live vault/UI retest remains pending.
- [2026-10-29 13:46] Added a local capability registry and a bounded offline
  controller for approved-memory context, CPU/memory readings, ordinary
  conversation and truthful fresh-data limitations. 50 tests and full
  offline verification pass; live voice/UI behavior remains unverified.
  A synthetic test note created during a failing test was removed with user
  approval; tests now mock all default-vault writes.
- [2026-10-29 13:48] Tightened selection: personal statements remain
  conversational; approved-note source must survive re-read. 52 tests pass;
  no network or general simulation capability was added.
- [2026-10-29 14:02] User voice log showed 21-23s replies, model overclaiming
  Obsidian edits, gratitude routing to inference, and a late reply after
  stopping listening. Grounded capability and gratitude phrases locally;
  voice-generation guard discards late spoken replies. 55 offline tests pass;
  live retest after restart pending.
- [2026-10-29 14:31] Follow-up live test: "Thank you, Jarvis." is fast, but
  "do you recognize ... tools or the Obsidian?" missed the narrow visibility
  matcher and produced another 22.8s model overclaim. Added a registry-backed
  vault-access answer and recognition/manage/read variants with negative
  statement coverage. Full offline verification passes (58 tests); restart
  and retest the recognition question and voice-stop behavior.
- [2026-10-30 08:07] Local-only intent foundation and approved wikilink graph
  implemented. Reviewed user-owned purpose is read only from Core/Purpose.md;
  typed model drafts cannot authorize actions or self-capability claims.
  Knowledge links expand only approved notes with depth/size limits and
  ID/path provenance. Offline suite 81 tests after a self-claim guard; synthetic real-model app path
  passes with temporary vault. User vault notes untouched; no commit/push.
