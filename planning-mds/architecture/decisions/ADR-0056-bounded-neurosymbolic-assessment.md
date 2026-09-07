# ADR-0056: Bounded Neurosymbolic Assessment in v0.1

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-07
**Deciders:** Architect, domain steward, security reviewer, and quality engineer; acceptance requires recorded proof results below.
**Source:** User-authorized roadmap amendment, master blueprint section 124, F0065.

## Context

v0.1 already plans model-based interpretation, typed assertions, governed canonical acceptance, evidence, and temporal state. General native reasoning was scheduled for v0.4+, leaving no concrete rule evaluation in the first GL demonstration. A bounded guideline assessment makes the neural/symbolic interaction observable and teaches the repository's concepts without requiring vector search or a general reasoner.

## Proposed decision

Add F0065 in v0.1B. A reviewed, immutable guideline rule performs one typed monetary comparison against canonical facts from an explicit consistent snapshot. Persist an immutable assessment and exact derivation lineage separately from canonical facts. Recompute on demand; prior records remain historical. Access to the result and its complete relevant input/evidence lineage is checked under current permissions. Model confidence is an interpretation signal; an assessment is not business approval.

The supported subset, outcome/error distinction, temporal rule selection, and freshness behavior are defined in the [assessment contract](../../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md). This narrows the section 89 exclusion to a general reasoning engine. Accepted ADRs on semantic ownership, bitemporality, provenance, and retrieval projections remain in force.

## Alternatives and consequences

- Moving all of F0055/F0056 into v0.1 would introduce general inference, authoring/workbench dependencies, and automatic derivation propagation. Those remain later capabilities.
- On-demand evaluation introduces repeated bounded computation but avoids a cross-request stale-result cache and a dependency worker in the first release.
- A combined entity/fact/vector JSON view is useful for explanation but does not become a storage authority. The model's neural interpretation supplies the neural part even before embeddings ship.
- Fixed source-controlled rule releases are sufficient for v0.1; production applicability and approval of those assets still need a named domain owner.
- The documentation example is a development fixture. It is not benchmark evidence and must remain outside the frozen holdout.

## Acceptance conditions

| Proof | Owner | Release gate | Recorded result |
|---|---|---|---|
| Decimal comparison, qualifier/currency applicability, missing/conflicting input outcomes, unsupported syntax | Backend + QA | F0065 S0001/S0002 | Not executed |
| Exact input/rule lineage, idempotency, consistent snapshot under concurrent commits | Backend + architect | F0065 S0003/S0004 | Not executed |
| Retroactive endorsement, correction/retraction, rule release, current versus historical answers | Backend + QA | F0025 / F0065 S0004 | Not executed |
| Complete lineage authorization and revocation across result/history/evidence/UI | Security reviewer | F0065 S0005 and F0026 | Not executed |
| Real neural interpretation through canonical acceptance to comparison and independently authored expected result | AI engineer + QA | F0024 and F0026 | Not executed |

Scope scheduling is authorized; this record remains Proposed until the proofs and reviewer identities/evidence are recorded. No new approval checkpoint is needed merely to author the authorized planning package.

## References

- [F0065 PRD](../../features/F0065-grounded-gl-guideline-assessment/PRD.md)
- [Assembly plan](../../features/F0065-grounded-gl-guideline-assessment/feature-assembly-plan.md)
- [Worked example](../../examples/neurosymbolic-gl/README.md)
- [ADR-0026: derivation lineage](ADR-0026-derived-facts-have-dependency-lineage.md)
