# F0052 — Normative constraints

**Status:** Planned
**Phase:** v0.3
**Roadmap:** Later

## Overview

Obligations such as issue-within-24-hours are modeled separately from fact modes and evaluated against canonical and execution state (section 57).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0027](../../architecture/decisions/ADR-0027-normative-and-hypothetical-semantics-are-not-fact-modes.md). Likely predecessors (inferred, confirm at Phase B): F0048.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0052.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Receive mood-routed statements (obligations, requirements, subjectivities) as normative-constraint candidates (ADR-0065, EX-SEM-007).
