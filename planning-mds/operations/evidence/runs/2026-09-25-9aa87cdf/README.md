# Validate run 2026-09-25-9aa87cdf

**Action:** `validate` · **Scope:** `all` · **FEATURE_ID:** unset · **Contract:** Feature Evidence Contract, `base-run-only`, 2026-07-11
**Subject:** branch `docs/utopia-evolution` @ `b1f4357` (ADR-0063 to ADR-0069, F0066 reservation, feature scope amendments, recompiled knowledge graph), base `main` @ `93cc8c1`
**Framework:** `nebula-agents` @ `c218bf1` (the product's pin)
**Status:** Complete. V3 approved with follow-ups by the operator on 2026-09-25. A-1, A-2, and P-4 are fixed on the branch, and a follow-up validate run covers the final state.

## Why this run exists

The subject branch was authored outside an action. This run is the framework validation of that branch: it re-executes the validator set through `run-gate.py`, adds PM and Architect judgment, and leaves an auditable record before integration.

## Validation Summary

| Lane | Report | Verdict | Blocking findings |
|---|---|---|---|
| Requirements (PM) | [pm-validation-report.md](pm-validation-report.md) | PASS WITH RECOMMENDATIONS | None; P-1 needs an operator decision |
| Architecture (Architect) | [architect-validation-report.md](architect-validation-report.md) | PASS WITH RECOMMENDATIONS | None; A-1 and A-2 recommended before integration |
| Implementation (validators) | [implementation-validation-report.md](implementation-validation-report.md) | PASS | None |

**Knowledge graph:** intact. Integrity, drift, reproducibility, and symbols all pass; coverage is 4 mapped, 62 excluded, 0 uncovered. Orphans fall from 30 (`main`) to 27; six are new ADR nodes that bind at each feature's `plan` G4.

**Findings needing action:**

| ID | Severity | Summary | Route |
|---|---|---|---|
| A-1 | Medium | ADR-0067 impact-hold detail could reveal restricted content | Fix on branch before integrate |
| A-2 | Medium | ADR-0066 does not state KB ownership of name facts and the alias projection | Fix on branch before integrate |
| A-3 | Medium | F0065 contract and stories lack the `basis_hash` its README amendment adds | F0065 plan update, or defer to F0056 |
| A-4 | Medium | F0005 (In Progress) not amended for ADR-0065 text origin and admission | Add to F0005 activation criteria, or defer with rationale |
| P-1 | Medium | F0025 v0.1B acceptance now depends on Proposed ADR-0064 | Operator decision |
| P-2 | Medium | v0.1A scope growth (storage and contract hooks) | Confirm at each Phase A |
| A-5 to A-7, P-3, P-4 | Low | Schema versioning obligations, orphans, §28 field list, F0066 persona, 2 lint hits | Feature planning / small edits |
| A-8, A-9, I-1 to I-3 | Info | Framework gaps (init-run, manifest wording, exec-and-log output capture, V3 checkpoint cannot be attested) | `nebula-agents` maintainer |

## Next step

At V3 the operator reviews the three reports and records a decision. Options:

- approve as-is;
- approve with follow-ups, then fix A-1, A-2, and P-4 on the branch and rerun this action;
- reject.
