# F0040 — Conversation Graph

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

A temporary conversation graph holds hypotheses and discovered relationships outside canonical truth until explicit promotion (sections 40, 41, 43).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0019](../../architecture/decisions/ADR-0019-conversation-knowledge-is-not-canonical-by-default.md). Likely predecessors (inferred, confirm at Phase B): F0037.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0040.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- In traces, conversation hypotheses and discovered relationships carry the `CONVERSATION` layer and are never drawn or counted as canonical (ADR-0019).
