# Security Review Report — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Scope

- Feature ID: F0003
- Run ID: `2026-10-03-57d14a51`
- Date: 2026-10-04
- Reviewer: Security Reviewer (Codex)
- Product root: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (source: explicit operator value)
- Reviewed change: `main` (`430352c1c6a0acb06169884cd259f493cfd33936`) to feature head (`1e9db3381d63c8634b52d8e172ccd36a1e3cdf73`)
- Environment: local disposable PostgreSQL 18 test database and checked-in source; no production data or production service was used.

In scope: the F0003 persistence boundary and its tenant/knowledge-base ownership, bitemporal constraints, migration/backfill acceptance, transactional audit behavior, test-data handling, and the current PR diff. I reviewed the F0003 assembly plan and test plan, the changed test, the existing F0002 ownership migrations/reconciliation path used by F0003's acceptance tests, and the PostgreSQL audit tests.

Out of scope: recertifying every F0002 API authorization path, external identity-provider configuration, production network/TLS posture, and broad DAST. F0003 adds no runtime authorization, endpoint, dependency, deployment, or migration change in this PR. The sole engine code diff is a context-manager refactor in `engine/tests/integration/test_persistence_contract.py`; its persistence assertions are unchanged.

Assumptions: the run's PostgreSQL test output is accurate and the named database was disposable. The run artifact records a fresh schema upgrade through revision `0007` after installing database-local extensions, followed by 12 passed, 0 failed, and 0 skipped tests. Those tests use synthetic principals, UUIDs, fact values, and temporary databases.

## Reviewed Surfaces

- Changed code: `engine/tests/integration/test_persistence_contract.py`.
- Relevant F0003 scope and evidence: `planning-mds/features/F0003-postgresql-persistence/feature-assembly-plan.md`, `planning-mds/features/F0003-postgresql-persistence/STATUS.md`, `planning-mds/operations/evidence/runs/2026-10-03-57d14a51/test-plan.md`, `test-execution-report.md`, and `artifacts/test-results/f0003-postgres-run.md`.
- Ownership and migration controls exercised by the evidence: `engine/migrations/versions/0005_tenancy_authx_expand.py`, `0006_tenancy_authx_constrain.py`, `0007_tenancy_authx_safeguards.py`, and `scripts/dev/reconcile_authx.py`.
- Audit and ownership test evidence: `engine/tests/integration/test_authx_migration.py`, `engine/tests/security/test_authx_audit.py`, and `artifacts/test-results/f0003-postgres.xml`.
- Secret/config exposure: no secret, auth configuration, deployment configuration, dependency manifest, API, or production source path changed in the reviewed diff.

## Threat Boundary

| Asset / sensitivity | Actor | Entry point and trust boundary | Operation / existing control |
|---|---|---|---|
| Tenant, workspace, knowledge-base ownership and membership restrictions / restricted | Migration operator | Explicit reconciliation mapping and Alembic process into PostgreSQL | Mapping digest and approval reference gate application; ambiguous or mixed-owner rows fail closed; composite foreign keys enforce parent ownership. |
| Principal, authorization-decision, and audit records / restricted | User or service principal | Existing authenticated API into authorization service and PostgreSQL | Current-grant and resource checks precede protected operations; audit persistence is required before successful response; audit rows reject update/delete. These runtime paths are inherited from F0002 and were not changed here. |
| Canonical facts, evidence references, and outbox events / confidential | Authorized application service | Repository/unit-of-work transaction into PostgreSQL | Owner keys and parent references are constrained in PostgreSQL; fact, audit, and outbox writes are transactional; bitemporal exclusion and idempotency tests exercise database behavior. |
| Migration/test fixtures / internal synthetic data | CI or local test runner | Test harness into a disposable PostgreSQL database | Fixtures generate UUIDs and test-only identities/values; migration tests create and drop named temporary databases. No production records or source bytes are used. |

No new trust boundary or entry point is introduced by this PR.

### STRIDE assessment

