# Code Review Report — F0002 run 2026-09-27-bb7c8d1d

**Reviewer role:** Code Reviewer (agents/code-reviewer/SKILL.md)
**Date:** 2026-09-28
**Reviewed revision:** feature/F0002-tenancy-kernel, cycle 1 at ade364c/4777949 and cycle 2 at 89f5dd5 (G4 fix-issues)

## Reviewed Files

The canonical changed-file set is artifacts/diffs/changed-files.txt. Every runtime, migration, script, config and test file in it was read:

.github/workflows/ci-gates.yml
config/authx-identity-profile.yaml
engine/apps/api/src/brain_api/config.py
engine/apps/api/src/brain_api/deps.py
engine/apps/api/src/brain_api/errors.py
engine/apps/api/src/brain_api/routes/content.py
engine/apps/api/src/brain_api/routes/facts.py
engine/apps/api/src/brain_api/routes/reviews.py
engine/apps/api/tests/test_content.py
engine/apps/api/tests/test_facts.py
engine/apps/api/tests/test_reviews.py
engine/apps/worker/src/brain_worker/document_delivery.py
engine/migrations/env.py
engine/migrations/versions/0005_tenancy_authx_expand.py
engine/migrations/versions/0006_tenancy_authx_constrain.py
engine/migrations/versions/0007_tenancy_authx_safeguards.py
engine/packages/brain-domain/src/brain_domain/audit.py
engine/packages/brain-domain/src/brain_domain/authx.py
engine/packages/brain-domain/src/brain_domain/tenancy.py
engine/packages/brain-domain/tests/test_authx.py
engine/packages/brain-domain/tests/test_tenancy.py
engine/packages/brain-jobs/src/brain_jobs/queue.py
engine/packages/brain-persistence/src/brain_persistence/authx.py
engine/packages/brain-persistence/src/brain_persistence/grants.py
engine/packages/brain-persistence/src/brain_persistence/identity.py
engine/packages/brain-persistence/src/brain_persistence/models.py
engine/packages/brain-persistence/src/brain_persistence/repositories.py
engine/packages/brain-persistence/src/brain_persistence/tenancy.py
engine/packages/brain-persistence/tests/test_models.py
engine/packages/brain-persistence/tests/test_repositories.py
engine/packages/brain-persistence/tests/test_tenancy_and_grants.py
engine/packages/brain-security/pyproject.toml
engine/packages/brain-security/src/brain_security/audit.py
engine/packages/brain-security/src/brain_security/authorization.py
engine/packages/brain-security/src/brain_security/casbin_adapter.py
engine/packages/brain-security/src/brain_security/delegation.py
engine/packages/brain-security/src/brain_security/evaluation.py
engine/packages/brain-security/src/brain_security/execution.py
engine/packages/brain-security/src/brain_security/identity_profile.py
engine/packages/brain-security/src/brain_security/principals.py
engine/packages/brain-security/src/brain_security/verification.py
engine/packages/brain-security/tests/conftest.py
engine/packages/brain-security/tests/test_authorization.py
engine/packages/brain-security/tests/test_casbin_adapter.py
engine/packages/brain-security/tests/test_delegation.py
engine/packages/brain-security/tests/test_evaluation.py
engine/packages/brain-security/tests/test_execution.py
engine/packages/brain-security/tests/test_identity_profile.py
engine/packages/brain-security/tests/test_principals.py
engine/packages/brain-security/tests/test_verification.py
engine/packages/brain-temporal/src/brain_temporal/commit.py
engine/packages/brain-temporal/tests/conftest.py
engine/packages/brain-temporal/tests/test_commit.py
engine/packages/brain-testing/pyproject.toml
engine/packages/brain-testing/src/brain_testing/__init__.py
engine/packages/brain-testing/src/brain_testing/fixtures.py
engine/packages/brain-testing/src/brain_testing/py.typed
engine/pyproject.toml
engine/ruff.toml
engine/tests/contract/test_authx_kernel.py
engine/tests/integration/conftest.py
engine/tests/integration/test_authx_migration.py
engine/tests/integration/test_bitemporal_commit.py
engine/tests/integration/test_commit_concurrency.py
engine/tests/integration/test_outbox_replay.py
engine/tests/security/conftest.py
engine/tests/security/test_authx_audit.py
engine/tests/security/test_authx_consumers.py
engine/tests/security/test_authx_delegation.py
engine/tests/security/test_authx_principals.py
engine/tests/security/test_authx_restrictions.py
engine/tests/security/test_authx_scope.py
engine/tests/security/test_credential_verification.py
neuron/packages/brain-ingestion/src/brain_ingestion/worker_cli.py
neuron/pyproject.toml
neuron/tests/integration/test_document_delivery.py
neuron/tests/integration/test_document_process_recovery.py
neuron/tests/integration/test_worker_cli_enqueue.py
scripts/dev/provision_delegation.py
scripts/dev/reconcile_authx.py
scripts/dev/revoke_membership.py

## Validation Artifacts

