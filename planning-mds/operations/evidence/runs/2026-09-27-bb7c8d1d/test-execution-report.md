# Test Execution Report — F0002 run 2026-09-27-bb7c8d1d

**Owner:** Quality Engineer
**Date:** 2026-09-27
**Code under test:** branch feature/F0002-tenancy-kernel. Cycle 1 at ade364c/4777949; cycle 2 (G4 fix-issues) at 89f5dd5. The results table reports cycle 2.

## Environment

- Docker Compose: brain-postgres (PostgreSQL 18, pgvector 0.8.6, AGE 1.8.0), authentik 2026.2.0, all healthy (see g1-runtime-preflight.md).
- Dev database migrated 0003 → 0006 (applied through runlog; output in artifacts/test-results/g2-dev-db-migrate.txt).
- `BRAIN_TEST_POSTGRES_URL=postgresql+psycopg://brain:brain@localhost:5432/brain` is set for every run, so the brain-jobs and worker-recovery PostgreSQL proofs execute instead of skipping.

## Results

| Suite | Command (full text in commands.log) | Result |
|---|---|---|
| Engine: all tests (unit, contract, integration, migration, security) | `uv run pytest -q -rs --junitxml ... --cov ...` in engine/ | 282 passed, 0 failed, 0 skipped (cycle 1: 277) |
| Engine static gates | `ruff check .`, `ruff format --check .`, `mypy <9 source roots incl. brain-testing>` | clean |
| Engine per-package coverage gates (CI-equivalent, ≥ 80%) | loop over 8 packages with `--cov-fail-under=80` | all pass (see coverage-report.md) |
| Neuron: all tests + static gates | `ruff check`, `ruff format --check`, `mypy`, `pytest` in neuron/ | 75 passed, 3 skipped (opt-in live vLLM/Graph inference, not F0002 scope), 0 failed |
| Migration proof on throwaway PostgreSQL databases | tests/integration/test_authx_migration.py | 4 passed (0005/0006 proofs plus the 0007 safeguards proof) |
| Measured local latency | test_authx_consumers.py::test_measured_local_decision_latency | p50 12.94 ms, p95 14.14 ms, max 19.55 ms (60 samples, 1 grant slice, 0 dependencies; cycle 1: 13.15/14.38/20.77); no SLO claimed |

The first neuron run failed on mypy (an unannotated helper in the new CLI test). It was fixed and re-run; both runs are in commands.log. No product-code failure occurred during G2.

## EX-AUTHX case ledger (independent expectation → actual observed outcome)

