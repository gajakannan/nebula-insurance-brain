# Architect Implementation Review — F0009 run 2026-11-24-08701e37

Reviewer: Claude (Opus 5.5) / Architect
Date: 2026-11-24

## Conformance to the approved design

The as-built implementation follows the reconciled assembly plan (Phase B with rework `2026-11-24-c32acf46`, plus the G0 reconciliation), including:

- the closed 17-kind edge table, enforced in both the schema and the domain;
- the metadata-first reader order;
- the fixed limits and error categories;
- the review preflight with "always re-evaluate" refusals (PR-H1);
- an atomic reservation under a server-owned marker and a deferred constraint;
- the guarded downgrade;
- F0011 registration of all five resources.

## Recorded design corrections (G2)

1. **`provenance-result-v1` `fact_change.from_version_id` is now `string|null`.** A creation change has no predecessor, and the shipped commit writes NULL. This is an F0009-owned schema that had not been released. `sources.yaml` carries the new hash.
2. **The attempt's `authorization_decision_id` binds to `audit_event.decision_id`,** checked by the guard for the actor, resource and action. The design's FK pointed at `audit_event(id)`, a per-row random id.
3. **`uq_review_decision_owner` is added in 0016.** It was absent in 0005/0006 and the composite owner FKs need it.
4. **`review-decision` is promoted from OpenAPI-only to a bundled resource** (retain-versioned-boundary), because `provenance-result-v1` references it.
5. **F0008's migration identity test is pinned to `0015`,** its own head. 0016's tables and grants are proven by F0009's own suite.

None changes a story requirement, a route, a grant or canonical semantics. All five are reflected in the delivered code and tests.

## ADR-0080 proof status

ADR-0080's runtime proof gates are met in this run:

- current-authority materialization (S0004);
- atomic reservation (S0005);
- non-applied attribution (S0002 AC6);
- legacy byte identity and the guarded downgrade (S0006 AC1/AC2);
- F0011 conformance (S0006 AC3).

ADR-0080 remains **Proposed**. Formal acceptance is a separate operator decision.

## Knowledge-graph delta (for G7)

- **Bind to code:**
  - `capability:provenance-lineage` → `engine/packages/brain-provenance/**`, `brain_domain/provenance.py`, `brain_persistence/provenance.py`;
  - `capability:learning-candidate-reservation` and `capability:review-submission-attribution` → `brain_persistence/provenance_models.py` and migration 0016.
- **Extend existing bindings:** `capability:evidence-review-round-trip` (already covers `decisions.py`) and the authorization capability (already covers `execution.py`).
- **PR-L3:** narrow the F0009 story mappings.

## Result

Result: PASS
