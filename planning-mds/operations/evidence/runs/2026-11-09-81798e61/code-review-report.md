# Code Review Report — F0007-factslot-model run 2026-11-09-81798e61

Reviewer: Codex / independent Code Reviewer (`/root/remediation_code_review`). Date: 2026-11-10.

The reviewer did not implement the changes. Scope is the current remediation implementation relative to `fa8fc1d`, plus the new migration and regression files. The seven original findings are in audit run `2026-11-09-8b8456df`; this report assesses their implementation repairs, not an automatic acceptance of the original completion claim.

## Reviewed Files

Canonical scope inventory: `artifacts/diffs/changed-files.txt`, with inherited original final-diff inventory `artifacts/diffs/original-final-changed-files.txt`.

- `brain_domain modules: {fact_values,fact_answers,fact_slots}.py` and domain numeric tests.
- `brain_factslots modules: {answers,service}.py`; existing ports/normalization contracts and application tests.
- `engine/packages/brain-security/src/brain_security/execution.py`; authority-store locking contract; new `tests/test_payload_reads.py` and existing execution tests.
- `engine/apps/api/src/brain_api/routes/facts.py`; new/existing FactSlot answer, name, ownership, migration and protected-read test sources.
- New `engine/migrations/versions/0013_f0007_identity_guard.py` and `engine/tests/integration/test_factslot_identity_guard_migration.py`; immutable `0012` constraint for comparison.
- CI F0007 test step, shared numeric schema descriptions, API rejection documentation, active feature stories, amended assembly plan and ADR-0077.

## Validation Artifacts

- `artifacts/test-results/remediation.xml`: directly parsed raw JUnit, **319 tests; 0 failures, 0 errors, 0 skipped**, from the application validation container.
- `artifacts/test-results/engine-full-final.xml` and `artifacts/engine-full-final.txt`: independently checked final full application-container suite, **868 tests; 0 failures, 0 errors, 0 skipped**. The owned database was removed after execution.
- `artifacts/coverage/remediation.json`: directly parsed raw coverage, 2,176 covered of 2,263 executable statements (**96.1555%**) over the selected domain/factslots/security scope. `artifacts/combined-postgres.txt` carries the per-file table and execution command.
- `artifacts/code-review-quality.txt`: framework quality scan on application source passes (no TODO/FIXME, overlong lines or oversized files).
- `artifacts/code-review-final-source-snapshot.txt`: clean Git whitespace check and inspected regression/runtime context.
- `artifacts/code-review-risk.txt`: resolver risk score 3, routine; owner-concentration guidance is retained for integration review. No new high-band reviewer requirement results from this score.
- `artifacts/code-review-read-uow.txt`, `code-review-decimal-member-tests.txt`, `code-review-new-migration-tests.txt` and `code-review-final-lines.txt`: exact inspected source/test snapshots.
- `artifacts/static-final.txt`: final Ruff check and formatting pass across189 files; mypy succeeds across72 source files.
- `artifacts/symbols-decisions-remediation.txt`: symbol and WHY-decision regeneration/checks pass. The authored F0007 binding includes0013 and the new migration/protected-read tests.
- `artifacts/code-review-final-validation-evidence.txt` and `artifacts/code-review-static-kg-refresh.txt`: this reviewer's final raw-output verification.

The first full-engine run's three backup/restore failures report `backup.sh: docker: command not found` in the validation image. The runtime tool dependency was corrected without an implementation change; the same full suite was rerun and all868 tests passed. Initial failures remain in the audit trail rather than being relabeled as a successful execution.

## Severity-Ranked Findings

No new implementation findings. Open Critical: 0. Open High: 0. Open Medium: 0. Open Low: 0.

| Original finding | Implementation assessment |
|---|---|
| FR-C1 member identity | Repaired: `FactAnswerPolicy.canonical_value` computes the canonical answer member key under the pinned contract and compares it with the immutable stored key before returning the accepted envelope. Existing evidence/owner validation retains precedence. Entity, production name and scoped-identifier positives/negatives are present; the old incorrect success assertion is corrected. |
| FR-H1 canonical numeric reload | Repaired: input and complete canonical output share 64 characters, including sign and decimal point. Boundary tests cover both exponent signs, money and decimal, typed reload and HTTP persistence. |
| FR-H2 SQL NULL identity guard | Repaired: new0013 requires the complete legacy-or-v1 expression to be TRUE, explicitly constrains mandatory fields, and leaves0012 unchanged. Preflight holds ACCESS EXCLUSIVE through scan/replacement; occupied malformed rows cause transactional refusal with count/slot IDs only. Downgrade restores the old guard without modifying data. |
| FR-M1 current-authority read race | Repaired: `AuthorizationExecution.read` loads once privately, derives dependencies from that exact payload, evaluates them under the same authority unit of work, rechecks, audits all decisions and commits once before returning. Internal/HTTP callers use that callback. |
| FR-M2 numeric allocation bound | Repaired: digits/exponent/sign determine canonical length before zero-padding allocation. The isolated capped-child regression expects named rejection for either extreme exponent sign. |
| FR-M3 final source inventory | The new manifest has a distinct original final-diff artifact, retaining both Neuron test adaptations without pretending they are new AI behavior changes. Final reconciliation is a lifecycle artifact, separate from this implementation verdict. |
| FR-M4 stale feature entries | The feature has been reopened to its active path and entry status now states remediation in progress. Completion/archive transitions remain PM-owned. |