artifacts/test-results/g2-engine-pytest.txt
artifacts/test-results/g3-engine-pytest.txt
artifacts/test-results/g2-engine-static.txt
artifacts/test-results/g2-neuron-pytest.txt
artifacts/coverage/g2-engine-coverage.json
artifacts/coverage/g2-package-coverage-gates.txt
artifacts/security/g2-semgrep-report.json
artifacts/test-results/g3r-engine-pytest.txt
artifacts/test-results/g3r-engine-static.txt
artifacts/test-results/g3r-neuron-pytest.txt
artifacts/coverage/g3r-engine-coverage.json
artifacts/coverage/g3r-package-coverage-gates.txt
artifacts/security/g3r-semgrep-report.json

## Severity-Ranked Findings

No critical or high findings.

Review-cycle findings fixed in this pass (re-verified: 279 passed; ruff, format, and mypy clean — artifacts/test-results/g3-engine-pytest.txt):

| Severity | Finding | Resolution |
|---|---|---|
| low | The stale-version path that re-opens a review task (and so provisions its security metadata via `inherit_resource_access`) had no committed test | Added test_authx_restrictions.py::test_stale_review_reopens_a_task_that_inherits_its_restrictions |
| low | "Denied is indistinguishable from nonexistent" was asserted only on status and code | Added test_denied_and_nonexistent_are_byte_for_byte_indistinguishable (whole-body equality) |
| low | The rejected-credential process-log line and its durable authentication event carried unrelated trace IDs | `deps._reject` passes the event's server trace to the log as `event_trace_id`; the invalid-credential test asserts the correlation |

## Non-Blocking Recommendations With Owner/Follow-up

None open after review cycle 2. The cycle-1 recommendations were fixed at the user's G4 selection:

| Cycle-1 item | Cycle-2 resolution (89f5dd5) |
|---|---|
| medium: lock/load orchestration duplicated in the async facade and the sync worker | One `brain_security.execution.decide` over a sync `AuthorityReader`; the facade reaches it through `AuthorityStore.run_sync`, and the worker calls it directly. Lock order and delegation binding now live in one place |
| low: unused `DelegationService` protocol | Removed |
| low: synthetic fixtures inside the runtime `brain_persistence` package | Moved to the dev-only `brain-testing` workspace package (engine and neuron dev groups; added to CI mypy roots) |
| low: worker allowed-then-refused on a lease/metadata KB mismatch | The lease KB is a request-scope filter, so a mismatch is a recorded `scope_denied` (test_authx_delegation.py::test_worker_lease_scope_must_match_the_artifact_metadata) |

The user's scope amendment added BLUEPRINT §4.11 migration 0007. It was reviewed: the trigger function quotes column names with `format('%I')` and receives trigger arguments only from migration constants; a NULL owner may be filled once (backfill), and any later rewrite raises `check_violation`; append-only guards cover row UPDATE/DELETE; assertion self-references are DEFERRABLE INITIALLY IMMEDIATE, so normal writes are unchanged. The proof is tests/integration/test_authx_migration.py::test_safeguards_make_ownership_immutable_audit_append_only_and_restore_deferrable.

## Vertical-Slice Completeness

| Layer | Status |
|---|---|
| Backend | Complete: kernel, persistence, migrations, and every protected route and service consumer |
| Frontend | Not in scope (PRD: no UI) |
| AI | Only the trusted-submission CLI change; no model, prompt, or inference change |
| Tests | Complete: unit, contract, PostgreSQL integration/migration, EX-AUTHX security suites through consumers, worker regression |
| Deployability | Independently deployable: additive expand, reviewed reconcile, then constrain; restore drill and round trip recorded |

## AC / Test Adequacy

All 41 ACs map to executed tests (test-plan.md). Each denial is tested independently while the other conditions allow. Guards were verified by breaking what they guard: exact constraint names in the migration proof, captured SQL on rejected credentials, the file-read counter on denials, failure injection on audit and grant reads, and a manifest role removed to prove the G2 validator enforces it. No test-without-AC of concern; the latency test measures and claims no SLO.

## Architecture Compliance

- Clean layering holds: domain (no I/O), then security (pure evaluator, ports), then persistence adapters, then API/worker composition. No new cross-package dependency beyond pyyaml (brain-security) and jsonschema (engine dev group).
- The lock order matches the plan: pointer, then authority by principal ID, then delegation, then resource access by key, then operation rows. Grant, status, and restriction changes take FOR UPDATE on the rows evaluation reads FOR SHARE.
- `CanonicalCommitService` no longer authorizes internally. It runs inside the facade's unit of work, re-checks the authorized scope against its slot lock, and preserves temporal and outbox semantics.
- The legacy snapshot authorizer is removed rather than left as a bypass (R5). `PolicyEvaluator.permits` takes both scopes (a recorded deviation that strengthens the unchanged Casbin condition).
- SOLUTION-PATTERNS §1 still names `AuthorizationService.authorize` as the enforcement point. This is stale; routed to the Architect for G7.

## Coverage Verification

coverage-report.md (cycle 2) matches artifacts/coverage/g3r-engine-coverage.json. Changed-kernel lines total 2366/2516 = 94.04%, recomputed from the JSON (the fixtures moved out of the measured runtime set). Per-package gate output matches artifacts/coverage/g3r-package-coverage-gates.txt.

## Recommendation

Approve. Cycle 2 closed every open code-review recommendation. Re-verified: engine 282 passed; neuron 75 passed (3 opt-in live-inference skips); ruff, format, and mypy clean across the 9 source roots.

Result: APPROVED
