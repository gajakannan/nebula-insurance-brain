# F0041 — Learning Plane

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

The learning plane holds candidates, evidence, gaps, and reasoning-pattern candidates with independent-support rules so repetition never becomes proof (sections 31 to 35, 110.5).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0020](../../architecture/decisions/ADR-0020-learning-plane-is-separate-from-canonical-truth.md), [ADR-0021](../../architecture/decisions/ADR-0021-learned-knowledge-requires-provenance.md), [ADR-0047](../../architecture/decisions/ADR-0047-controlled-learning-and-reinterpretation.md). Likely predecessors (inferred, confirm at Phase B): F0009.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0041.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Graph Observatory carry-in (2026-10-13)

[ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Keep learning-candidate lifecycle records (proposed, superseded, retained, rejected, promoted) with terminal states and evidence, citable as `authoritative_record_ref` in learning traces (ADR-0072 section 2).
- A run that proposes but commits nothing must be distinguishable from a run that failed.
- Example: [EX-OBS-001/002](../../examples/graph-observatory-2d-options.html) learning run, which ends with one ontology proposal, one unresolved conflict and zero canonical changes.
