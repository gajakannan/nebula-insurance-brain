# Feature assembly index

Per-feature plans are authoritative for their approved scope. Planning does not imply implementation or architecture approval.

| Feature | Assembly plan | Sequence / boundary |
|---|---|---|
| F0001 | [Archived foundation](../features/archive/F0001-repository-and-engineering-foundation/feature-assembly-plan.md) | Historical foundation; use current source/accepted ADR evidence for as-built details |
| F0002 | [Tenancy and AuthX kernel](../features/archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts/feature-assembly-plan.md) | Six stories after F0001; F0005 worker is an impacted consumer; Phase B design approved 2026-09-25; runtime unstarted |
| F0065 | [Grounded GL assessment](../features/F0065-grounded-gl-guideline-assessment/feature-assembly-plan.md) | Downstream consumer of F0002 current authority; separately governed plan |

| F0004 | [Content artifact model](../features/archive/F0004-content-artifact-model/feature-assembly-plan.md) | All four stories implemented in run 2026-10-17-8a6cc79f; G4 approved 2026-10-21; all required signoffs and G7 passed; activation limits retained |

| F0006 | [Assertion semantics and admission](../features/archive/F0006-assertion-plane-origin-and-interpretation-basis/feature-assembly-plan.md) | Bounded implementation in run `2026-11-02-5a00b0ff`: additive migration 0011 and source-bound storage/admission/current-consumer proof (336 unique final-lane cases: 306 engine, 15 importer, ten recovery, five content-worker); v1 defaults retained; trusted local synthetic fixtures only; ADR-0065/0075 remain Proposed; no live producer or production activation |

## Governed retrieval planning sequence (2026-11-06)

The [design amendment](governed-evidence-retrieval-design.md) is a cross-feature planning input, not an approved assembly plan. F0035 Phase A may clarify the need first; F0033/F0034 projection/checkpoint contracts settle before F0035 Phase B approval; production F0033/F0034 adapters precede F0035 integration; F0036 binds the retrieval interface and exact answer-model budget afterward. QE/PM establish the benchmark runner before implementation measurements. Each feature's plan action must produce its own PRD, stories, contracts and assembly plan.

F0067 reads the resulting trace events later; it does not gate emission. F0068 at v0.4+ owns conditional spectral/heat work after baseline measurement and a separate experiment decision. F0061 retains its existing scope. See Proposed [ADR-0076](decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md) and handoff PR-01–09 for role ownership and proof conditions.

| F0007 | [FactSlot model](../features/archive/F0007-factslot-model/feature-assembly-plan.md) | Done / Archived 2026-11-09 (feature run `2026-11-09-b94cfa12`; plan run `2026-11-09-60865e32`); additive migration 0012; 39 ACs and ADR-0077 proof gates evidenced; ADR-0077 still Proposed |