| Threat | Preconditions and impact | Existing control / evidence | Remaining gap |
|---|---|---|---|
| Spoofing | A caller presents a forged or invalid identity and attempts a protected operation. | No authentication code changed. Existing F0002 tests cover allowed/denied consumer calls and ensure audit records do not contain bearer tokens; F0003 does not add an identity path. | Full issuer, audience, token expiry, and production identity-provider posture are outside this review. |
| Tampering | A caller or migration process attempts to attach a child row to another tenant/KB, rewrite ownership, or alter audit history. | Composite ownership constraints reject mismatched parent keys; revision `0007` guards immutable owner columns and append-only audit rows. Migration tests exercise cross-owner rejection and update/delete rejection (`test_authx_migration.py`; `f0003-postgres.xml`). | A database superuser can bypass trigger-level protections; privileged DBA access is an operational trust boundary, not changed by this PR. |
| Repudiation | A protected action succeeds without durable audit evidence, or an operator rewrites prior audit. | Existing audit tests inject audit-write failure and require sanitized failure with no mutation; migration tests reject audit update/delete. Evidence: `engine/tests/security/test_authx_audit.py` and `test_authx_migration.py`. | Central audit export, alerting, and DBA-level tamper detection are not changed or assessed here. |
| Information disclosure | Tokens, source bytes, or fact payloads escape through audit or migration output. | Audit tests assert serialized decisions omit tokens, a PDF marker, and the proposal amount. Reconciliation dry-run output is asserted not to disclose the synthetic principal name and is documented as counts/IDs only. | Broader production logging and data-at-rest/in-transit configuration need their project baseline documents; no such configuration changed here. |
| Denial of service | A malformed migration/backfill or repeated protected operation causes uncontrolled work or partial schema/data updates. | Invalid UUID and ambiguous mixed-KB cases stop before constraints/data are partially applied; database migration runs only in a disposable test DB for this evidence. | Runtime rate limiting and production migration duration/restore testing are not in this PR's change set. |
| Elevation of privilege | A tenant/KB association is mistaken for an access grant, or a row can cross an ownership boundary. | ADR-0061 states identity association does not grant access; F0003 plan preserves F0002 policy; the DB rejects cross-owner links and incomplete membership slices. No role/policy code changed. | Complete authorization behavior across future search/graph/vector surfaces remains owned by their features. |

## Auth / Authz

No permission, role, grant, credential, policy evaluator, or endpoint code changed. The F0003 plan explicitly preserves the F0002 authorization contract. PostgreSQL evidence exercises owner-mismatch rejection and the existing audit decision behavior; it does not constitute a fresh review of every F0002 consumer.

## Validation

The only code diff refactors nested `async with` blocks in the PostgreSQL exclusion test into a combined context manager. The transaction boundary and test assertions remain the same. New operator-controlled values in the migration test path are bound parameters; the relevant dynamic SQL identifiers in migration code are drawn from fixed module constants. The synthetic test fixtures do not read production records or source bytes.

## Audit / Logging

No audit implementation changed. The evidence reports passing tests for allowed/denied outcomes, audit persistence failure, append-only audit rows, successful reviewed reconciliation audit, and no partial business mutation on audit failure. Tests explicitly check that bearer tokens, a source-file marker, and a fact amount are absent from decision serialization.

## Secrets / Config

No secret, key, database credential, auth configuration, or deployment configuration was introduced or modified by this diff. Test tokens/keys are generated in test code, and the PostgreSQL test run uses synthetic identities on a disposable local database. Production secret storage, encryption settings, and credential rotation were not verified by this test-only change review.

## Scan Disposition

The run manifest records `security_sensitive_scope=false`; its changed paths are the F0003 status tracker and a PostgreSQL integration test. Therefore the contract's four security scan classes were not required for this run. No waiver is claimed for a required scan.

| Class | Ran | Result / Finding summary | Artifact or waiver reason |
|-------|-----|--------------------------|---------------------------|
| dependency | No | No dependency manifest or runtime package changed. | Not required: `security_sensitive_scope=false`; see manifest and diff. |
| secrets | No | No secret/config path changed; manually reviewed the complete change diff. | Not required: `security_sensitive_scope=false`; see manifest and diff. |
| sast | No | No runtime source or policy implementation changed; test-only context-manager refactor. | Not required: `security_sensitive_scope=false`; see manifest and diff. |
| dast | No | No endpoint, service configuration, or deployable application surface changed. | Not required: `security_sensitive_scope=false`; see manifest and diff. |

