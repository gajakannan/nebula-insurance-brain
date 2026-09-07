# F0065 assembly plan

**Status:** Draft; user-authorized v0.1 scope, no completed Phase A/B gates or runtime proof claimed.

## Ownership and boundaries

Backend owns the assessment service, deterministic comparison, persistence, snapshots, and authorization in `engine/`. AI engineering owns the existing profile-guided interpretation integration in `neuron/`; it proposes assertions through kernel services. Frontend owns the existing Entity 360 extension in `experience/`. The architect/domain steward owns guideline/ontology definitions; QA owns the independent expected results and release evaluation. These are future runtime deliverables, not paths claimed to exist today.

## Build order

| Step | Stories / owner | Assembly and exit condition |
|---|---|---|
| 1 | S0006 / architect + QA | Agree on the synthetic scenario, vocabulary, and expected-case table; validate example structure. Runtime reproduction remains open until step 7. |
| 2 | S0001 / architect + backend | Bind the draft contract to F0011/F0013 typed values and approved rule-release authority. Reject unsupported syntax; record release audit. |
| 3 | S0002 / backend | Consume F0018–F0020 canonical snapshot reads. Implement the finite outcome table and exact-decimal comparison without model calls. |
| 4 | S0003 / backend + security | Persist immutable assessments with exact lineage and audit; prove idempotency and denied access before disclosure. |
| 5 | S0004 / backend + QA | Prove correction, retraction, retroactive endorsement, rule release, concurrent snapshot, and historical grant behavior. |
| 6 | S0005 / frontend + backend | Extend F0023 Entity 360, using F0022 evidence/review links; include historical, loading, unknown, conflict, and access-error states. |
| 7 | S0006, F0024/F0025 / AI + QA | Run actual model interpretation through reviewed canonical acceptance and assessment, publish runnable instructions and evidence. |
| 8 | F0026 / QA + reviewers | Evaluate the independent frozen slice, report extraction and deterministic-rule results separately, and complete release signoffs. |

F0065 depends on the canonical kernel, F0018/F0019, and F0020. Only its UI story depends on F0021–F0023. F0024/F0025 depend on F0065 for their expanded integration acceptance, not vice versa. F0030, F0033, F0055, F0056, and Temporal are not build prerequisites.

## Interfaces and storage

Service boundary proposed: `assess(subject, rule_release, time_context, verified_principal, idempotency_key)` and `get_assessment(id, verified_principal)`. The API adapter must use existing principal and ProblemDetails contracts and parameterized kernel queries. Runtime OpenAPI, database migration, DTOs, and permission mapping must be authored against proven upstream contracts before these steps ship; the educational JSON is not imported as canonical SQL.

Separate `GuidelineRuleVersion` and `AssessmentRecord` repositories from canonical facts. Rules and assessments are immutable versioned records. Inputs refer to `CanonicalFactVersion`; evidence is traversed through existing lineage. Use a single consistent read basis and the existing audited transaction pattern. Define the exact persisted snapshot identifier against F0003/F0018 before implementation; no hidden dependence on a new projection engine.

## Validation and review

Planning now: story validation, project/feature readiness, KG reproducibility, example-schema/reference validation, and tracker synchronization. Runtime later: table-driven evaluator cases; typed decimal and boundary tests; transaction/idempotency/snapshot integration; access and revocation negative cases; Entity 360 interaction checks; real extraction-to-result canary; independent frozen evaluation. Runtime tests must compare observed outputs with authored expected outcomes, not regenerate expectations from the evaluator.

ADR-0056 remains Proposed until its named proof results and architect/security/QA reviews are recorded. Existing proposed source-authority, typed-value, and access decisions remain governed by their own acceptance conditions. No unexecuted acceptance checkbox or structural tooling pass counts as signoff.

## Open decisions before implementation

| Decision | Owner | Required by |
|---|---|---|
| Production guideline source, applicability scope, and release approver | Product owner + domain steward | S0001; synthetic demo may use its explicitly fictional rule |
| Runtime snapshot identifier, transaction layout, DTO/OpenAPI and schema bindings | Architect + backend | S0002/S0003, after upstream contract proofs |
| Canonical conflict/completeness query binding and reason mapping | Architect + backend | S0002; the full F0028 conflict engine is not required |
| Named evaluation reviewers, licensed holdout, quality/latency/cost thresholds | QA + product owner | F0026 release gate |

## Rollout

Ship the bounded comparison through the existing GL slice in v0.1B and qualify it in v0.1C. Start with a reviewed fixed rule release and scoped internal users. Operational logs record identifiers and outcomes without source text. S0005 exposes the rule and time basis to the user. Later reasoners and dependency propagation reuse these identities and lineage without redefining an assessment as an approval.
