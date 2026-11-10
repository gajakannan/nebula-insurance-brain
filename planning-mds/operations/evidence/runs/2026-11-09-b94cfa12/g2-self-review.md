# Self Review — F0007-factslot-model run 2026-11-09-b94cfa12

- Roles: Backend Developer (implementation), Quality Engineer, DevOps; Architect plan conformance
- Reviewer: Claude (Opus 5.5)
- Date: 2026-11-09

## Scope Review

The as-built code matches the G0 plan's build order and file handoffs:

| Plan step | As built |
|---|---|
| 0 baseline | `engine/tests/fixtures/factslots/pilot-seed.sql` and `pilot-before.json`. The snapshot is generated from deterministic rows at 0011 (G0 reconciliation 3), not captured from a live database. |
| 1 pure domain | `brain_domain/fact_slots.py`, `fact_values.py`, `fact_answers.py`, `data/iso4217-2026-01.txt` |
| 2 application | `engine/packages/brain-factslots`: `ports`, `predicates`, `resolution`, `answers`, `names`, `service` |
| 3 persistence | migration `0012`, `brain_persistence/fact_slot_models.py`, `fact_slots.py`, identity columns on `FactSlotRow` |
| 4 commit integration | `brain_temporal/commit.py` (`CommitAnswerPolicy` hook, G0 reconciliation 1); `engine/apps/api/src/brain_api/routes/facts.py` (policy, extra READ keys, evidence-only source proof, G0 reconciliation 2); `errors.py` (`FactAnswerRejectedApiError`); `deps.py` (`get_predicate_registry`) |
| 5 proof | the tests listed in `test-plan.md`; test composition in `brain_testing/factslots.py` |

Deviations, all non-semantic:

- `seed_identity_slot` lives in `brain_testing/factslots.py` with `seed_subject`/`slot_key`, and tests create identity slots through the real resolver. `fixtures.py` is unchanged.
- `commit_source_keys` is unchanged; `FactAnswerPolicy.source_keys` supplies the answer-derived READ keys, and the route joins both.
- The design examples pin the release references as `f0007-system-predicates/1` and `f0007-fixtures/1`; the code follows them.

Two carry-in repairs outside the six stories are needed so that existing suites keep passing with a new head:

- `scripts/ops/verify_content.py` hashes only the columns present at the database's revision;
- `test_assertion_migration.py` no longer hard-codes head `0011`.

Without the first repair, 0012 would break the backup drill on older revisions. That drill already failed on `main` for 0011. No other scope was added: no route, grant, Casbin row, UI, model call, RLS, or `canonical_fact_version` DDL.

## Acceptance Criteria Review

39 of 39 ACs pass against PostgreSQL, or through the named review item S0006 AC5. See the mapping in `test-plan.md`. Key rules confirmed:

- the fingerprint never decides identity: stored rows are compared, and a forced collision is rejected without a merge;
- explicit null is rejected, and an omitted qualifier contributes nothing;
- members are child slots, so the ADR-0008 exclusion applies per member;
- every rejection writes zero rows;
- a denial is a 404 indistinguishable from not-found and comes before any reason;
- legacy slots stay legacy and their pilot values are unchanged.

## Implementation Risks

- **Answer envelope in JSONB.** The state/value rule is enforced in the service. The database backstop is an F0008 follow-up (ADR-0077 consequence).
- **Restrictions fixed at creation.** A slot's restrictions are fixed from its creating sources; re-derivation is an F0018 follow-up.
- **Per-slot authorization in the name hook.** The hook authorizes each candidate slot with `fact_slot:read`, one durable read decision per slot. That is correct but grows with the number of name facts. No production caller exists until F0017/F0023.
- **Shared authorship.** One agent implemented and tested the feature (`test-plan.md` independence note). G3 review is the independent check.

## Validation Evidence

- `artifacts/test-results/g2-f0007-ci-step.xml`: 148/148, `brain_factslots` 98.25%.
- `artifacts/test-results/g2-engine-full.xml`: 816/816 on an owned database at head.
- `artifacts/test-results/g2-neuron-suite.xml`: 264 passed, 41 CI-equivalent skips.
- `artifacts/coverage/changed-code-summary.json`: 98.9% changed-line coverage.
- `deployability-check.md`: lock, CI, migration, clone and API boot.
- `artifacts/security/`: semgrep 0 findings over 33 files; gitleaks no leaks across 75 changed files; pip-audit 0 vulnerabilities across 35 resolved packages; ZAP API scan 113 pass, 0 warn, 0 fail (unauthenticated reach).
- `artifacts/test-results/g2-prior-hints.txt`: `hint.py` output for every file edited, captured before the edit.

## Post-G3 Delta

The G3 security review found three access-control gaps (SEC-F7-01/02/03), now fixed with tests. Final-code evidence: 819/819 engine tests, 151/151 in the F0007 CI step, 99.0% changed-line coverage, and scans clean (`test-execution-report.md`, `security-review-report.md`).

## Result

PASS for implementation self-review. Independent Code and Security review and the operator approval are still required. This report does not approve or close the feature.
