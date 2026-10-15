# F0038 — Chat with Document

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

Chat rooted on a document distinguishes what the document says from what the Brain currently accepts and cites content blocks as evidence (sections 38, 113.1).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0018](../../architecture/decisions/ADR-0018-conversation-is-knowledge-producing.md), [ADR-0046](../../architecture/decisions/ADR-0046-grounded-answer-and-analytic-query-contract.md). Likely predecessors (inferred, confirm at Phase B): F0022, F0037.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0038.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) and [ADR-0072](../../architecture/decisions/ADR-0072-observatory-is-a-read-only-projection.md) (Proposed) govern this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Return a `trace_id` with each answer when an instrumented execution exists, and show the compact **How the Brain answered** summary: sources, recorded hops, evidence, time checks, gaps and status. The full trace view and replay are F0067.

**Early panel (operator decision, 2026-10-13).** This feature ships the first **How the Brain answered** panel instead of waiting for F0067:

- The static summary plus the basis-path view (option C on the [options page](../../examples/graph-observatory-2d-options.html)): question to answer, with considered-not-used branches and gaps shown as such, and an equivalent accessible list. A lightweight SVG/list rendering is enough; F0045's Cytoscape explorer and F0067 can replace it later.
- No replay, no 3D, no learning traces. Those stay in F0067.
- Stand up the read-path trace store (ADR-0071 section 5): retention defaults to 90 days and is configurable per tenant; a trace whose answer is cited by a recorded decision is kept with that decision.
- Trace access follows answer access (ADR-0072 section 3): whoever may read the answer may read its trace, including colleagues' answers.
- First golden case: one real GL endorsement answer (the same case F0067 reuses).
- If there is no trace, show "Detailed trace unavailable". The answer never depends on the trace.
