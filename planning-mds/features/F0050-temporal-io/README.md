# F0050 — Temporal.io

**Status:** Planned
**Phase:** v0.3
**Roadmap:** Later

## Overview

Temporal owns durable execution and proposes state changes only through canonical commit services (section 62). Activities invoke the shared bounded document service under the ADR-0074 controls.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0028](../../architecture/decisions/ADR-0028-temporal-owns-execution-brain-owns-semantic-state.md). Likely predecessors (inferred, confirm at Phase B): F0049.

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- Own the master blueprint 114.1 connector contract (source-system identity, object/version ID, timestamps, observed permissions, change cursor, withdrawal events, freshness). v0.1 intake is local files only.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0050.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Remain in v0.3 for human waits, timers, external activities, and durable business execution. v0.1 PostgreSQL jobs retain document-job recovery until then.
- Invoke the same authorized document service from Temporal activities. Pass artifact/run references and idempotency keys; keep document bytes and large graph outputs outside workflow history.
- Docling-Graph owns the internal extraction stage/chunk loop. Test activity retries, cancellation, and resumption against the persisted parse checkpoint and canonical commit idempotency.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0069](../../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Activities that dispatch external side effects use the action-attempt state machine and do not automatically retry the dispatch step, unless the remote honours the attempt's idempotency key (ADR-0069).
