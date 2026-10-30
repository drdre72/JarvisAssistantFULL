# ADR-0005: Bounded idle-time work queue for proactive assistance

**Status:** proposed

## Decision

Jarvis gains a persistent, inspectable work queue processed by a background
scheduler. Proactivity is expressed as *queued jobs with declared completion
criteria*, not an always-thinking model loop. Two lanes exist: interactive
requests always preempt; background jobs fill idle time.

Jobs may produce proposals (Review-queue memory candidates, validation and
diagnostic reports, prefetched approved-Knowledge context) but never grant
themselves authority. Nothing in the queue writes to approved Knowledge,
executes tools, changes permissions, or speaks to the user uninvited.

"Satisfied" means a job's typed completion criterion verified or the job
returned a bounded report of why it could not complete — the same
intent-to-fulfillment contract used for user turns. Jobs are budgeted
(tokens, time, count per tick) and cannot spawn unbounded sub-jobs.

## Context

- The purpose profile's axiom IV permits anticipation but forbids presumed
  authority; a proactive runtime needs a structural home for initiative.
- `llama-completion.exe` is currently spawned per request, reloading the
  ~4.4 GB model each turn; a meaningful share of observed 18-30 s latency is
  reload, not generation.
- The CPU can run only one 7B-class inference at a useful speed, so a
  background lane must not starve an active user turn.
- Long-term direction (wearable form factor) favors a scheduler that can
  later split into its own process and drive a smaller background model.

## Alternatives rejected

- An always-running "think loop" that lets the model decide when it is done:
  unbounded, unauditable, and violates the intent-to-fulfillment contract.
- Letting background work write to Knowledge or invoke tools directly:
  initiative would silently become authority (axioms IV-VI).
- A second concurrent inference on the same CPU build: contention makes
  voice turns slower and less reliable, not faster.

## Consequences

- New modules: a work-queue/task model and a scheduler/tick loop, initially
  a daemon thread in `jarvis_app.py` alongside the voice and monitor loops;
  a separate process is deferred work.
- Prerequisites before jobs do useful inference: interactive preemption
  (terminate/deprioritize the inference subprocess — does not exist today)
  and job checkpointing.
- Model residency is an open design point: keeping one model loaded
  (persistent subprocess or `llama-server` bound to loopback) removes reload
  latency at the cost of ~5 GB resident RAM and a new process boundary.
  Loopback serving must be documented as not-network-egress under ADR-0001
  before adoption; on constrained hardware a smaller background model is
  preferred over a second resident 7B.
- All job outputs land in existing governed locations (`Jarvis/Review/`,
  diagnostics logs, context assembly) and stay labelled unverified or
  pending review. The queue itself lives in the `Jarvis/` vault subtree so
  it remains inspectable and gitignored.
- This ADR describes direction only; no scheduler exists yet.
