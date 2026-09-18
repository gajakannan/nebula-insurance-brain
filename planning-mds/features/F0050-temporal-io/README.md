# F0050 — Temporal.io

**Status:** Planned
**Phase:** v0.3
**Roadmap:** Later

## Overview

Temporal owns durable execution and proposes state changes only through canonical commit services (section 62). Docling-Graph coordinates internal document stages; activities invoke the shared bounded document service (ADR-0060).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0028](../../architecture/decisions/ADR-0028-temporal-owns-execution-brain-owns-semantic-state.md). Likely predecessors (inferred, confirm at Phase B): F0049.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0050.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Remain in v0.3 for human waits, timers, external activities, and durable business execution. v0.1 PostgreSQL jobs retain document-job recovery until then.
- Invoke the same authorized document service from Temporal activities. Pass artifact/run references and idempotency keys; keep document bytes and large graph outputs outside workflow history.
- Docling-Graph owns the internal extraction stage/chunk loop. Test activity retries, cancellation, and resumption against the persisted parse checkpoint and canonical commit idempotency.
