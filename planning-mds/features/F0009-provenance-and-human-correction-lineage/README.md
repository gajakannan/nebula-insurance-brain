# F0009 — Provenance + human-correction lineage

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Now (2026-11-20 roadmap review)

## Overview

No authoritative fact exists without evidence, and human corrections append with lineage that feeds the Golden Corpus (sections 17, 75).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0010](../../architecture/decisions/ADR-0010-provenance-is-mandatory.md), [ADR-0037](../../architecture/decisions/ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0006, F0008 (previously F0001).
- Carry the master blueprint 88 LearningCandidate hook: human corrections persist a reserved LearningCandidate reference for the Golden Corpus. No learning behaviour ships in v0.1 (F0041 owns it).

## Shipped contract carry-in: ADR-0077/ADR-0078 (2026-11-21)

F0007 and F0008 shipped [ADR-0077](../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md) (FactSlot identity, `fact-answer/v1`) and [ADR-0078](../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md) (`fact-temporal/v1`, close-only versions). Both are Accepted. The handoffs below come from those records' Consequences sections. Bind Phase B to the as-built contract (master blueprint sections 13 and 14, "As built"), not to the original sketch. The feature status is unchanged.

- Provenance lineage reads remainder `split_of_version_id` (bound to the same slot by migration 0015) and the append-only `canonical_fact_change` rows (ADR-0078 consequences).
- Version rows are close-only: the database refuses UPDATE (except the single recorded close), DELETE and TRUNCATE. Correction lineage must append and must not rewrite a version.
- Ending evidence is stored in the version's `evidence` JSONB as `ending_refs`. A correction of a version-2 assertion is a version-2 child assertion (ADR-0075).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0009.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
