# F0008 — Bitemporal canonical facts

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Full bitemporality with database-level overlap integrity is required before the endorsement slice can be proven (sections 14, 15, 109.2).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0007](../../architecture/decisions/ADR-0007-full-bitemporality.md), [ADR-0008](../../architecture/decisions/ADR-0008-database-level-temporal-integrity.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0008.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Store per-bound granularity, `valid_to_state` (`OPEN`, `BOUNDED`, `UNKNOWN`), and `attested_from`/`attested_to`. Settle how `UNKNOWN` ends are represented inside the ADR-0008 exclusion constraint; the recommended option is in ADR-0064. Reads distinguish unknown from open and never widen a missing start to negative infinity.
- A successor closes a predecessor in a single-valued slot only when its start is grade `A` or `B`, never on model confidence.