| Case | Expected (worked-examples.md) | Observed |
|---|---|---|
| EX-AUTHX-001 | Owned association accepted; swapped parent rejected with no partial write | KB under a foreign workspace raises OwnershipConflict and no row is written; the rejection is audited without foreign IDs. In the DB, `fk_document_version_source_document_id_owner`, `fk_source_document_kb_owner`, and `fk_kb_workspace_owner` fire exactly |
| EX-AUTHX-002 | Entity shared by A1/A2; A1-only actor gets nothing in A2 | A1 artifact 200, A2 artifact 404; 2 associations created, 0 memberships created |
| EX-AUTHX-003 | Same external key in tenants A/B are distinct | Different entity IDs; associating A's entity to B's KB raises OwnershipConflict; fact slot for a foreign entity raises `fk_fact_slot_entity_owner` |
| EX-AUTHX-004 | One durable ID under repeat/concurrent resolution; issuer-namespaced | 8 concurrent first-sight requests produce 1 principal and 1 alias, stable across a fresh session; the same subject at another issuer is a distinct ID |
| EX-AUTHX-005 | Generic 401; safe authentication audit; no principal/membership/resource lookup | 10 credential variants each return 401 `unauthenticated`. Captured SQL is only `insert into authentication_event`; 0 statements touch principal/external_identity/membership/resource_access/content_artifact; 0 bytes are opened; no token appears in the event |
| EX-AUTHX-006 | Disabled/forged/unapproved identities are denied or require reconciliation | Disabled principal gets 401 with a `disabled_principal` event, for both an existing and a nonexistent artifact. Forged headers/query do not change the actor. An unapproved link is refused; an approved link keeps the existing ID; a conflicting link raises AliasConflict. An unprovisioned service client creates no principal |
| EX-AUTHX-007 | Union, then filter intersection; a filter never adds | Accounts X and Y are allowed and Z is denied. A narrowing filter gives `scope_denied`, a widening filter is denied, and a foreign-KB filter is denied |
| EX-AUTHX-008 | Next operation after revoke/expiry is denied; past business time does not reinstate | After revoke: 404 with `no_membership` at authority revision +1; `/facts` at 2026-01-01 coordinates also 404; an expired grant gives `membership_expired`; concurrent revoke vs 6 commits is linearized (each commit either allowed below the revoked revision with 1 version, or denied at it with 0) |
| EX-AUTHX-009 | Role applies only in its granting KB | Annotate in A2 is 404; annotate in A1 is 200 (applied=1); read in A2 is 200 |
| EX-AUTHX-010 | Classification (and inverted parent) each deny alone | `parent_denied` and `classification_denied` each 404 with 0 file reads; the permitted combination is 200 |
| EX-AUTHX-011 | Source ACL denies; forged attributes ignored; missing metadata fails closed | `source_denied` 404; forged query/header 404; deleted metadata gives `missing_attributes` with null scope; metadata disagreeing with the record's owner gives 404 |
| EX-AUTHX-012 | One denied evidence dependency denies the derived resource | `dependency_denied`; all-visible dependencies give allowed. A Reviewer-only principal still cannot read the evidence artifact |
| EX-AUTHX-013 | Annotation persists with the authenticated reviewer; revoked/reclassified submit denied; never commit | Decision persisted with `reviewer_principal_id` = authenticated principal, and the audit links the authorization decision ID, policy hash, and grant revision. Reclassified task gets `classification_denied` with 0 decisions; revoked reviewer 404 with 0 decisions; reviewer commit 404 with 0 fact versions |
| EX-AUTHX-014 | Only the intersection of the actor's grant and the ceiling | Delegated read allowed with actor=user, executor=agent, delegation ID and revision recorded. Outside the ceiling gives `delegation_denied`; another executor or an unknown ID gives `delegation_denied`; the actor's grant revoked gives `no_membership`. Wider/onward/USER-executor/expired issuance is refused with 0 rows |
| EX-AUTHX-015 | Revoked/expired delegation denies the next job step | Worker ingest allowed, then delegation revoked, then interpret raises PermissionError (`delegation_expired`); a forged delegation in the payload gives `delegation_denied`; membership revoked mid-job gives PermissionError |
| EX-AUTHX-016 | Autonomous service uses its own grant; audited as a service | Commit 201 with `actor_kind=service`, null delegation and executor; another tenant's slot 404; an agent with no delegation or grant 404 |
| EX-AUTHX-017 | Outcome and audit agree; versions and trace recorded; no token/payload; denied mutation leaves no state | 6 calls across content/fact/review: each decision validates against schema `Decision` and carries policy hash, release, grant revision ≥ 1, and trace. No token, PDF bytes, or fact value in the payload. The allowed commit is referenced by `canonical_commit.authorization_decision_id`; the denied commit and denied annotation wrote 0 rows |
| EX-AUTHX-018 | Audit persistence failure yields no success | Injected failure on `INSERT INTO audit_event` gives 503 `unavailable` for content, commit, and review; 0 bytes, 0 fact versions/outbox/commit rows, 0 review decisions, 0 decisions persisted |

## Cycle 2 (G4 fix-issues) additions

- 0007 safeguards: 8 ownership/audit rewrite attempts, each refused with `check_violation` (document_version, review_item, resource_access, membership principal, knowledge_base workspace, external_identity principal, audit_event UPDATE, audit_event DELETE). Non-ownership updates (revocation, review status) still succeed. A correction assertion loads before its original only under `SET CONSTRAINTS ALL DEFERRED`; immediately it raises ForeignKeyViolation.
- Worker lease/metadata KB mismatch is recorded as `scope_denied`, and the matching lease is allowed.
- Hydration refuses metadata that disagrees with the record owner (SQLite unit, beneath the 0007 trigger); the PostgreSQL tamper attempt is refused by the trigger.
- The EX-AUTHX ledger above was re-executed unchanged in cycle 2 (all 18 as expected).

## Evidence artifacts

artifacts/test-results/g3r-engine-pytest.txt
artifacts/test-results/g3r-engine-junit.xml
artifacts/test-results/g3r-engine-static.txt
artifacts/test-results/g3r-neuron-pytest.txt
artifacts/test-results/g3r-neuron-junit.xml
artifacts/test-results/g3r-authx-latency.json
artifacts/test-results/g3r-dev-db-migrate-0007.txt
artifacts/coverage/g3r-package-coverage-gates.txt
artifacts/coverage/g3r-engine-coverage.json

Cycle 1:

artifacts/test-results/g2-engine-pytest.txt
artifacts/test-results/g2-engine-junit.xml
artifacts/test-results/g2-engine-static.txt
artifacts/test-results/g2-neuron-pytest.txt
artifacts/test-results/g2-neuron-junit.xml
artifacts/test-results/g2-authx-latency.json
artifacts/test-results/g2-dev-db-migrate.txt
artifacts/coverage/g2-package-coverage-gates.txt
artifacts/coverage/g2-engine-coverage.json
artifacts/coverage/g2-engine-coverage.xml

## Deferred (not counted as passed)

The section 121.2 categories owned by later features are listed in test-plan.md. Live vLLM/Graph inference proofs remain opt-in F0005 work.

Result: PASS
