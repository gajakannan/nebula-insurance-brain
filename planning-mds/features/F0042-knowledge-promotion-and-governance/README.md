# F0042 — Knowledge promotion/governance

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

Governed promotion moves conversation artifacts and learning candidates into canonical knowledge or the ontology through review and provenance checks (sections 32, 42).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0019](../../architecture/decisions/ADR-0019-conversation-knowledge-is-not-canonical-by-default.md), [ADR-0020](../../architecture/decisions/ADR-0020-learning-plane-is-separate-from-canonical-truth.md). Likely predecessors (inferred, confirm at Phase B): F0040, F0041.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0042.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Graph Observatory carry-in (2026-10-13)

[ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Keep commit, release-publication and review-decision records distinguishable from attempts (ADR-0069), so a learning trace never shows a commit the record does not show.
- Provide stable deep-link targets for review items and commits. The Observatory links to them and never acts.
