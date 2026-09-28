# Code Review Report — F0002 run 2026-09-27-bb7c8d1d

**Reviewer role:** Code Reviewer (agents/code-reviewer/SKILL.md)
**Date:** 2026-09-28
**Reviewed revision:** feature/F0002-tenancy-kernel at ade364c, plus the review-cycle changes listed below

## Reviewed Files

The canonical changed-file set is artifacts/diffs/changed-files.txt. Every runtime and test file in it was read. Focus areas:

- engine/packages/brain-security/src/brain_security/{evaluation,execution,delegation,identity_profile,verification,principals,casbin_adapter,audit}.py
- engine/packages/brain-domain/src/brain_domain/{authx,tenancy,audit}.py
- engine/packages/brain-persistence/src/brain_persistence/{authx,tenancy,identity,grants,fixtures,repositories,models}.py
- engine/migrations/versions/0005_tenancy_authx_expand.py, 0006_tenancy_authx_constrain.py, engine/migrations/env.py
- engine/apps/api/src/brain_api/{deps,errors,config}.py and routes/{content,facts,reviews}.py
- engine/packages/brain-temporal/src/brain_temporal/commit.py, engine/packages/brain-jobs/src/brain_jobs/queue.py
- engine/apps/worker/src/brain_worker/document_delivery.py, neuron/packages/brain-ingestion/src/brain_ingestion/worker_cli.py
- scripts/dev/{reconcile_authx,provision_delegation,revoke_membership}.py, config/authx-identity-profile.yaml
- every new or changed test module (contract, integration/migration, six EX-AUTHX security suites, package units, neuron worker tests)

## Validation Artifacts

artifacts/test-results/g2-engine-pytest.txt
artifacts/test-results/g3-engine-pytest.txt
artifacts/test-results/g2-engine-static.txt
artifacts/test-results/g2-neuron-pytest.txt
artifacts/coverage/g2-engine-coverage.json
artifacts/coverage/g2-package-coverage-gates.txt
artifacts/security/g2-semgrep-report.json

## Severity-Ranked Findings

No critical or high findings.

Review-cycle findings fixed in this pass (re-verified: 279 passed; ruff, format, and mypy clean — artifacts/test-results/g3-engine-pytest.txt):

| Severity | Finding | Resolution |
|---|---|---|
| low | The stale-version path that re-opens a review task (and so provisions its security metadata via `inherit_resource_access`) had no committed test | Added test_authx_restrictions.py::test_stale_review_reopens_a_task_that_inherits_its_restrictions |
| low | "Denied is indistinguishable from nonexistent" was asserted only on status and code | Added test_denied_and_nonexistent_are_byte_for_byte_indistinguishable (whole-body equality) |
| low | The rejected-credential process-log line and its durable authentication event carried unrelated trace IDs | `deps._reject` passes the event's server trace to the log as `event_trace_id`; the invalid-credential test asserts the correlation |

## Non-Blocking Recommendations With Owner/Follow-up

- [medium] Lock/load orchestration is written twice, once in `AuthorizationExecution._decide` (async) and once in `DocumentJobAuthorization.decide` (sync). All allow/deny rules are shared through `evaluate`, as ADR-0062 requires, but a future change to lock order or delegation binding must be made in both places. Extract a shared orchestration step parameterized by a sync store when the next consumer needs it. — owner: Backend Developer; follow-up: deferred-no-followup
- [low] `brain_security.delegation.DelegationService` is an unused protocol kept to mirror the assembly plan's port list; the implemented operations are `brain_persistence.grants.issue_delegation`/`revoke_delegation`. Remove it or implement it when a runtime delegation service is introduced (F0047). — owner: Backend Developer; follow-up: deferred-no-followup
- [low] `brain_persistence.fixtures` (synthetic builders) ships inside the runtime package so the engine, neuron, and scripts can share it. It only composes the trusted services and is unreachable from the API, but it would sit better in a test-support package. — owner: Backend Developer; follow-up: deferred-no-followup
- [low] When the worker's decision allows the artifact but its hydrated scope differs from the lease's tenant/KB, the step is refused after the decision was recorded as `allowed`/`attempted`. The audit is not wrong (attempted, never succeeded), but a distinct reason would be clearer. — owner: Backend Developer; follow-up: deferred-no-followup

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

coverage-report.md matches artifacts/coverage/g2-engine-coverage.json. Changed-kernel lines total 2457/2621 = 93.74%, recomputed from the JSON. Per-package gate output matches artifacts/coverage/g2-package-coverage-gates.txt.

## Recommendation

Approve. The remaining items are maintainability recommendations with owners and do not block.

Result: APPROVED WITH RECOMMENDATIONS