Separate from those conditional scans, the framework planning-artifact audit was run and exited `1` because the product security baseline is incomplete. Artifact path: artifacts/security/g3-security-planning-audit.md

## OWASP Top 10 Coverage

| Category | Status | Notes |
|----------|--------|-------|
| A01 Broken Access Control | OK for reviewed delta | No endpoint/authz change. Existing ownership tests reject cross-tenant/KB links; F0002 consumer behavior is regression evidence, not a recertification. |
| A02 Cryptographic Failures | N/A | No cryptography, transport, or encryption configuration changed. Production encryption posture was not assessed. |
| A03 Injection | OK for reviewed delta | The diff changes only a test context manager. Test/migration values are bound; dynamic migration identifiers come from fixed constants. |
| A04 Insecure Design | OK for reviewed delta | F0003 scope preserves the accepted tenant ownership boundary and does not add permissions, roles, or a new data flow. |
| A05 Security Misconfiguration | N/A | No runtime, container, CORS, cookie, or deployment configuration changed. |
| A06 Vulnerable / Outdated Components | N/A | No dependency or image change; dependency scan was not required by the run's scope boolean. |
| A07 Identification & Authentication Failures | N/A | No identity or session implementation changed. |
| A08 Software and Data Integrity Failures | OK for reviewed delta | Reviewed reconciliation requires the expected mapping digest and approval reference; ambiguous backfill fails closed; audit rows are append-only. |
| A09 Security Logging and Monitoring Failures | OK for reviewed delta | Existing audit path and fail-closed audit behavior have passing PostgreSQL evidence; no logging implementation changed. |
| A10 Server-Side Request Forgery | N/A | No URL fetch, webhook, or server-side network request path changed. |

## Findings

### Medium — Project security planning baseline is incomplete

- **Location:** `planning-mds/security/README.md:17-23`; missing `planning-mds/security/threat-model.md`, `data-protection.md`, `secrets-management.md`, and `owasp-top-10-results.md`.
- **Evidence:** `python3 agents/security/scripts/security-audit.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` exited `1`; captured at artifacts/security/g3-security-planning-audit.md
- **What:** The product baseline still marks the threat model, data-protection, secrets-management, and OWASP results as pending, and the framework audit cannot validate them.
- **Why it matters:** Reviewers lack finalized cross-feature guidance for data classification/retention and secret handling. This does not identify an exploitable weakness in the F0003 diff, which adds no runtime or configuration behavior, but it weakens assurance for future sensitive changes.
- **Exploit scenario:** A later feature introduces a new sensitive data flow or secret and its implementation is reviewed without shared retention, logging, or secret-handling criteria; an unsafe configuration could pass feature review because the expected baseline is absent.
- **Remediation:** Security should complete and validate the four missing baseline artifacts before the next feature that adds a sensitive data flow. Target date: 2026-10-31.
- **Recommendation:** `- [medium] Complete the four pending project security baseline artifacts before the next feature that adds a sensitive data flow — owner: Security; follow-up: Security to complete and validate the four baseline artifacts before the next feature that adds a sensitive data flow; target 2026-10-31.`

No Critical or High findings were identified in the reviewed change set.

## Recommendation Disposition

The medium recommendation is deferred to completion of the project security baseline. It is non-blocking for this F0003 PR because the current delta is a test-only refactor and does not change runtime security behavior. Product Manager acceptance should be recorded at G5 if this verdict remains `PASS WITH RECOMMENDATIONS`.

## Residual Risk and Release Recommendation

The reviewed PR introduces no security-sensitive runtime change. PostgreSQL evidence supports the bounded persistence claims for structural ownership, fail-closed backfill, audit atomicity/immutability, and use of synthetic test data. This review does not certify production transport/encryption settings, privileged DBA controls, or the full inherited F0002 authorization surface. Proceed from G3 with the medium project-baseline recommendation carried to G5 closeout acceptance.

## Result

`PASS WITH RECOMMENDATIONS`
