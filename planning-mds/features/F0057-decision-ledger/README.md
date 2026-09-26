# F0057 — Decision ledger

**Status:** Planned
**Phase:** v0.4+
**Roadmap:** Later

## Overview

Decisions record the exact fact versions, recorded-time snapshot, rule, ontology, and model versions used (section 63).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0032](../../architecture/decisions/ADR-0032-decision-replay-uses-recorded-time-state.md). Likely predecessors (inferred, confirm at Phase B): F0018, F0056.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0057.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Record which entities and facts a decision cited, so that the impact hold's `CITED` check is computable (ADR-0067).
