# ADR-0074: Local Document-Job Execution Controls

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-10-27
**Direction authorized by:** Operator, F0005 G4 (2026-10-27), which asked the Architect to give the shipped controls an architectural home.
**Accepted:** 2026-10-28. At G4 round 2 of feature run `2026-10-25-4020923b`, the operator approved acceptance once Code Review N1 and Security SEC-F5-L5 were fixed and verified. Both were verified by the independent delta review (`delta-review-report.md`) and by the final live fault, timeout and kill lanes.
**Refines:** [ADR-0003](ADR-0003-one-time-content-extraction.md) (one-time extraction: how a conversion attempt is bounded and owned), [ADR-0004](ADR-0004-source-content-artifact-and-interpretation-are-separately-versioned.md) (job recovery around the artifact checkpoint) and [ADR-0055](ADR-0055-local-inference-profile-phi-4-mini-on-vllm.md) (how the dedicated local provider is shared and recovered). It applies to every extraction pipeline (`direct-baseline`, `graph-dense`, `graph-direct`).
**Scope:** The local Docker Compose runtime on one host, matching ADR-0060's acceptance scope. It is not a distributed quota or a production topology. F0026 may reopen it for production qualification.
**Source:** F0005 assembly plan Steps 0a, 2, 4 and 6 (Phase B, approved 2026-10-25), first written as ADR-0060 amendments, plus the F0005 G3 review findings.

## Context

ADR-0060 (Docling-Graph orchestration) carried the Phase B control design: supervised conversion, a host singleton per inference endpoint, stable failure reasons, a submission bound and pipeline selection. F0005 implemented and qualified those controls live. Its comparison then **rejected** Graph dense (see ADR-0060), so ADR-0060 stays Proposed.

The controls themselves are not Graph-specific. They now run for the default `direct-baseline` pipeline, and migrations 0009 and 0010 fix the failure-reason vocabulary in the database. A runtime this load-bearing cannot rest on a Proposed ADR about a rejected engine (Architect G3 verdict, High finding). ADR-0003 changes only by supersession, and ADR-0055 covers the inference profile, not conversion or job admission. So this record collects the controls on their own.

## Proposed Decision

### 1. Conversion runs in a supervised, conversion-only process group

- The parent starts a **300-second monotonic deadline** before launch. It durably records child ownership (a launch receipt) before acknowledging that conversion started.
- An attempt latch decides exactly one outcome: accepted, timeout, cancelled or failed. A late result after the deadline can never publish or start extraction.
- On failure the parent sends SIGTERM to the group, waits 2 s, sends SIGKILL, and reaps with a bound. If cleanup cannot be confirmed, the worker stops claiming (`converter_cleanup_unconfirmed`).
- Orphaned children are reaped at startup. A reused PID fails closed. Receipts carry the kernel boot id, so a receipt from a known earlier boot never signals anyone; only its staging is removed. An unreadable boot id is not proof of staleness: the reaper then fails closed.
- The child has no inference or publication capability, and does not inherit the host-guard lock. Only the parent publishes, through the existing fenced readiness commit (ADR-0004/0059).
- **Known limit (Security SEC-F5-M1):** the child shares the worker's OS user and has no memory cap. OS-level isolation (a separate user or container, a memory limit, no network) is required before any activation or non-synthetic document.

### 2. One host worker per canonical inference endpoint

- A process-lifetime `flock` lives in a fixed control directory, `/tmp/nebula-brain-inference-<uid>/`, mode 0700, same owner, no symlinks or overrides. It is keyed by the canonical loopback endpoint, so aliases, profiles, tenants and temporary configs share one lock. One in-process model slot limits the worker to a single request at a time.
- A durable **in-flight marker** precedes every HTTP dispatch. A timeout, broken transport or killed worker leaves the outcome uncertain: no worker claims again until the DevOps/harness supervisor confirms quiescence. Provider health alone is not quiescence.
- **Quiescence** stops the recorded provider group, confirms every member exited and restarts the identical recorded command. It confirms the model is served *and* that unauthenticated requests are refused, writes a source-free receipt, and only then clears the marker.
  - The provider record is validated when written and again before use. It must be a `vllm serve` process-group leader launched as a program named `vllm` (the console script, or an interpreter running a `vllm` script from its own directory), bound to the guarded host and port, with no credential in its argv. The name check alone does not prove the program is vLLM; **listener ownership is the binding check.**
  - When recorded, the guarded listening socket must belong to that group.
  - On restart, the credential is sent only after the guarded listener is owned by the new group.
  - Same-account tampering stays out of scope (SEC-F5-L4).
  - Before any signal, the live process must match the recorded start time, group and argv, and must still own the listener. Otherwise nothing is signalled.
  - A refused restart (unauthenticated, not ready, changed pins or a foreign listener) stops the process group it started and leaves the marker dirty. The provider log is owner-only (0600).
