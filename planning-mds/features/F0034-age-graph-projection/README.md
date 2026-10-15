# F0034 — AGE graph projection

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

Apache AGE provides openCypher traversal over canonical entities and relationships as a rebuildable projection with commit-consistent delivery (sections 47 to 49, 109.3).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0022](../../architecture/decisions/ADR-0022-apache-age-is-the-graph-projection.md), [ADR-0041](../../architecture/decisions/ADR-0041-atomic-semantic-commit-and-projection-delivery.md). Likely predecessors (inferred, confirm at Phase B): F0003, F0018.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0034.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Build AGE from accepted canonical records and the existing outbox/rebuild path. Do not load upstream graph exports directly; local extraction IDs and deduplication have no canonical authority.

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Give every projection build a stable version identifier and keep it queryable, so a trace can cite the projection it used and a replay can tell when that version is no longer available (ADR-0071 section 4).
