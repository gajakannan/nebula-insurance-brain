# Test Plan — F0002 run 2026-09-27-bb7c8d1d

**Owner:** Quality Engineer
**Date:** 2026-09-27

## Strategy

The plan follows the assembly plan's "Verification and handoff" section. There are four layers:

1. **Pure kernel units** (no I/O). These cover the v1 carriers (`brain_domain.authx`/`tenancy`), the shared evaluator, the execution-facade transaction contract, delegation issuance, identity profile, and verification.
2. **Contract equivalence.** Implementation carriers are validated against `planning-mds/schemas/authx-kernel.schema.json`. All 12 authored `contract-examples.json` cases round-trip, and every authored invalid shape is refused by the domain types too.
3. **Real PostgreSQL.** This layer runs the migration proof on throwaway databases, the EX-AUTHX security suites through the actual API consumers (content, fact, review, commit), and the sync worker adapter. The brain-jobs and worker recovery proofs run with `BRAIN_TEST_POSTGRES_URL` set. A skipped database test is not a pass, and none of the F0002-relevant tests skip.
4. **Regression.** Every pre-existing F0001 API, commit, review, and security test and every F0005 worker, importer, and recovery test still runs.

Security case expectations are the independently authored EX-AUTHX-001–018 in `worked-examples.md`. Tests assert those outcomes, and each is checked by breaking what it guards. For example, the migration violations assert the exact constraint name that fired, and the invalid-credential tests capture every SQL statement issued.

## Acceptance → test map

