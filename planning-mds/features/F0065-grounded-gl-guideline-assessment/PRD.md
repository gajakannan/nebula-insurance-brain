# F0065 — Grounded GL guideline assessment — PRD

## Feature Header

**Feature ID:** F0065
**Feature Name:** Grounded GL guideline assessment
**Priority:** High
**Phase:** v0.1B
**Status:** Draft — scope incorporation authorized 2026-09-07; implementation and architecture signoffs pending.

## Feature Statement

**As a** GL underwriter reviewing a policy
**I want** an evidence-backed comparison of its applicable each-occurrence limit with a specified guideline
**So that** I can see the result, the exact inputs and rule used, and why a conclusion could not be reached.

## Business Objective

Deliver a bounded neurosymbolic workflow in v0.1: ontology/profile-guided neural interpretation produces assertions; governed acceptance produces canonical facts; a deterministic rule evaluates those facts. The product question is “Does this applicable limit meet this specified guideline?” The result is a guideline assessment, not a policy approval or a general risk score. No embedding dependency is needed for this workflow.

## Scope & Boundaries

**In Scope:**
- A versioned, explicitly selected guideline rule with one operation: compare an accepted each-occurrence monetary limit against a minimum, using exact decimals and matching currency, coverage, policy term, and scope.
- On-demand evaluation at explicit valid-time and recorded-time coordinates using a consistent semantic snapshot and a pinned rule version.
- Immutable assessment records with input fact versions, rule/ontology versions, evaluator version, comparison, evidence lineage, time basis, actor, and audit linkage.
- Explicit `MEETS_GUIDELINE`, `BELOW_GUIDELINE`, `UNKNOWN`, `CONFLICT`, and `NOT_APPLICABLE` outcomes; authorization failures and invalid rule definitions are errors outside this outcome vocabulary.
- Reassessment after an accepted correction, retraction, endorsement, or rule release without silently reusing a historical assessment as current.
- An assessment panel in the existing Entity 360, linked to Document 360 evidence and the existing review path.
- A synthetic worked example and challenge cases, linked to concepts, contracts, stories, and future runtime acceptance fixtures.

**Out of Scope:**
- Arbitrary first-order logic strings, user-supplied executable code, multi-rule chaining, general OWL/Datalog reasoning, or autonomous rule learning (F0055, F0060, F0062).
- Automatic propagation through a graph of persisted derived canonical facts (F0056). Assessment records are not automatically promoted into canonical facts.
- Business approval, issuance, workflow execution, general normative obligations, or a full decision ledger/replay product (F0048–F0059).
- Semantic vector search (F0033, v0.2A), a new graph UI, a rule-authoring workbench, currency conversion, or general coverage interpretation.

## Acceptance Criteria Overview

- [ ] The synthetic $500,000 each-occurrence limit compared with the fictional $1,000,000 minimum yields `BELOW_GUIDELINE`; $1,000,000 and $2,000,000 yield `MEETS_GUIDELINE`.
- [ ] Missing, conflicting, mismatched, and inaccessible inputs follow the [assessment contract](assessment-contract.md), without treating confidence as approval authority.
- [ ] Every evaluated result identifies the exact fact and rule versions and resolves authorized evidence; the comparison uses no model call.
- [ ] An endorsement accepted after its effective date produces distinct answers at the documented valid/recorded coordinates. Earlier assessment records remain unchanged.
- [ ] Revoking access prevents disclosure through assessment outcomes, explanations, history, citations, or caches.
- [ ] F0024 runs the real interpretation-to-assessment path; F0025 proves temporal reassessment; F0026 verifies the challenge suite and reports extraction quality separately from deterministic evaluator correctness.
- [ ] A new contributor can follow the worked example from source to result; structured examples validate and their references resolve.

## UX / Screens

Extend the existing Entity 360 under F0023. The panel displays the guideline name/version, plain-language result, selected time basis, the two compared values, and “Show evidence.” Historical results display their evaluation context. Unknown/conflict results show only authorized reasons and a link to the existing review path where permitted. Loading, unavailable, denied, and invalid-request states are separate from assessment outcomes. An assessment never displays an approval button or changes policy status.

## Data Requirements

Use [assessment-contract.md](assessment-contract.md) for proposed rule, request, result, freshness, and access semantics. Reuse canonical identity, typed money, qualifiers, evidence bindings, principal resolution, and bitemporal querying. The educational fixture schema validates the example bundle only; it is not a production persistence or API contract. The architect must bind the service DTOs to the proven kernel contracts before implementation freezes them.

## Dependencies

- F0001 pre-build proofs; F0002/F0003 tenant-aware domain and persistence.
- F0006–F0013 assertions, qualified facts, temporal history, provenance, changes, schemas, and ontology.
- F0015/F0016 interpretation profiles/runs and F0017 entity resolution supply the neural-to-symbolic path.
- F0018/F0019 authorized canonical commits and endorsement supersession; F0020 authorized temporal reads.
- F0021–F0023 supply the shell, evidence review, and Entity 360 for S0005. S0001–S0004 do not depend on the UI.
- F0024/F0025 consume F0065 for integration acceptance; F0026 owns release evaluation. These are downstream consumers, not prerequisites, avoiding a dependency cycle.
- Accepted ADR-0001, ADR-0007, ADR-0010, ADR-0023, ADR-0026 and the proposed [ADR-0056](../../architecture/decisions/ADR-0056-bounded-neurosymbolic-assessment.md). Existing proposed identity, source-authority, and typed-value decisions retain their proof requirements.

## Success Criteria

All specified deterministic and boundary cases pass. The end-to-end suite uses real model interpretation and reports field errors, severe errors, abstention, review workload, latency, and cost separately. Synthetic documentation outputs are not measured model performance. F0026 sets measured quality thresholds with named owners and a frozen holdout before release; examples used for development are excluded from that holdout.

## Risks & Assumptions

The $1,000,000 minimum is a fictional fixture rule, not an insurance-wide requirement. Production guideline authority, applicability, release approval, and benchmark thresholds must be established by the product owner/domain steward during feature planning. Rule definitions are reviewed versioned assets in v0.1. A consistent snapshot and current grant checks are required even when a request asks for historical knowledge. See the assembly plan for proof gates and ownership.

## Related Stories

- [S0001 — Versioned guideline rule](F0065-S0001-versioned-guideline-rule.md)
- [S0002 — Evaluate accepted facts](F0065-S0002-evaluate-accepted-facts.md)
- [S0003 — Preserve assessment lineage](F0065-S0003-preserve-assessment-lineage.md)
- [S0004 — Temporal reassessment](F0065-S0004-temporal-reassessment.md)
- [S0005 — Explain assessment in Entity 360](F0065-S0005-explain-assessment-in-entity-360.md)
- [S0006 — Reproducible worked examples](F0065-S0006-reproducible-worked-examples.md)

## Review Evidence

Planning evidence: this PRD, the story acceptance criteria, [assembly plan](feature-assembly-plan.md), [contract](assessment-contract.md), and [worked example](../../examples/neurosymbolic-gl/README.md). Structural checks do not grant Phase A/B approval or prove the runtime. Story execution and signoffs remain pending in [STATUS.md](STATUS.md).
