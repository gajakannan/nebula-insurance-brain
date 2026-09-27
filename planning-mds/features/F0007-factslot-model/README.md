# F0007 — FactSlot model

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

FactSlot defines canonical semantic identity for every fact; the GL limits in the v0.1 acceptance question are distinct FactSlots (section 13).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0006](../../architecture/decisions/ADR-0006-factslot-defines-canonical-semantic-identity.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0007.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Define the name FactSlots: `hasLegalName` (single-valued per valid time), `hasTradeName`, `hasFormerName`, and `knownAs` (multi-valued). An entity's display name is selected from its current name facts (ADR-0066, EX-SEM-008).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
