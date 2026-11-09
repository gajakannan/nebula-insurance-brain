# F0007 — FactSlot model

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

FactSlot defines canonical semantic identity for every fact; the GL limits in the v0.1 acceptance question are distinct FactSlots (section 13).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0006](../../architecture/decisions/ADR-0006-factslot-defines-canonical-semantic-identity.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0002, F0003, F0006 (previously F0001).
- Carry master blueprint 107.4 and ADR-0039 into the PRD: information state (eight states) is separate from the value, NOT_FOUND/NOT_STATED carry the exact scope searched, and access denial is never an information state. Values use qualified money (exact decimal, ISO 4217 currency, basis) and scoped identifiers (scheme, type, value).
- Carry 109.1: define FactSlot identity beyond the first scalar example (multi-valued, qualified and relationship slots). FactSlot keys are the predicate key referenced by the ADR-0038 SourceAuthorityPolicy owned by F0018.
- New tenant-owned tables bind child rows and foreign keys to tenant ownership and follow the ADR-0042 row-security pattern settled in F0018 Phase B.

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
