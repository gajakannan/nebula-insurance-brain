# F0020 — Minimal graph/temporal query API

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

A minimal graph and temporal query API answers the v0.1 acceptance questions as of valid time and recorded time (sections 20, 68, 87).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0022](../../architecture/decisions/ADR-0022-apache-age-is-the-graph-projection.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0008, F0018 (previously F0001).
- Responses return the ADR-0039 information state, never a bare null. Historical (valid/recorded time) queries are authorized against current grants and cannot reinstate revoked access (ADR-0053).

## Shipped contract carry-in: ADR-0077/ADR-0078 (2026-11-21)

F0007 and F0008 shipped [ADR-0077](../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md) (FactSlot identity, `fact-answer/v1`) and [ADR-0078](../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md) (`fact-temporal/v1`, close-only versions). Both are Accepted. The handoffs below come from those records' Consequences sections. Bind Phase B to the as-built contract (master blueprint sections 13 and 14, "As built"), not to the original sketch. The feature status is unchanged.

- Expose information states over HTTP (ADR-0077/0078 consequences). `GET /facts/{factSlotId}` already has the optional `temporal` block and the `FactValidityUnknown` 200 variant (ADR-0078 D9).
- Reads resolve by ADR-0078 D9: `VALIDITY_UNKNOWN(UNKNOWN_END_WINDOW | BEFORE_ATTESTATION_FLOOR)`, then `NOT_PROCESSED` for identity-v1 slots. A principal who cannot read the attesting documents receives the non-disclosing 404.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0020.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Assessment and example integration

Expose a consistent authorized canonical snapshot for F0065, including explicit valid/known coordinates and permitted completeness/conflict context. F0065 owns its assessment service contract; this query feature does not depend on the assessment UI.

See the [example coverage map](../../examples/README.md) and [F0065](../F0065-grounded-gl-guideline-assessment/README.md).
