# F0019 — Basic endorsement supersession

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

Basic endorsement supersession exercises change semantics and bitemporal versions on a real policy change (section 87).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0007](../../architecture/decisions/ADR-0007-full-bitemporality.md), [ADR-0009](../../architecture/decisions/ADR-0009-explicit-change-semantics.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0019.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Take endorsement effective dates from time mentions resolved against the policy period and its time-of-day convention. "Effective as of inception" without a known policy period is grade `C` and opens review (EX-SEM-003b).
