# F0027 — Probabilistic entity resolution

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

Fuzzy, embedding, and model-assisted entity resolution with reversible merges follows the deterministic v0.1 resolver; every merge stays inspectable through merge history (sections 53, 90).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0025](../../architecture/decisions/ADR-0025-deterministic-er-ships-before-probabilistic-er.md). Likely predecessors (inferred, confirm at Phase B): F0017.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0027.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md), [ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Name-vector, abbreviation, containment, and cross-script matches only propose pairs. A pair proposed by similarity is never merged on a batch model verdict alone (ADR-0066).
- Automated merges pass the impact hold, read only human precedent, record their undo, and respect the revert fuse. Automation is off by default (ADR-0067).
- Key verdict caches on a basis that includes both profiles and the precedent set (ADR-0068).
