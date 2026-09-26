# F0023 — Minimal Entity 360

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

Minimal Entity 360 exposes current and historical facts with evidence pointers for the acceptance question (section 70).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0036](../../architecture/decisions/ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0023.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Assessment and example integration

Provide the host Entity 360 surface for F0065 S0005: assessment outcome, selected guideline/version, time basis, comparison and evidence/review links, with distinct loading/error/unknown/conflict states. F0065 owns the extension and depends on this base view; do not introduce the reverse dependency.

See the [example coverage map](../../examples/README.md) and [F0065](../F0065-grounded-gl-guideline-assessment/README.md).

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- List an entity's names with their kind, sources, and validity; answer the legal name as of a valid time (ADR-0066).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