## Non-Blocking Recommendations With Owner/Follow-up

None. Existing downstream temporal close, envelope database enforcement, RLS/restriction re-derivation, predicate registration and display precedence remain explicit feature handoffs; no new requirement was invented here.

## Vertical-Slice Completeness

The bounded repairs connect domain validation through the existing commit/read API, persistent migration controls and actual PostgreSQL negative tests. No new endpoint, grant, producer or UI is introduced. The new CI step includes both the identity-guard migration and protected-read suites. The read API extension is optional for existing consumers and preserves their current behavior.

## AC / Test Adequacy

- S0002 AC3 and name-member semantics: member/entity/name/identifier mismatches produce `member_value_mismatch`; API tests assert no canonical writes and preserve authorization-denial precedence. Canonical-equivalent spellings and normalized identifiers remain accepted.
- S0003 AC6/T-08: unit tests cover denied primary, denied dependency, exact payload, discovery failure, expiry and audit failure. Real PostgreSQL concurrency verifies a supported grant revocation cannot commit while the selected slot/scope read retains its authority lock; a subsequent read is denied. The HTTP test deliberately makes a separate prequery see different scope metadata and checks the actual selected version is the authority source.
- S0004 exact values: four complete 64-character canonical boundaries round-trip for both money and decimal; expanded65-character cases reject without writes, as do positive/negative extreme exponents. Both schema descriptions and the runtime enforce the same total canonical limit at the semantic layer.
- S0006/persistent identity: new0013 tests directly exercise every nullable mandatory field, partial legacy rows, absent member/object shape, uniqueness, valid legacy/SINGLE/MULTI/MEMBER/RELATIONSHIP preservation, up/down/up byte equality, exact restoration of0012 semantics, and refusal that preserves the old revision/constraint/data.
- S0001 and remaining original behavior are represented in the combined319-test run, including existing resolver concurrency/ownership/legacy examples. The review does not substitute a new line-coverage percentage for semantic invariants.

The regression tests assert externally meaningful outcomes rather than mirroring implementation calculations. The concurrency test uses events and database lock timeout, not timing sleeps. IDs are synthetic and each PostgreSQL test owns its database.

## Architecture Compliance

Domain logic remains pure. The answer policy reuses the domain `member_key` function rather than duplicating canonical encoding. `brain_security` accepts a typed callback without depending on FactSlot or persistence types. The API supplies exact version-derived scope metadata and the application service supplies the internal typed answer scope. The migration is a separate Alembic revision, uses transactional DDL and never fabricates or repairs immutable evidence.

Non-obvious changes have rationale comments. No hidden TODO/debug path, swallowed error or new outward domain dependency was found. Denial/error responses continue through the existing ProblemDetails and non-disclosure mapping. The resource-length precheck bounds allocation work; the remaining per-name-slot read cost was an existing disclosed caller handoff, not introduced by this repair.

KG source bindings now include the new0013/test paths and the protected-read regression. Symbol/decision regeneration and validation pass, including the changed helper definitions. Warnings retained in the raw output concern pre-existing F0006 assertion-symbol references and do not establish a new F0007 regression. Tracker/archive closeout remains a separate PM lifecycle output.

## Coverage Verification

Verified the raw319-test JUnit, final868-test JUnit and selected-scope coverage counts directly, as stated above. Final full-suite coverage XML/JSON exists under `artifacts/coverage/engine-full-final.*`. The coordinator is calculating the final changed-line measure; this report retains the independently verified96.1555% selected-scope measure and does not substitute it for that distinct calculation. The initial865-pass/3-environment-failure execution is retained separately from the fully passing rerun.

## Result

APPROVED

This is the Code Reviewer implementation verdict. It does not create operator approval, signoff, candidate validation, deployment, archive or completion approval on behalf of their owners.
