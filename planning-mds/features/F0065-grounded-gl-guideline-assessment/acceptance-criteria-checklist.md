# Acceptance Criteria Checklist — F0065

Applied to stories F0065-S0001 to F0065-S0006 at Phase A (2026-09-07, plan run `2026-09-07-38aed4ad`).
Items marked N/A carry the reason. Checking an item asserts that the *written criteria* satisfy it, not
that any runtime behavior has been observed; every story remains Not Started.

## 1) Clarity & Testability

- [x] Each criterion is specific and measurable (exact decimal amounts 500000.00 / 1000000.00 / 2000000.00, named outcome constants, named valid/known dates, typed error classes)
- [x] No vague terms; "current" is defined as the resolved snapshot rather than a claim about later acceptances
- [x] Pass/fail is unambiguous — the outcome vocabulary is a closed set (`MEETS_GUIDELINE`, `BELOW_GUIDELINE`, `UNKNOWN`, `CONFLICT`, `NOT_APPLICABLE`) and errors are explicitly outside it
- [x] Comparison determinism is stated as a testable property: zero model calls during the comparison

## 2) Coverage

- [x] Happy path covered in every story
- [x] At least one error or edge case covered in every story (rule released after the requested known time, retracted value with no replacement, unresolved conflict, concurrent commit during evaluation, failed save shown as a persisted result, dangling fixture reference)
- [x] Boundary values covered explicitly — the amount equal to the minimum is asserted as `MEETS_GUIDELINE`, not left to inference (S0002)
- [x] Permission behavior specified in every story that returns or displays a result (S0001–S0005); S0006 states N/A with reason (synthetic documentation only)
- [x] Negative-knowledge cases separated from extraction failure: an explicit absent coverage is `NOT_APPLICABLE`, an unknown presence is `UNKNOWN` (S0002, S0006 challenge table)

## 3) Data Validation

- [x] Required fields enforced (rule identity/version, authority and source references, ontology release, effective interval, tenant/KB scope, coverage type, limit basis, currency, operation, decimal minimum)
- [x] Formats and constraints specified (exact decimals with no implicit currency conversion, matching limit basis, non-empty effective intervals, explicit valid/known coordinates)
- [x] Malformed input rejected before evaluation (negative or malformed monetary values, empty intervals, unsupported operators, free-form logic strings)
- [x] Duplicates and conflicts handled (idempotency key replay yields at most one record; the same key with different content is rejected; unresolved source conflict yields `CONFLICT` rather than a confidence-ranked pick)

## 4) Error Handling

- [x] Error messages are actionable (rule-unavailable, unsupported-operation, invalid-definition are typed and distinct)
- [x] System errors have a user-safe message — access denials disclose no existence, no missingness reason, and no partially supported outcome
- [x] Error ordering is specified: request/definition validity and authorization are resolved before any business outcome is disclosed
- [x] Failure is never rendered as success — a failed persistence operation returns an error rather than a saved result (S0003, S0005)

## 5) Navigation & Feedback

- [x] The single UI surface is specified as an extension of the existing F0023 Entity 360, with no new standalone workbench (S0005)
- [x] Loading, service-failure, and invalid-request states are specified as distinct from business outcomes
- [x] Historical results are labeled with their original coordinates and are not presented as a new current evaluation
- [x] The panel is specified to expose no policy-approval action
- N/A for S0001–S0004 and S0006: no user-facing surface; those stories deliver service, persistence, and documentation behavior

## 6) Non-Functional Criteria

- [x] Security expectations stated (verified principals, current grants on every read including history, complete relevant lineage required before disclosure, revocation covering result, title, count, explanation, citations, and transport cache)
- [x] Reliability expectations stated (single consistent snapshot per assessment, no mixed pre/post-change fact sets, idempotent retry, append-only records)
- [x] Determinism expectations stated (exact decimal arithmetic, pinned rule and ontology versions, recorded evaluator version)
- [x] Performance and cost expectations are deliberately deferred to F0026 with a named owner, rather than invented per story
- [x] Logging constraint stated (identifiers and outcomes in operational logs; no source text)

## 7) Audit & Timeline

- [x] Mutations name their audit records (rule-release installation audit; assessment creation recording acting principal, rule release, request/snapshot, and outcome; access denials under existing audit controls)
- [x] Immutability stated for both mutable-looking records — a changed minimum creates a new rule release, and earlier assessment records remain unchanged
- [x] Provenance path stated end to end (assessment → fact versions → assertions → interpretation runs → evidence), with extraction confidence kept on the assertion
- N/A for S0006: authors documentation and fixtures; it records no runtime audit event of its own

## 8) Out of Scope

- [x] Explicit non-goals listed in every story
- [x] The feature-level boundary is stated as a product claim, not only a technical one: an assessment is not a policy approval, is not promoted to a canonical fact, and does not change policy status
- [x] Deferred work is routed to named owning features (F0055 general reasoning, F0056 derivation propagation, F0033 retrieval, F0028 conflict engine, F0048–F0059 process and decision ledger)

## Open Requirement Questions (G1)

These are recorded as unresolved requirements, not as satisfied criteria. Each is owned in the
[assembly plan](feature-assembly-plan.md) open-decisions table and blocks implementation, not Phase A.

| # | Question | Owner | Blocks |
|---|---|---|---|
| 1 | Production guideline source, applicability scope, and release approver — the EX-GL-001 threshold is explicitly fictional | Product owner + domain steward | S0001 implementation |
| 2 | Which administrative authority installs a rule release, given that `policy.csv` today declares only TenantMember, Reviewer, and ServicePrincipal | Product owner + Security | S0001 implementation |
| 3 | Measured quality, latency, and cost thresholds, and the named reviewers and licensed frozen holdout | QA + product owner | F0026 release gate |
| 4 | Whether the assessment panel needs a persona file, or whether "GL underwriter" and "domain steward" remain role-descriptive only | Product Manager | Not blocking; see G1 decision note |
