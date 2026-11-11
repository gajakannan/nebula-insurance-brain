# Test Plan — F0007-factslot-model run 2026-11-09-b94cfa12

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-09
- Independence note: the same agent session implemented the feature and authored these tests. Expectations were written from the story ACs, ADR-0077, ADR-0039 and the F0007 worked examples, not read back from the code. The 26 design cases in `contract-examples.json` were authored at plan time and are checked unchanged against both the schemas and the runtime parser. Independent review is the G3 Code and Security reviewers' job.

## Story-to-AC Mapping

Paths: `R` = `engine/tests/integration/test_factslot_resolution.py`, `A` = `test_factslot_answers.py`, `N` = `test_factslot_names.py`, `O` = `test_factslot_ownership.py`, `M` = `test_factslot_migration.py` (all under `engine/tests/integration/`). `U` = `engine/packages/brain-factslots/tests/`, `D` = `engine/packages/brain-domain/tests/test_fact_slots.py`.

| AC | Test(s) | Runtime |
|---|---|---|
| S0001 AC1 | R `test_s0001_ac1_resolving_twice_and_concurrently_returns_one_slot` (6 concurrent sessions) | PostgreSQL |
| S0001 AC2 | R `test_s0001_ac2_basis_splits_and_input_order_does_not` | PostgreSQL |
| S0001 AC3 | R `test_s0001_ac3_typed_normalization_and_stored_qualifier_rows`, R `test_s0001_ac3_forced_collision_is_rejected_never_merged`; D decimal/JCS/fingerprint tests | PostgreSQL + unit |
| S0001 AC4 | R `test_s0001_ac4_omitted_and_explicit_null_are_distinct`; D qualifier tests | PostgreSQL + unit |
| S0001 AC5 | R `test_s0001_ac5_two_kbs_two_slots_and_kb_b_principal_sees_not_found` | PostgreSQL + HTTP GET |
| S0001 AC6 | R `test_s0001_ac6_malformed_or_unpinned_key_writes_no_row` (5 cases), R `test_s0001_ac6_predicate_key_is_exposed_unchanged` | PostgreSQL |
| S0001 AC7 | R `test_s0001_ac7_creation_is_audited_and_unauthorized_writes_nothing`, R `test_s0001_restrictions_union_of_sources` | PostgreSQL |
| S0002 AC1 | R `test_s0002_ac1_cardinality_conflict_and_invalid`; U `test_collision_and_cardinality_conflict_roll_back` | PostgreSQL + unit |
| S0002 AC2 | O `test_s0002_ac2_single_slot_overlap_still_hits_the_exclusion`; existing `test_bitemporal_commit`, `test_commit_concurrency` | PostgreSQL |
| S0002 AC3 | R `test_s0002_ac3_two_insureds_two_members_and_duplicate_resolves`, O `test_s0002_ac3_ac5_members_carry_independent_versions` | PostgreSQL |
| S0002 AC4 | R `test_s0002_ac4_relationship_identity_includes_object` | PostgreSQL |
| S0002 AC5 | O `test_s0002_ac3_ac5_members_carry_independent_versions` | PostgreSQL + HTTP commit |
| S0002 AC6 | R `test_s0002_ac6_named_rejections_write_no_rows` (7 reasons + unauthorized) | PostgreSQL |
| S0003 AC1 | A `test_s0003_ac1_all_nine_states_are_accepted` (9), A `test_s0003_ac1_any_other_state_is_rejected` (4) | PostgreSQL + HTTP commit |
| S0003 AC2 | A `test_s0003_ac2_state_value_mismatch_writes_no_version` (4) | PostgreSQL + HTTP |
| S0003 AC3 | A `test_s0003_ac3_absence_scope_required_and_owned` | PostgreSQL + HTTP |
| S0003 AC4 | A `test_s0003_ac4_unread_slot_reads_not_processed_never_null` | PostgreSQL |
| S0003 AC5 | A `test_s0003_ac5_ex_own_003_three_kinds_of_no_value` (commit, reload, pilot GET) | PostgreSQL + HTTP |
| S0003 AC6 | A `test_s0003_ac6_unreadable_scope_is_denied_before_any_explanation` | PostgreSQL + HTTP |
| S0003 AC7 | A `test_s0003_ac7_accepted_answer_is_audited_and_rejection_writes_nothing` | PostgreSQL + HTTP |
| S0004 AC1 | A `test_s0004_ac1_ac3_money_rejections` (7), A `test_s0004_ac1_basis_required_where_the_predicate_requires_it`; D money tests | PostgreSQL + unit |
| S0004 AC2 | A `test_s0004_ac2_exact_decimal_canonical_form_and_round_trip`; D decimal tests | PostgreSQL + unit |
| S0004 AC3 | A money rejection `converted_from` case; D conversion cases | PostgreSQL + unit |
| S0004 AC4 | R `test_s0004_ac4_ac6_identifier_members_are_scheme_scoped`, A `test_s0004_ac4_ac5_identifier_values` | PostgreSQL |
| S0004 AC5 | same two tests; D identifier tests | PostgreSQL + unit |
| S0004 AC6 | R `test_s0004_ac4_ac6_identifier_members_are_scheme_scoped` (money qualifier, identifier member) | PostgreSQL |
| S0004 AC7 | A `test_s0004_ac7_unauthorized_caller_gets_denial_before_value_detail`, R AC6 zero-row cases | PostgreSQL + HTTP |
| S0005 AC1 | N `test_s0005_ac1_system_predicate_cardinalities`, N `test_s0005_ac1_resolving_legal_name_as_multi_is_cardinality_conflict` | unit + PostgreSQL |
| S0005 AC2 | N `test_s0005_ac2_ex_sem_008_rename_is_a_new_version_in_the_same_slot` | PostgreSQL + HTTP |
| S0005 AC3 | N `test_s0005_ac3_name_without_admitted_evidence_is_rejected` (real F0006 v2 assertion) | PostgreSQL + HTTP |
| S0005 AC4 | N `test_s0005_ac4_kb_a_trade_name_is_invisible_in_kb_b` | PostgreSQL + HTTP |
| S0005 AC5 | N `test_s0005_ac5_display_hook_is_precedence_free_and_creates_no_alias` | PostgreSQL |
| S0006 AC1 | M `test_s0006_ac1_ac6_up_down_up_keeps_pilot_rows_identical`, M `test_s0006_ac1_ac2_legacy_slots_read_back_unchanged_and_stay_legacy` | PostgreSQL + HTTP GET |
| S0006 AC2 | M `test_s0006_ac1_ac2_legacy_slots_read_back_unchanged_and_stay_legacy`, O legacy NULL-to-value trigger case | PostgreSQL |
| S0006 AC3 | Existing suites unchanged: `test_bitemporal_commit`, `test_commit_concurrency`, `test_assertion_consumers`, `apps/api/tests/test_facts.py`, `test_reviews.py` (full engine run) | PostgreSQL |
| S0006 AC4 | O `test_s0006_ac4_child_rows_cannot_point_at_another_owner`, O `test_s0006_ac4_identity_and_ownership_columns_are_immutable` (direct SQL as the application role) | PostgreSQL |
| S0006 AC5 | Inventory in `GETTING-STARTED.md` and the assembly plan; migration review shows no RLS, `BYPASSRLS` or `SECURITY DEFINER` (G3 Security) | Review |
| S0006 AC6 | M `test_s0006_ac1_ac6_up_down_up_keeps_pilot_rows_identical`, M `test_s0006_ac6_downgrade_refuses_while_identity_rows_exist` | PostgreSQL |
| S0006 AC7 | R AC5, O `test_relationship_and_cross_kb_reads_are_not_disclosed` (denial audit rows), R AC7 creation audit | PostgreSQL + HTTP |

