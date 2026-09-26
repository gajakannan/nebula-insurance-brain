# F0056 — Derived dependency invalidation

**Status:** Planned
**Phase:** v0.4+
**Roadmap:** Later

## Overview

Automatic propagation across persisted derived canonical facts invalidates and recomputes dependencies after input changes; it extends the lineage introduced by F0065 without being a prerequisite for its on-demand v0.1 assessments (sections 55, 56, 124).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0026](../../architecture/decisions/ADR-0026-derived-facts-have-dependency-lineage.md). Likely predecessors (inferred, confirm at Phase B): F0008.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0056.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Scope amendment and required story acceptance (2026-09-07)

- F0065 recomputes each requested assessment from an explicit snapshot and retains prior records as history.
- F0056 owns dependency discovery, affected-interval invalidation, cascading recomputation, and publication for persisted derived canonical facts.
- Preserve exact input/rule versions and current permission propagation. Historical assessments must not be silently rewritten by the generalized engine.

Reference: [EX-GL-001](../../examples/neurosymbolic-gl/README.md), [cases](../../examples/neurosymbolic-gl/cases.md), and [F0065](../F0065-grounded-gl-guideline-assessment/README.md). These requirements must be carried into this feature's PRD/stories when planned; runtime and feature status remain Planned.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Find the derived facts and assessments to invalidate by decision-basis fingerprint, never by timestamp comparison (ADR-0068).
