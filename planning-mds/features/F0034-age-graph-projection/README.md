# F0034 — AGE graph projection

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

Apache AGE provides openCypher traversal over canonical entities and relationships as a rebuildable projection with commit-consistent delivery (sections 47 to 49, 109.3).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0022](../../architecture/decisions/ADR-0022-apache-age-is-the-graph-projection.md), [ADR-0041](../../architecture/decisions/ADR-0041-atomic-semantic-commit-and-projection-delivery.md). Likely predecessors (inferred, confirm at Phase B): F0003, F0018.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0034.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Build AGE from accepted canonical records and the existing outbox/rebuild path. Do not load upstream graph exports directly; local extraction IDs and deduplication have no canonical authority.

## Graph Observatory carry-in (2026-10-13)

[ADR-0071](../../architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Design: [design note section 10](../../architecture/graph-observatory-design.md#10-delivery-approach-carry-the-contract-in-now-land-the-observatory-in-v02b). The scoped Observatory is [F0067](../F0067-graph-observatory/README.md).

- Give every projection build a stable version identifier and keep it queryable, so a trace can cite the projection it used and a replay can tell when that version is no longer available (ADR-0071 section 4).

## Governed retrieval carry-in (2026-11-06)

The operator requested incorporation of the [spectral graph handoff](../../architecture/nebula-spectral-graph-intelligence-handoff.md). These are Phase A requirements inputs; this feature remains Planned and has no new phase approval. [Integrated design](../../architecture/governed-evidence-retrieval-design.md); [ADR-0076](../../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) is Proposed. The baseline is v0.2A, later trace visualization is v0.2B, and the separate [F0068 experiment](../F0068-spectral-graph-retrieval-experiments/README.md) remains conditional at v0.4+.

- **RET-34-01** Projected relationships must keep type, direction and input-version references sufficient to re-evaluate mode, temporal and authorization predicates per edge (see the handoff).
- **RET-34-02** The projection must define its own consumer checkpoint and rebuild contract; it must not reuse the shared processed marker of the current outbox worker (see the handoff).
- **RET-34-03** Traversal must accept an eligibility predicate applied to every intermediate vertex and edge.
- **RET-34-04** Current-only topology must declare itself as such and must not serve as a historical fallback (see the handoff).

Settle consumer-specific checkpoint, replay/rebuild, temporal-view and atomic cutover contracts with F0033 (D8) before F0035 Phase B approval. Preserve original domain direction/type; optional F0068 numerical adjacency is a separate derivative.

Use [EX-RET-001–006](../../examples/governed-evidence-retrieval.md), the [evaluation protocol](../../testing/evaluation-strategy.md#governed-retrieval-and-spectral-experiment-evaluation) and the [authorization carry-in](../../security/authorization-review.md#governed-retrieval-carry-in-2026-11-06) when writing stories and proof plans. RET IDs must remain traceable into the PRD and acceptance criteria.