- **Host or provider faults stop the worker; queued jobs are left for reclaim rather than failed.** These are: a marker that cannot be written or cleared durably, a leftover or uncleared marker met mid-run (`provider_quiescence_required`), and serving usage beyond the token reservation (a changed tokenizer or an ignored output cap). A refused restart whose group cannot be confirmed stopped fails as `provider_restart_cleanup_unconfirmed`.

### 3. Every failed attempt records one stable reason

- Reasons come from a closed, CHECK-constrained vocabulary: migration 0009, expanded by 0010. They contain no source text or SDK messages.
- Any failed, rejected or budget-refused model call fails the attempt, including rejections before dispatch. A Graph-dense fallback to a direct call is never accepted under dense identity.
- **Retry rules:**
  - Before a ready bundle, a job converts at most twice (one reconversion). The budget is checked **before each launch** against durable `conversion_started` job events, not recorded reasons, so silent crashes count too. An exhausted budget fails the job as `conversion_failed`.
  - The `conversion_started` event name is part of this contract: recovery counts it, and the event column has no CHECK constraint.
  - After a ready bundle, an unexpected error is `interpretation_failed` and never spends conversion budget.
  - These reasons are terminal: `stage_guard_mismatch`, `unsupported_*`, `authorization_denied` and `model_budget_exceeded`.
- Downgrades refuse to drop or narrow recorded reasons.

### 4. Submissions are bounded

- `jobs.max_queue_depth` (committed, default 100) caps unfinished jobs. Admission happens under a PostgreSQL advisory transaction lock; duplicates stay idempotent, and the excess is rejected with `queue_depth_exceeded` (CLI exit code 4).
- **Known limits:**
  - The bound is host-wide, not per tenant; F0026 owns tenant fairness.
  - The submission pre-check runs before source storage. Two submitters racing for the last slot can leave the loser's stored source object and provisioned access rows behind. That is an orphan to sweep, not a bound violation.

### 5. The engine is chosen by committed configuration and pinned per job

- `extraction.pipeline` must be set explicitly in committed configuration. No environment variable selects it, and isolated qualification uses separate hashed configs.
- New jobs pin their pipeline, and the idempotency key includes it. Historical jobs without one keep their pre-change meaning (`graph-direct`).
- Changing the setting affects only new submissions, after a restart.

## Alternatives

- **Keep the controls inside ADR-0060.** Rejected: they would then depend on a Proposed ADR about a rejected engine.
- **Amend ADR-0003 or ADR-0055.** Rejected: ADR-0003 changes only by supersession, and ADR-0055 covers the inference profile, not conversion or job admission.
- **A distributed lease or quota service** for provider concurrency. Rejected for v0.1's single local host; F0026/F0050 own production topology.

## Consequences

- One worker on a single dedicated GPU: throughput is bounded by design. Scaling needs a new decision, not configuration.
- Recovery from an uncertain request restarts the shared local provider: 43–85 s measured in F0005. The restart uses only the recorded command.
- The reason vocabulary is a migration-governed contract. Adding a reason is an expand-only migration with a frozen enumeration test.

## Proof

These live-host results come from F0005 run `2026-10-25-4020923b`:
- every provider fault mode on two engines;
- an ambiguous timeout with the provider still generating;
- four kill points;
- competing workers with confirmed quiescence;
- storage failure before the marker;
- revocation and cancellation;
- the real 300-second deadline (decided at 300.002 s, cleaned up in 2.03 s);
- migration upgrade, downgrade and restore drills.

The reruns after the G3 rework (H1, M1–M5, SEC-F5-L1/L2) and after G4 round 2 (N1, SEC-F5-L4/L5, Code Review Lows) are recorded in that run's `test-execution-report.md`. At G4 (2026-10-28) the operator approved accepting this ADR once N1 and L5 were fixed and verified.

**Open before any activation or non-synthetic document:** SEC-F5-M1 (converter OS isolation) and the restart environment. The supervisor restarts vLLM with the inherited environment, which the recording environment needs for CUDA and the model cache.

## References

- [ADR-0060](ADR-0060-docling-graph-document-pipeline-orchestration.md): origin of these controls as Phase B amendments.
- F0005 [assembly plan](../../features/archive/F0005-one-time-docling-ingestion/feature-assembly-plan.md), Steps 0a, 2, 4 and 6.
- [Local inference runbook](../../../docker/local-inference-runbook.md): guard and quiescence procedure.
- F0005 run `planning-mds/operations/evidence/runs/2026-10-25-4020923b/`: `architect-qualification-verdict.md`, `security-review-report.md`, `code-review-report.md`.
