# F0035 — Hybrid search + consistent authorized rows/counts/facets/graph scope

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

Search fusion across full-text, vector, graph, ontology, temporal, and metadata signals with authorization applied before rows, counts, facets, and graph paths (sections 51, 120.3).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0024](../../architecture/decisions/ADR-0024-search-is-multi-modal.md), [ADR-0053](../../architecture/decisions/ADR-0053-permission-safe-retrieval-and-historical-access.md). Likely predecessors (inferred, confirm at Phase B): F0033, F0034.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0035.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Governed retrieval carry-in (2026-11-06)

The operator requested incorporation of the [spectral graph handoff](../../architecture/nebula-spectral-graph-intelligence-handoff.md). These are Phase A requirements inputs; this feature remains Planned and has no new phase approval. [Integrated design](../../architecture/governed-evidence-retrieval-design.md); [ADR-0076](../../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) is Proposed. The baseline is v0.2A, later trace visualization is v0.2B, and the separate [F0068 experiment](../F0068-spectral-graph-retrieval-experiments/README.md) remains conditional at v0.4+.

- **RET-35-01** Seeds, expansion neighbors, edge existence and counts must be authorized before scoring or logging (see the handoff).
- **RET-35-02** A rooted query must never broaden to the principal's full visible corpus.
- **RET-35-03** Negative proof (see the handoff): with admissible inputs unchanged, changing or revoking an unauthorized node or edge must not change returned IDs, paths, score components, visible counts or selected context.
- **RET-35-04** Every request must pin one execution basis (see the handoff); incompatible or missing projections must take a recorded authorized fallback or return an explicit gap.
- **RET-35-05** Implemented modes must be independently switchable. `hybrid_only` and `graph_expand` are baseline modes; `graph_ppr` remains an optional comparator. Unknown, unimplemented or disabled modes must be rejected explicitly.
- **RET-35-06** Expansion must be bounded by hops, candidates, fan-out, per-edge-type caps and wall-clock limits, and must record the path to each candidate (see the handoff).
- **RET-35-07** Seed fusion must preserve per-retriever ranks and must not blend uncalibrated raw scores (see the handoff).
- **RET-35-08** Backend loss must degrade to authorized lexical retrieval, never unfiltered retrieval.
- **RET-35-09** PPR, if implemented, must be row-stochastic with explicit dangling-node handling (see the handoff).

Phase A may clarify the user problem first; F0033/F0034 projection and checkpoint contracts must be settled before this feature's Phase B approval. Their runtime adapters must be delivered before production integration. QE and PM plan the corpus/runner before baseline measurement (D4). Architect owns package placement and schemas (D6), AI Engineer and domain steward own profile hypotheses (D7), and Security owns cache/replay rules (D9). Read-path traces start here and do not depend on F0067 rendering. Spectral work belongs to F0068 at v0.4+.

Use [EX-RET-001–006](../../examples/governed-evidence-retrieval.md), the [evaluation protocol](../../testing/evaluation-strategy.md#governed-retrieval-and-spectral-experiment-evaluation) and the [authorization carry-in](../../security/authorization-review.md#governed-retrieval-carry-in-2026-11-06) when writing stories and proof plans. RET IDs must remain traceable into the PRD and acceptance criteria.
