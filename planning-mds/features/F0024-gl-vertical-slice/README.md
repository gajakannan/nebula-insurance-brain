# F0024 — GL vertical slice

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

The GL vertical slice proves actual model interpretation through evidence review and canonical acceptance to the bounded F0065 guideline assessment, with exact rule/fact/evidence lineage and explicit time context (sections 86, 124).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0005](../../architecture/decisions/ADR-0005-three-plane-knowledge-model.md), [ADR-0006](../../architecture/decisions/ADR-0006-factslot-defines-canonical-semantic-identity.md), [ADR-0010](../../architecture/decisions/ADR-0010-provenance-is-mandatory.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0024.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Scope amendment and required story acceptance (2026-09-07)

- Run actual interpretation over the synthetic GL package, follow the governed review/commit path, and compare the accepted each-occurrence limit with the reviewed fictional guideline using F0065.
- Show the rule version, comparison, evidence, and time basis; no model confidence may authorize acceptance or approval.
- Include wrong high-confidence extraction and missing/conflicting-input variations. Mocked interpretation alone does not satisfy the end-to-end acceptance.
- Depends on F0065 for assessment integration; existing extraction/commit foundations remain prerequisites.

Reference: [EX-GL-001](../../examples/neurosymbolic-gl/README.md), [cases](../../examples/neurosymbolic-gl/cases.md), and [F0065](../F0065-grounded-gl-guideline-assessment/README.md). These requirements must be carried into this feature's PRD/stories when planned; runtime and feature status remain Planned.
