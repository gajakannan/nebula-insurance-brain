# F0059 — Execution gate

**Status:** Planned
**Phase:** v0.4+
**Roadmap:** Later

## Overview

Agent-proposed actions pass authorization, ontology constraints, business rules, process and temporal state, evidence requirements, and unresolved conflicts before ALLOW, DENY, or REVIEW (section 64).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0042](../../architecture/decisions/ADR-0042-resource-and-derivation-authorization.md), [ADR-0052](../../architecture/decisions/ADR-0052-delegated-agents-and-review-authority.md). Likely predecessors (inferred, confirm at Phase B): F0047, F0057.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0059.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md), [ADR-0069](../../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- The impact hold is the gate's first concrete check; approved actions execute as action attempts (ADR-0067, ADR-0069).
