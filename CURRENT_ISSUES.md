# Jarvis — Current Issues

Numbered buglist. States: ACTIVE, OPEN, PENDING VERIFY, RESOLVED, EXTERNAL.

## Runtime

1. **First uncanned voice reply appears stalled** - RESOLVED as a perceived
   stall. The user confirmed a successful multi-turn voice conversation.
   The first uncanned request took 16.0s to classify plus 10.6s to reply;
   the earlier canned response needed no model call. Stage feedback and
   `logs/runtime.log` now explain the wait. An unrelated parentless model
   process holding ~7.1 GiB was stopped with user approval; its origin is
   unconfirmed. The later intent classifier has now been replaced by an
   explicit local note-command match. Casual conversation should use only
   one model call; user log confirms ~18-19s for a CPU reply.
   A follow-up log showed the model fabricated a 2023 time/date when asked
   "time and date". Common current-clock questions now use the local system
   clock, and tool/UI capability questions use a truthful fixed response;
   live verification of these two answers is pending.

## Correctness / maintainability

2. Silent no-op fallbacks in `scripts/jarvis_app.py` on `ImportError` -
   RESOLVED. Required imports now fail visibly; optional `flet-video` still
   degrades to a placeholder, as intended. Unit tests cover missing memory.
3. `jarvis_commands.py` retains `ollama.Client()` (removed runtime) and macOS
   `osascript` functions - OPEN for cleanup. They are no longer registered as
   voice commands; only local note-taking is registered.
4. Broad `except`/swallowed errors in `jarvis_app.py` monitor + avatar paths —
   OPEN; errors should surface in the UI or logs.
5. Dependencies not pinned to exact versions — OPEN. Generate a lock from the
   staged wheelhouse so builds are reproducible.

## Distribution

6. PyInstaller build unexercised; `--onefile` puts data inside the exe while
   `main.py` checks beside it — OPEN. Decide layout before building.
7. `ui/` + `avatar_loop.mp4` absent; `flet-video` unstaged - OPEN. Voice avatar
   commands were removed and the UI avatar button disabled rather than
   invoking an obsolete macOS path. Restore only with a supported local player.
8. No LICENSE file (README claims MIT) — OPEN.

## External / historical

9. Leaked Picovoice key remains in public Git history — EXTERNAL. Revocation
   pending with Picovoice support (account inaccessible). Local path is dead
   code and can never init — residual risk is vendor-side only.
10. `progress.txt`, old README/SETUP claims — RESOLVED as a truth problem:
    superseded by `PROGRESS_LOG.md` + `JARVIS_STATE.md` (files themselves are
    still stale text; cleanup is cosmetic, not urgent).

## Roadmap (not bugs)

11. Obsidian-backed Markdown vault MVP - implemented and unit-tested.
    Conversation, review and approved Knowledge are separate; live microphone
    and actual Obsidian editing remain PENDING VERIFY. Existing JSON is
    read-only context; no bulk migration or deletion was performed.
12. Sandboxed execution boundary for commands/thoughts.
13. Keyless local wake word (future; Picovoice path must stay dead).
14. Retrieval/OS isolation - OPEN. The Lute-style typed memory action gate
    prevents model-authored commands but is not an OS sandbox or a cure for
    prompt injection inside user-edited Markdown. Knowledge retrieval is
    lexical and manually approved, not independent factual verification.
