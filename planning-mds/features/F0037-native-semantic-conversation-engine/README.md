# F0037 — Native Semantic Conversation Engine + Onyx-inspired Chat mechanics

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

The native conversation engine implements turn trees, streaming, citations, branching, attachments, and feedback studied from Onyx while keeping Nebula's semantic model and scoping (sections 37, 72).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0018](../../architecture/decisions/ADR-0018-conversation-is-knowledge-producing.md), [ADR-0036](../../architecture/decisions/ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md). Likely predecessors (inferred, confirm at Phase B): F0021, F0036.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0037.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Record which entities and canonical facts each answer turn cited, so that the impact hold's `CITED` check is computable (ADR-0067).

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Record each model and tool call as a call-boundary event with its structured output and citations, plus an `INSTRUMENTATION_GAP` event for what is not recorded. Never capture chain-of-thought, prompts or full responses in a trace.
- Carry one `trace_id` per answer turn, correlated with the operational log trace id (SOLUTION-PATTERNS) but stored separately.
