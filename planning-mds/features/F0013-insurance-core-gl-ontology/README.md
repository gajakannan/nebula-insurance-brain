# F0013 — Insurance Core GL ontology

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The General Liability module of the insurance core ontology supplies the coverage, limit, and trigger concepts the v0.1 slice extracts (sections 23, 24, 107).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0011](../../architecture/decisions/ADR-0011-ontology-is-versioned-and-modular.md), [ADR-0039](../../architecture/decisions/ADR-0039-typed-insurance-values-and-completeness.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0013.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Declare `temporal_kind` on every GL property, and declare the name properties and name kinds (ADR-0064, ADR-0066).
- Model policy-period time-of-day and time-zone conventions so that documents can declare them in their time context.
