# Code Review Report — F0007-factslot-model run 2026-11-09-b94cfa12

- Role: Code Reviewer
- Reviewer: Claude (Opus 5.5) / Code Reviewer
- Date: 2026-11-09
- Independence: the reviewer is the same agent session that implemented the feature. This review re-read every changed file against the story ACs, ADR-0077 and SOLUTION-PATTERNS, independent of the self-review. It is not an independent human review; the operator decides at G4 whether that is sufficient.

## Reviewed Files

The production code is 21 files: 11 new and 10 modified.

- **New domain modules:** `brain_domain/fact_slots.py`, `fact_values.py`, `fact_answers.py`, `data/iso4217-2026-01.txt`.
- **New package:** `brain-factslots` (`ports`, `predicates`, `resolution`, `answers`, `names`, `service`, `__init__`).
- **New persistence and migration:** `brain_persistence/fact_slots.py`, `fact_slot_models.py`; migration `0012_f0007_factslot_identity.py`.
- **Modified:** `brain_persistence/models.py`, `brain_temporal/commit.py`, `engine/apps/api/src/brain_api/routes/facts.py`, `errors.py`, `deps.py`, `scripts/ops/verify_content.py`, and five `pyproject.toml`/lock pairs.

The tests are 13 files, with 2 fixture files, plus `.github/workflows/ci-gates.yml`. The full list is `artifacts/diffs/changed-files.txt`.

## Validation Artifacts

- `artifacts/test-results/g3-engine-full.xml`: 819/819 on an owned database at head, after the G3 fixes.
- `artifacts/test-results/g3-f0007-ci-step.xml`: 151/151, `brain_factslots` 98.6%.
- `artifacts/test-results/command-output/g3-static.txt`: ruff, ruff format and mypy over 98 files, all clean.
- `artifacts/coverage/changed-code-summary.json`: 99.0% changed-line coverage (1211/1223).

## Severity-Ranked Findings

| ID | Severity | Finding | Disposition |
|---|---|---|---|
| CR-F7-01 | Medium | Test adequacy: the S0003 AC6 suite proved T-08 non-disclosure only on the commit path. `GET /facts/{id}` and `AuthorizedFactSlots.read_answer` returned an identity-v1 envelope, absence scope included, to any slot reader. This is the same defect as SEC-F7-02. | **Fixed in this cycle.** `FactAnswerReader.scope_read_keys` drives a READ check of the scope artifact before the slot read in both paths. New test `test_s0003_ac6_reads_never_expose_a_scope_the_reader_cannot_read`. |
| CR-F7-02 | Low | Name-member resolution did not READ-authorize the evidence artifacts, and the member's restrictions omitted them. This is the same defect as SEC-F7-01. | **Fixed in this cycle.** `FactSlotResolver.evidence_source_keys` feeds `additional_reads`, and the evidence keys join the member's derived restrictions. New test `test_g3_name_member_evidence_is_read_authorized_before_any_reason`. |

Open findings after the fixes: Critical 0, High 0, Medium 0, Low 0.

Observations that need no change:

- **Defensive branch.** `FactAnswerPolicy.canonical_value` raises `ANSWER_CONTRACT_UNSUPPORTED` on a slot-owner mismatch. The commit lock already prevents that path (it is marked `pragma: no cover`).
- **Deploy order.** New code needs migration 0012 before it runs, because the ORM maps the new columns. The rollout order is already "apply 0012, then deploy" (assembly plan; `deployability-check.md`).
- **Name hook cost.** `AuthorizedFactSlots.current_names` records one durable READ decision per candidate name slot. That is correct and bounded by an entity's name facts. It is a handoff note for F0017/F0023, whose caller will choose a batch-read facade if needed, not an F0007 change.

## Non-Blocking Recommendations With Owner/Follow-up

None. The name-hook cost note above is design input for F0017/F0023, the feature that will add the caller. It asks no change of F0007.

## Vertical-Slice Completeness

- **Backend:** complete. Domain, application package, persistence, migration, commit hook and API error mapping are all in place.
- **Frontend and AI:** not in scope (manifest `frontend_in_scope=false`; no neuron, model or prompt change).
- **Tests:** unit, contract, PostgreSQL integration, HTTP and migration suites.
- **Deployable:** yes. The feature is additive, with CI wiring and a proven up/down/up cycle.

## AC / Test Adequacy

All 39 ACs map to executed tests (`test-plan.md`), and S0006 AC5 is checked in the Security review below.

- Every rejection test asserts zero rows across `fact_slot`, `fact_slot_qualifier`, `canonical_fact_version` and `canonical_commit`.
- Expectations are literal: canonical strings, reason codes and HTTP codes. None is derived from the code under test.
- One weakness was found and closed during review: the read-path T-08 gap (CR-F7-01).

## Architecture Compliance

- **Clean layering.** Pure domain has no I/O. `brain-factslots` depends only on `brain-domain` and `brain-security`. `brain-temporal` gains a protocol, not a dependency. Persistence implements the port.
- **Owned semantics.** No DDL on `canonical_fact_version` (F0008). No new grant, route or Casbin row. ProblemDetails with the lowercase `code` and no detail text.
- **Assembly plan.** It matches the G0 plan and its six recorded reconciliations. The deviations are listed in `g2-self-review.md` and are all non-semantic.

## Coverage Verification

Changed-line coverage is 99.0%, well above the contract floor. The `brain_factslots` CI gate is 98.6% with PostgreSQL and 87% unit-only; both exceed the floor. The uncovered lines are defensive branches, listed in `coverage-report.md`.

## Result

APPROVED
