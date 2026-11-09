# F0033 — pgvector retrieval

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

pgvector adds exact and approximate vector retrieval as a tenant-scoped projection; vectors locate evidence and never define truth (section 50).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0023](../../architecture/decisions/ADR-0023-pgvector-is-a-retrieval-projection.md). Likely predecessors (inferred, confirm at Phase B): F0003.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0033.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Assessment and example integration

F0065 already combines neural interpretation and symbolic rule evaluation in v0.1. This feature retains v0.2A vector retrieval scope: source/model/version-linked embeddings rank candidate evidence without defining facts or assessment confidence. See EX-FUTURE-001.

See the [example coverage map](../../examples/README.md) and [F0065](../F0065-grounded-gl-guideline-assessment/README.md).

## Governed retrieval carry-in (2026-11-06)

The operator requested incorporation of the [spectral graph handoff](../../architecture/nebula-spectral-graph-intelligence-handoff.md). These are Phase A requirements inputs; this feature remains Planned and has no new phase approval. [Integrated design](../../architecture/governed-evidence-retrieval-design.md); [ADR-0076](../../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) is Proposed. The baseline is v0.2A, later trace visualization is v0.2B, and the separate [F0068 experiment](../F0068-spectral-graph-retrieval-experiments/README.md) remains conditional at v0.4+.

- **RET-33-01** Embedding records must carry source block ID, owned scope, artifact/content version, model ID and version, so an eligibility predicate can run inside the vector query.
- **RET-33-02** Indexing must read the persisted content artifact and be idempotent per artifact version.
- **RET-33-03** The projection must expose a stable version identifier that an execution basis and trace can cite.

Settle independent projection checkpoints, coherent read/version identity and rebuild/cutover semantics with F0034 (D8) before F0035 Phase B approval. Synthetic adapters are contract proofs only. RET-33-01–03 cover the vector hooks; no spectral index is needed.

Use [EX-RET-001–006](../../examples/governed-evidence-retrieval.md), the [evaluation protocol](../../testing/evaluation-strategy.md#governed-retrieval-and-spectral-experiment-evaluation) and the [authorization carry-in](../../security/authorization-review.md#governed-retrieval-carry-in-2026-11-06) when writing stories and proof plans. RET IDs must remain traceable into the PRD and acceptance criteria.
