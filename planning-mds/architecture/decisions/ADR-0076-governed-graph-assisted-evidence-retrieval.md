# ADR-0076 — Retrieval graph structure is a governed, derived ranking signal

**Status:** Proposed
**Date:** 2026-11-06
**Owners:** Architect; Security review required
**Scope:** F0033–F0036 baseline contracts; F0068 conditional experiment; F0067 read-only diagnostics

## Context

An insurance answer can require original wording, an amending endorsement and its effective date together. Independent passage rankings can omit that bridge evidence under a fixed context budget. The [handoff](../nebula-spectral-graph-intelligence-handoff.md) proposes set-oriented retrieval and optional spectral experiments inspired by SpectRAG/SpectraFuse. Its incorporation is a planning amendment, not proof that retrieval exists or authorization to implement an experiment.

PostgreSQL canonical records, persisted content, admission, evidence locators, current authorization and bitemporality already have owners. AGE and pgvector remain rebuildable projections under ADR-0022/0023. A relevance algorithm cannot introduce a competing truth or permission system.

## Decision Drivers

- Complete, inspectable evidence sets within the actual model window.
- Current-grant and requested-root isolation, including intermediate and derived inputs.
- Historical correctness, exact lineage and reproducible projection versions.
- Baseline delivery independent of numerical research or additional stores.

## Decision (proposed)

1. Build a derived retrieval plane over immutable evidence blocks, source bindings and directed typed canonical relationships. It cannot admit assertions or write canonical truth. Numerical symmetrization never changes domain direction or meaning.
2. Apply root, requested scope, current grants, source/dependency restrictions, knowledge mode and both temporal coordinates inside every adapter before scoring, counting or recording. Source retrieval preserves wording without conferring canonical eligibility (ADR-0075).
3. Pin one execution basis with coherent input/projection versions. Reauthorize at evidence use and replay. An incompatible optional projection permits only a recorded compatible authorized fallback or explicit gap. A historical query never silently reads current-only topology.
4. Deliver hybrid rank fusion, bounded typed expansion and token-budgeted context in F0035/F0036. Preserve individual seed ranks; do not blend incomparable raw scores. PPR remains an optional stochastic comparator.
5. Select evidence under the exact model tokenizer/window; revalidate locators, preserve precision and semantic grouping, recount after authorization changes, and disclose missing evidence. Only ADR-0046 answer citations and ADR-0071 `ANSWER_BASIS_LINKED` establish use. Sanitized trace recording is non-blocking; F0067 consumes it later.
6. Reserve spectral coordinates, heat diffusion and their derived manifests for F0068 at v0.4+. A stored basis requires an exactly compatible authorized influence domain and temporal/mode/revision basis. Precomputed global structures spanning permission boundaries are prohibited absent a reviewed non-influence proof. Tenant partitioning or post-filtering alone is insufficient.
7. Retain the native stack. Do not install, vendor, wrap or copy reference implementations into the runtime, or introduce Neo4j/FAISS to match them. Package placement and detailed schemas remain Phase B decisions. No global per-query eigendecomposition or baseline solver dependency.

```text
persisted content + source/canonical records
    -> scoped, versioned vector/typed graph projections
    -> eligible seeds -> bounded expansion -> context selection
    -> locator + current-authority recheck -> grounded answer / gap
                       |
                       +-> sanitized trace -> later F0067 replay

F0068 optional compatible spectral/heat scores feed selection only.
No retrieval path writes back to canonical truth.
```

## Options Considered

| Option | Benefits | Costs / disposition |
|---|---|---|
| Hybrid + bounded typed expansion + context selection | Uses existing projection direction; independently measurable baseline | Additional eligibility and context contracts; proposed baseline |
| Optional PPR | Structural comparator without eigenbasis | Sink/convergence proofs and evaluation cost; optional |
| Scoped spectral/heat experiment | Tests wider structural relevance | Numerical, authorization-partition, temporal and rebuild costs; F0068 only |
| Adopt SpectRAG/SpectraFuse runtime stack | Reuses reference implementation | Conflicts with native storage/evidence/permission boundaries; not selected |
| Global spectrum followed by ACL filtering | Cheap reuse | Restricted topology can influence visible results; prohibited without proof |

## Consequences

F0033/F0034 must settle projection identities, per-consumer checkpoints and rebuild semantics before F0035 Phase B approval. F0036 must settle an answer model profile rather than borrowing the extraction model window. Phase B binds schemas to existing identity/evidence types. Baseline implementation can ship without F0068, F0061 or the F0067 renderer. Experimental quality and operating cost must be evaluated separately; lack of benefit is a valid reason to defer spectral delivery.

## Security and acceptance conditions

This ADR stays Proposed until the contracts are reviewed and runtime evidence proves:

- RET-35-03 non-influence: modifying an unauthorized node/edge with admissible inputs unchanged leaves visible IDs, paths, scores, counts and selected context unchanged; timing/cache inference is assessed.
- Root narrowing, source/canonical distinction, revocation, both time axes and incompatible-projection fallback pass, including current-only graph rejection for historical queries.
- Final payload budget and locator fidelity pass; only answer-basis linkage marks evidence used.
- Threat model and cache/replay rules are reviewed; no source text/private graph contents leak via traces or derived artifacts.

F0068 additionally needs sparse numerical/component/zero-mode proofs, atomic artifact recovery, measured incremental value/cost and its separate experiment/promotion decisions. Acceptance of baseline contracts does not activate F0068.

## References and follow-up

- [Integrated design and decision ownership](../governed-evidence-retrieval-design.md)
- [Security requirements](../../security/authorization-review.md#governed-retrieval-carry-in-2026-11-06)
- [Evaluation protocol](../../testing/evaluation-strategy.md#governed-retrieval-and-spectral-experiment-evaluation)
- [Worked and boundary examples](../../examples/governed-evidence-retrieval.md)

Related contracts: ADR-0003/0007/0010/0019, ADR-0022/0023/0024, ADR-0040/0041/0046, ADR-0053/0058, ADR-0062/0064, ADR-0071/0072/0073/0075. Their existing statuses and proof boundaries remain unchanged. D4–D9 in the integrated design identify the remaining Phase A/B deliverables and owners.
