# G2 Self-Review — F0002 run 2026-09-27-bb7c8d1d

**Roles:** Backend Developer, Quality Engineer, DevOps, AI Engineer (worker CLI trusted-submission change only), Architect (plan conformance)
**Date:** 2026-09-27

## Scope Review

Every file in the assembly plan's "New files by layer" table was delivered. Deviations are the reconciled deltas R1–R5 from g0-assembly-plan-validation.md:

- Domain: `brain_domain/tenancy.py`, `brain_domain/authx.py` (the v1 carriers, field-for-field with the schema), and an `audit.py` extension (nullable v1 fields).
- Security: `evaluation.py` (the only place allow/deny rules live), `execution.py` (the transaction-aware facade), `delegation.py`, `identity_profile.py`, hardened `verification.py`, alias-based `principals.py`, and policy-release identity in `casbin_adapter.py`. The legacy `authorization.py` (snapshot `AuthorizationService`/`ResourceRef`) is removed (R5).
- Persistence: registries and substrate models, `authx.py` (shared sync queries; the async store runs them through `run_sync`), `tenancy.py`, `identity.py`, `grants.py` (planned under `authx.py`; split for size), and `fixtures.py` (synthetic builders over the real services).
- Migrations 0005 (expand) and 0006 (constrain). `scripts/dev/reconcile_authx.py`, `provision_delegation.py`, and `revoke_membership.py` (now authority-locked and audited). `config/authx-identity-profile.yaml`.
- Consumers: content, fact, and review routes and the commit service all run through the facade. The worker `DocumentJobAuthorization` keeps its constructor and `for_job` contract and now uses the shared evaluator through `SyncAuthorityStore`. `brain_jobs` IDs are native uuid on PostgreSQL (R4). The neuron `worker_cli --enqueue` provisions declared artifact restrictions (R3; no model, prompt, or inference change).
- Not delivered, as planned: no UI, no new route, no new policy row or role, no MCP/A2A transport, no automatic review-to-canonical promotion.
- Signature deviation: `PolicyEvaluator.permits` takes both the grant scope and the resource scope, so the unchanged Casbin condition compares two independently sourced KB IDs instead of one value with itself. This is recorded for the Architect and code review.

Architect confirmation: the as-built structure matches the Step 0 plan and its lock order (policy pointer, then authority rows by principal ID, then delegation, then resource-access rows, then operation rows). No shared-semantics change was made outside the approved schema, ADRs, and plan. The schema and ADRs are unchanged.

## Acceptance Criteria Review

All 41 story ACs across S0001–S0006 map to executed tests (test-plan.md, "Acceptance → test map"). All 18 EX-AUTHX cases record observed outcomes that match the independent expectations (test-execution-report.md). The no-mixed-slice, expiry, recheck-before-effect, batch-atomicity, concurrent-revoke, and audit-failure cases are included. Deferred section 121.2 categories name owning features and are not counted as passed.

## Implementation Risks

- The dev database is shared with the security suites, which truncate F0002 registries and the policy pointer (a pre-existing F0001 pattern). Recorded as a DevOps low recommendation.
- `SqlAlchemyAuthorityStore` reuses the sync query layer via `AsyncSession.run_sync` (greenlet bridge). This is proven on asyncpg under concurrency (concurrent first sight, revoke vs commit), but it is a pattern new to this codebase and the Code Reviewer should assess it.
- The evaluator reports only the first failing reason when several slices fail; the audit therefore records one representative denial reason, not every slice's reason. This is intentional (no disclosure; minimal audit) and noted for Security.
- Authentication-event and decision audit rows in `audit_event.occurred_at` keep the F0001 `timestamp without time zone` column (UTC instant stored naive) rather than rewriting the legacy column.
- BLUEPRINT §4.11 follow-up safeguards (ownership-immutability triggers, link-table triggers, deferred self-references) are not implemented. §4.11 defers them to this run as follow-ups outside the approved plan, and they are carried to README.md for the PM decision.

## Validation Evidence

artifacts/test-results/g2-engine-pytest.txt
artifacts/test-results/g2-engine-static.txt
artifacts/test-results/g2-neuron-pytest.txt
artifacts/coverage/g2-package-coverage-gates.txt
artifacts/test-results/g2-devops-restore-drill.txt
artifacts/security/g2-semgrep-report.json

Per role:
- **Backend:** ruff, format, and mypy clean across the 8 CI source roots. Unit, integration, contract, and security suites pass: 277 in engine.
- **QE:** test plan and execution ledger complete; changed-kernel coverage 93.74%; every per-package CI gate ≥ 80%.
- **DevOps:** migrations applied, round-tripped, and restore-drilled; operator activation runbook executed; compose and pins verified (deployability-check.md).
- **AI Engineer:** neuron ruff, format, mypy, and 75 tests pass. The worker CLI change is covered by test_worker_cli_enqueue.py; no model or inference path changed.

The only in-run SAST findings (dynamic-identifier `text()` in the reconcile script and the 0005 preflight) were hardened with an identifier allow-list before G2. The re-scan shows only the pre-existing `seed_principals.py` WARNING.

Result: PASS