## Test Strategy

- **Pure domain (unit):** canonical decimal, money, identifier, name and JCS vectors; qualifier canonicalization; fingerprint document; answer reason precedence.
- **Application (unit, in-memory store):** every resolver and policy branch, registry rules, name hook ordering, legacy reads.
- **Contract agreement:** the 26 plan-time cases validated against the three design schemas, and the 14 answer cases against the runtime parser.
- **PostgreSQL integration:** each test owns a fresh database migrated to head through `BRAIN_MIGRATION_ADMIN_URL`. The suites cover concurrency, keys, triggers, the authorization facade, and the HTTP commit/GET routes through the real app with dependency overrides for the principal, session and predicate registry.
- **Regression:** full engine suite on an owned database at head, the neuron suite, and the F0006 migration/backup drills.

## Developer-vs-QE Test Ownership

Developer-level unit tests are `brain-domain/tests/test_fact_slots.py` and `brain-factslots/tests/*`. The QE-level PostgreSQL acceptance suites are the five `test_factslot_*` files, plus the harness under `engine/tests/fixtures/factslots/`. In this run one agent covered both roles, as stated above.

## Test Data / Fixtures

- `brain_testing.factslots`: the `test` predicate namespace, used only in test composition, plus `seed_subject` and `slot_key`.
- `engine/tests/fixtures/factslots/harness.py`: an owned-DB world with tenant T, KB A, KB B, a subject associated with both, service, KB-B service and KB-B reader principals.
- `pilot-seed.sql` and `pilot-before.json`: deterministic pilot rows and their snapshot at revision 0011.
- The F0006 harness publishes immutable content and admits a real v2 assertion as name evidence.

All data is synthetic, kept outside the frozen holdout.

## Happy / Edge / Error / Auth / Accessibility / Regression Cases

- **Happy path:** create, resolve, members, relationships, nine states, exact money, scoped identifiers, names and renames.
- **Edge cases:** decimal forms, NFC text, reversed qualifier order, explicit null, forced collision, 6-way concurrency, pages and blocks in scopes, above-2^53 amounts, downgrade with pilot rows.
- **Errors:** every resolution reason and every answer reason, each asserting zero written rows.
- **Authorization:** INTERPRET denial, KB-B principals, a restricted scope artifact, unauthorized commit before any value detail, and 404 indistinguishable from a missing slot.
- **Accessibility:** not applicable, since F0007 has no UI.
- **Regression:** pilot snapshot byte-equality, existing suites unchanged, and the backup/restore drills.

## Risks And Mitigations

- **Authorship:** the same agent built and tested the feature. Mitigation: AC-derived expectations, plan-time contract cases, and G3 independent review.
- **DAST reach:** the local scan runs without credentials. Authenticated commit and denial behaviour is covered by the HTTP integration tests.

## Result

PASS. All 39 ACs map to executed tests or a named review check (S0006 AC5).
