# F0036 — Evidence-aware retrieval / grounded generation

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

Grounded answers carry scope, time basis, evidence references, and abstention, and counts or financial analysis run through typed authorized query plans rather than retrieved passages (sections 44, 113).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0010](../../architecture/decisions/ADR-0010-provenance-is-mandatory.md), [ADR-0046](../../architecture/decisions/ADR-0046-grounded-answer-and-analytic-query-contract.md). Likely predecessors (inferred, confirm at Phase B): F0035.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0036.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Emit `ANSWER_BASIS_LINKED` built from the ADR-0046 answer object: used nodes, considered-not-used nodes, and each answer span with its basis. Never derive "used" from retrieval rank, proximity or traversal.
- Record retrieval, graph traversal, temporal selection, evidence resolution and conflict boundaries as trace events, with permission-safe counts only.
- Record each trace's semantic context: ontology release, projection version, valid-as-of and known-as-of.
- Recording is non-blocking: a recording failure marks the trace partial and never fails the answer.
- Acceptance example: [EX-OBS-001/002](../../examples/graph-observatory-2d-options.html) answer trace, where the superseded $2,000,000 limit is traversed and classified as considered, not used.
