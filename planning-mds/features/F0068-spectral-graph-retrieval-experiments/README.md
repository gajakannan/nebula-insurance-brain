# F0068 — Spectral graph retrieval experiments

**Status:** Planned
**Phase:** v0.4+
**Roadmap:** Later
**Scope:** Future; conditional experiment, not a baseline retrieval prerequisite

## Overview

Test whether spectral structure adds useful insurance evidence beyond the measured F0035/F0036 baseline at an acceptable operating cost. This feature reserves the handoff's recommended separate home (D3) under the 2026-11-06 incorporation request. F0061 remains Advanced Retrieval: dense+sparse, multivectors, reranking and optional Qdrant.

Inspiration: SpectRAG research, with its official implementation and the independent SpectraFuse implementation referenced in the [handoff](../../architecture/nebula-spectral-graph-intelligence-handoff.md). Implement approved ideas natively; no reference runtime dependency or storage replacement.

Design: [governed evidence retrieval](../../architecture/governed-evidence-retrieval-design.md). Governing proposal: [ADR-0076](../../architecture/decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md). Worked/boundary examples: [EX-RET-002/006](../../examples/governed-evidence-retrieval.md). Evaluation: [strategy](../../testing/evaluation-strategy.md#governed-retrieval-and-spectral-experiment-evaluation).

## Entry conditions

F0033/F0034 production contracts and F0035/F0036 baseline measurements must be available. The owning feature plan must record a separate experiment scope, scheduling and cost decision after those measurements. Reservation does not authorize PR-07/PR-08, move work into v0.2A, or enable any runtime flag. F0061 comparators are used when available; F0067 can consume recorded diagnostics later.

## Scope and acceptance inputs

- **RET-68-01 — Versioned artifacts.** Weighted sparse adjacency with raw signals and typed input lineage; deterministic node maps; normalized Laplacian and component-aware eigenpairs; checksummed manifests with atomic BUILDING-to-READY publication, failed-build isolation and idempotent rebuild. No canonical direction changes or authoritative writes.
- **RET-68-02 — Eligibility and compatibility.** Exactly match the authorized influence domain, requested root, knowledge mode, pinned semantic/temporal view, content/ontology/model/edge profiles and authorization revisions. Current grants apply at use and replay. On mismatch, use compatible authorized baseline retrieval or a separately approved bounded local experiment; otherwise report a gap. Prove unauthorized non-influence (RET-35-03).
- **RET-68-03 — Numerical correctness.** Sparse scale/memory proofs; isolated/small/disconnected and repeated-eigenvalue cases; residuals, orthogonality and subspace/scoring reproducibility. Remove all trivial modes for nontrivial proximity coordinates; handle the zero subspace correctly for heat, comparing small graphs with an exact exponential. No mass crosses disconnected components.
- **RET-68-04 — Independent modes.** Optional `graph_spectral`, `graph_heat`, `graph_ppr_spectral`; `spectral_no_expansion` is benchmark-only. Reject unsupported/disabled modes, preserve calibrated score components and record effective fallback/projection IDs. PPR fusion applies only if PPR exists and passes stochastic tests.
- **RET-68-05 — Incremental evaluation.** Reuse the frozen-family split and exact budget protocol; compare against strong hybrid, budget/expansion baseline C, optional D and available rerankers. Hold candidate graphs fixed for scoring ablations. Report paired confidence intervals and quality, latency, memory, build/index and partition costs. Upstream results are not Nebula evidence.
- **RET-68-06 — Promotion.** Pre-register worthwhile gain and cost limits before held-out scoring. Permission-safe shadow evidence, limited opt-in, owner approval and rollback proof precede activation. Default enablement is a separate decision; record deferral if benefit does not justify cost. Baseline delivery remains valid.

## Exclusions

No new embedding training, canonical fact admission, ontology mutation, insurance adjudication, replacement evidence selectors, re-parsing, global per-query decomposition, or F0061/Qdrant scope transfer. Discovery/anomaly/drift uses beyond retrieval require their own later scope decision.

## Role handoff and open decisions

PM owns the experiment question and scope. Architect owns boundaries and manifests. AI Engineer owns numerical methods and tuning. QE owns held-out evaluation and correctness evidence; Security owns partition/cache/replay non-influence review. Numeric thresholds, solver/dependency selection, dimensions, recomputation policy and resource budgets remain decisions for this feature's plan after baseline evidence.

## Documents

The PRD, STATUS, GETTING-STARTED, stories and assembly plan are authored through this feature's Phase A/B plan actions. This folder reserves the identifier and carries requirements; no feature-plan approval or runtime delivery is claimed. Authored shard: `planning-mds/kg-source/features/F0068.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
