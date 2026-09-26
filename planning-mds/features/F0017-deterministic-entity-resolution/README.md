# F0017 — Deterministic entity resolution

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Deterministic entity resolution with stable, scoped identifiers ships before probabilistic resolution (sections 53, 107.3). Docling-Graph local deduplication does not replace enterprise identity resolution (ADR-0060).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0025](../../architecture/decisions/ADR-0025-deterministic-er-ships-before-probabilistic-er.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0017.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Treat upstream graph IDs as run-scoped references. Test that local node merges, synthesized parents, and identical text across tenants cannot merge enterprise identities or increase evidence precision.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Resolve on identifiers first. An exact name match without an identifier creates a review pair and never merges. A name held by another compatible entity creates a shared-name pair. Roles such as "the named insured" point at entities and are not names (ADR-0066).
