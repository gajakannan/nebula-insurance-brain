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

## Governed retrieval carry-in (2026-11-06)

The operator requested incorporation of the [spectral graph handoff](../../architecture/nebula-spectral-graph-intelligence-handoff.md). These are Phase A requirements inputs; this feature remains Planned and has no new phase approval. [Integrated design](../../architecture/governed-evidence-retrieval-design.md); [ADR-0076](../../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) is Proposed. The baseline is v0.2A, later trace visualization is v0.2B, and the separate [F0068 experiment](../F0068-spectral-graph-retrieval-experiments/README.md) remains conditional at v0.4+.

- **RET-36-01** The effective evidence budget must be resolved from a model profile naming window and exact tokenizer revision (see the handoff); non-positive budgets must be rejected.
- **RET-36-02** The final serialized payload must tokenize within the effective budget, measured after grouping and reauthorization.
- **RET-36-03** Each selected item must carry locator, declared precision, binding references and selection reason; precision is never upgraded by retrieval.
- **RET-36-04** Selected evidence must be revalidated and reauthorized before use; removals must recompute coverage, gaps and token count.
- **RET-36-05** Missing required evidence must produce an explicit gap or abstention (ADR-0046).
- **RET-36-06** Table rows and endorsement effective clauses must not be split in a way that changes meaning.
- **RET-36-07** "Selected" must never be reported as "used"; used-in-answer comes only from `ANSWER_BASIS_LINKED` (ADR-0071).
- **RET-36-08** Trace recording must be non-blocking and sanitized.

Bind the settled F0035 interface and resolve the answer-generation model profile with AI Engineer and Architect (D5). The extraction model's 4,096-token window is not an answer-generation decision. Source/canonical semantics, v1/v2 content dispatch and ADR-0058 locator precision remain intact. Counts and financial calculations continue through typed authorized queries. Baseline acceptance does not require F0068.

Use [EX-RET-001–006](../../examples/governed-evidence-retrieval.md), the [evaluation protocol](../../testing/evaluation-strategy.md#governed-retrieval-and-spectral-experiment-evaluation) and the [authorization carry-in](../../security/authorization-review.md#governed-retrieval-carry-in-2026-11-06) when writing stories and proof plans. RET IDs must remain traceable into the PRD and acceptance criteria.
