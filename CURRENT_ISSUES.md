# Jarvis — Current Issues

Numbered buglist. States: ACTIVE, OPEN, PENDING VERIFY, RESOLVED, EXTERNAL.

## Runtime

1. **First uncanned voice reply appears stalled** - RESOLVED as a perceived
   stall. The user confirmed a successful multi-turn voice conversation.
   The first uncanned request took 16.0s to classify plus 10.6s to reply;
   the earlier canned response needed no model call. Stage feedback and
   `logs/runtime.log` now explain the wait. An unrelated parentless model
   process holding ~7.1 GiB was stopped with user approval; its origin is
   unconfirmed. The later intent classifier has now been replaced by
   deterministic memory gating and a local-only decision controller. Casual
   conversation uses only one model call; user log confirms ~18-19s for a
   CPU reply before the controller addition.
   A follow-up log showed the model fabricated a 2023 time/date when asked
   "time and date". Common current-clock questions now use the local system
   clock, and tool/UI capability questions use a truthful fixed response;
   live verification of these two answers and the new controller is pending.

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
8. No LICENSE file (README now warns about rights) - OPEN.

## External / historical

9. Leaked Picovoice key remains in public Git history — EXTERNAL. Revocation
   pending with Picovoice support (account inaccessible). Local path is dead
   code and can never init — residual risk is vendor-side only.
10. `progress.txt` is historical and unreliable - RESOLVED as a truth
    problem by `PROGRESS_LOG.md` + `JARVIS_STATE.md`. README/SETUP now reflect
    the CPU/offline baseline; historical notes remain unedited.

## Roadmap (not bugs)

11. Obsidian-backed Markdown vault MVP - implemented and unit-tested.
    Conversation, review, approved Knowledge and reviewed purpose are separate.
    Approved Knowledge now supports bounded wikilink expansion; live microphone
    and actual Obsidian editing remain PENDING VERIFY. Existing JSON is
    read-only context; no bulk migration or deletion was performed.
12. Sandboxed execution boundary for commands/thoughts.
13. Keyless local wake word (future; Picovoice path must stay dead).
14. Retrieval/OS isolation - OPEN. The Lute-style typed memory action gate
    prevents model-authored commands but is not an OS sandbox or a cure for
    prompt injection inside user-edited Markdown. Knowledge retrieval uses
    lexical seeds plus bounded approved-only wikilinks; user review and
    relationships are not independent factual verification.
15. Offline decision controller - PENDING VERIFY in live UI. Unit tests cover
    local metrics, approved-memory matching, no needless model call for live
    data, and stable conversation routing. Rule-based local reads plus a
    typed local-model interpretation are not an adaptive general planner,
    freshness verifier, simulation engine, tool sandbox or online connector.
    The registry declares evidence but does not probe device runtime health.
16. Live voice retest - PENDING VERIFY after fixes. "Do you see your
    Obsidian?" fell through to a model reply claiming arbitrary note updates;
    stopping voice while inference ran still allowed a late spoken reply.
    A later live retest verified "Thank you, Jarvis." now takes the fast path,
    but "do you recognize any of your tools or the Obsidian?" still went to
    the model and overclaimed vault management. The exact phrase and related
    capability questions now have registry-backed local routing and tests;
    an ordinary statement about Obsidian remains conversation. Live retest
    of this new route and voice-stop behavior remains open. In-flight
    inference is not cancelled, only its late reply discarded. The earlier
    partial transcription's cause is unknown.
17. Audio/intent failure diagnosis - OPEN. The current voice path reduces
    low audio, empty or filtered transcription, and capture/model errors to
    an empty string; the UI treats them as one silence count. `WhisperSTT`
    squares `int16` samples before widening, so RMS can overflow (amplitude
    30000 produced RMS 0 in a check); existing thresholds cannot be trusted
    for diagnosing quiet speech, clipping or background noise. Introduce
    measured, calibrated stage-specific diagnostics and structured retry
    guidance before making causal claims or allowing uncertain speech to
    authorize actions. No category-based feedback is implemented yet.
18. Semantic intent/identity live validation - PENDING VERIFY. The new local
    structured model path can distinguish self-purpose, capability inquiry,
    ordinary dialogue and ambiguity without a second classifier call. Its
    classification can still be wrong; generated dialogue is not an
    independently verified fact. Only a manually approved `Jarvis/Core/Purpose.md`
    supplies purpose; no profile is auto-created. Existing narrow fast paths
    and the deterministic action gate remain. Live voice/typed chat retesting
    and user-authored purpose approval are still needed.
19. Wikilink graph validation - PENDING VERIFY in a real user vault. The
    approved-only graph supports outgoing related/depends_on/derived_from/
    used_by/contradicts links, IDs, source paths, depth/size limits and a
    read-only validator. Only flat `Jarvis/Knowledge/*.md` files (first 200,
    at most 32 KB each) are indexed; nested notes, full YAML aliases, rich
    conflict resolution and independently verified freshness are not yet
    supported. No link approves a pending note. Live Obsidian review and
    representative large-vault performance remain untested.