| Story / AC | EX-AUTHX | Test ID(s) |
|---|---|---|
| S0001 AC1 hierarchy, AC6 audited rejection | 001 | tests/security/test_authx_scope.py::test_ownership_hierarchy_rejects_cross_tenant_parents_without_partial_writes; packages/brain-persistence/tests/test_tenancy_and_grants.py::test_hierarchy_provisioning_is_idempotent_and_rejects_conflicts; packages/brain-domain/tests/test_tenancy.py |
| S0001 AC2 record/parent ownership incl. worker entry | 001 | tests/integration/test_authx_migration.py::test_expand_reconcile_constrain_preserves_ids_and_enforces_ownership (composite FK violations); neuron tests/integration/test_document_delivery.py (importer writes ownership) |
| S0001 AC3/AC4 tenant-scoped entity identity | 002, 003 | tests/security/test_authx_scope.py::test_entity_identity_is_tenant_scoped_and_grants_nothing |
| S0001 AC5 legacy IDs preserved; inconsistent legacy = explicit failure | — | test_authx_migration.py (all three tests) |
| S0002 AC1 one stable ID, concurrency, restart | 004 | tests/security/test_authx_principals.py::test_concurrent_first_sight_yields_one_principal_that_survives_restart; packages/brain-persistence/tests/test_repositories.py::test_identity_repository_resolves_one_stable_principal |
| S0002 AC2 issuer-namespaced, no email link | 004 | test_authx_principals.py::test_same_subject_at_another_issuer_is_a_distinct_principal |
| S0002 AC3 invalid credential before any lookup | 005 | test_authx_principals.py::test_invalid_credentials_never_touch_protected_storage[10 cases]; tests/security/test_credential_verification.py; packages/brain-security/tests/test_verification.py |
| S0002 AC4 disabled principal | 006 | test_authx_principals.py::test_disabled_principal_gets_the_generic_401_and_an_audited_reason |
| S0002 AC5/AC7 forged identity/kind/roles | 006 | test_authx_principals.py::test_forged_identity_and_role_fields_are_ignored; ::test_unprovisioned_service_client_cannot_become_a_user |
| S0002 AC6 approved link only, no merge | 006 | test_authx_principals.py::test_identity_links_need_approval_and_never_merge_histories |
| S0003 AC1 union then intersection | 007 | test_authx_scope.py::test_union_of_grants_then_request_filter_intersection; packages/brain-security/tests/test_evaluation.py::test_fully_valid_slices_form_a_union, ::test_request_filter_only_narrows |
| S0003 AC2 sibling KB | 002 | test_authx_scope.py::test_entity_identity_is_tenant_scoped_and_grants_nothing; test_evaluation.py::test_sibling_kb_grant_gives_nothing_in_this_kb |
| S0003 AC3 broker ≠ tenant | — | test_evaluation.py::test_broker_filter_never_substitutes_for_tenant |
| S0003 AC4 revocation/expiry, business time | 008 | test_authx_scope.py::test_revocation_and_expiry_deny_the_next_operation; tests/security/test_revocation_propagation.py |
| S0003 AC5 role scoped to its KB | 009 | test_authx_scope.py::test_role_applies_only_in_its_granting_kb |
| S0003 AC6 unavailable grants fail closed | — | test_authx_scope.py::test_unavailable_grant_state_fails_closed_with_503; packages/brain-security/tests/test_execution.py::test_stale_policy_or_unreadable_authority_fails_closed |
| S0003 AC7 revision and outcome change together, audited | 008 | test_authx_scope.py::test_revocation_and_expiry_deny_the_next_operation |
| S0004 AC1/AC2/AC7 each restriction independently; denied ≡ missing; no bytes opened | 010, 011 | tests/security/test_authx_restrictions.py::test_each_restriction_denies_independently_with_equivalent_404; test_evaluation.py (parent/classification/source/no-mixed-slice) |
| S0004 AC3 server-hydrated attributes only; missing fails closed | 011 | test_authx_restrictions.py::test_only_server_hydrated_attributes_count_and_missing_metadata_fails_closed |
| S0004 AC4 evidence dependencies | 012 | test_authx_restrictions.py::test_derived_resource_needs_every_evidence_dependency; test_evaluation.py::test_one_denied_evidence_dependency_denies_the_derived_resource |
| S0004 AC5/AC6 annotation, recheck at submit, never commit | 013 | test_authx_restrictions.py::test_reviewer_annotation_is_rechecked_at_submission_and_never_commits |
| S0005 AC1/AC2/AC4/AC7 intersection, forged refs, traceability | 014 | tests/security/test_authx_delegation.py::test_delegated_authority_is_the_intersection_and_fully_traceable |
| S0005 AC3 revoke between job steps | 015 | test_authx_delegation.py::test_worker_steps_reauthorize_after_delegation_revocation; neuron test_document_delivery.py::test_job_authorization_reloads_revocations_and_audits_denials |
| S0005 AC5 autonomous service | 016 | test_authx_delegation.py::test_autonomous_service_commits_under_its_own_grant_only |
| S0005 AC6 onward/wider/unregistered | 014 | test_authx_delegation.py::test_issuance_refuses_wider_onward_expired_or_unregistered_ceilings; packages/brain-security/tests/test_delegation.py |
| S0006 AC1/AC2/AC3/AC4 audit contents, no token, durable reference | 017 | tests/security/test_authx_audit.py::test_allowed_and_denied_calls_leave_matching_non_secret_audit |
| S0006 AC3 audit failure injection | 018 | test_authx_audit.py::test_audit_persistence_failure_never_yields_an_unaudited_success[content/commit/review]; test_execution.py::test_audit_failure_releases_no_payload |
| S0006 AC5 annotation ≠ commit; commit rechecks; outbox atomic | 013/016 | tests/security/test_authx_consumers.py::test_annotation_and_commit_are_independent_authorizations |
| S0006 batch semantics / partial failure | — | test_authx_consumers.py::test_batch_with_an_inaccessible_item_writes_nothing, ::test_failed_item_rolls_back_the_whole_batch_and_is_audited |
| S0006 concurrent revoke vs commit | 008 | test_authx_consumers.py::test_revocation_linearizes_against_concurrent_commits |
| S0006 AC6 case ledger | all | this table and test-execution-report.md |
| S0006 AC7 regression + coverage + latency | — | full engine and neuron suites; coverage-report.md; test_authx_consumers.py::test_measured_local_decision_latency |
| Trusted submission (worker CLI) | 011 | neuron tests/integration/test_worker_cli_enqueue.py |
| Contract equivalence | 002/005/007/011/014/017 | tests/contract/test_authx_kernel.py (15 cases) |

## Section 121.2 matrix: deferred categories

These categories have owning features and are not counted as passed. Projection leakage beyond the kernel boundary is owned by F0033–F0035/F0046. Conversation and session continuity is owned by F0021/F0037–F0040. MCP and general execution delegation is owned by F0047/F0059. Python/.NET policy parity and production IdP rollout are owned by F0026. Full review-to-canonical orchestration and review UI are owned by F0018/F0022.

## Environment

Local Docker Compose (PostgreSQL 18 + pgvector/AGE, authentik 2026.2.0), with the engine and neuron uv workspaces on Python 3.14. Commands and outputs are listed in test-execution-report.md.
