# F0045 — Cytoscape Graph Explorer

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

The graph explorer visualizes the AGE projection with time-aware traversal inside the native semantic UX (section 73).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0022](../../architecture/decisions/ADR-0022-apache-age-is-the-graph-projection.md), [ADR-0036](../../architecture/decisions/ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md). Likely predecessors (inferred, confirm at Phase B): F0034.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0045.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) and [ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) govern this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Define the shared visual vocabulary for knowledge layers (source, open statement, typed assertion, canonical, derived, conversation, candidate) and trace attribution (observed, used in answer, considered not used, not instrumented), so F0067's 2D view reuses this explorer instead of a second graph library.
- Filter existence server side: no ghost nodes, labels or counts outside the viewer's scope (ADR-0072 section 3).
