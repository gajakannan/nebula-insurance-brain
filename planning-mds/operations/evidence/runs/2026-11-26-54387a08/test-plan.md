# F0012 Test Plan — Foundation ontology

- Role: Quality Engineer
- Reviewer: Claude (Opus 5.5) / Quality Engineer
- Date: 2026-11-26
- Run: `2026-11-26-54387a08`
- Scope: all 46 ACs of F0012-S0001 to S0007; synthetic development data only, outside any frozen holdout.

## Strategy

| Layer | Where | What it proves |
|---|---|---|
| Offline unit | `engine/packages/brain-ontology/tests/` (`test_authoring.py`, `test_compiler.py`, `test_semantics_impact.py`, `test_cli.py`) | Every authoring rejection rule with its stable code and ordered error list; identity grammar, reuse, collision, change records; compile determinism, manifest, dependency lock, projection coverage; supported inference only; RDF export; impact classification, closure and constraint diffs; CLI exit codes |
| PostgreSQL integration (owned database per test, migrated to head) | `engine/tests/integration/test_ontology_release_install.py`, `test_ontology_activation.py`, `test_temporal_kind_activation.py` | Atomic, idempotent, concurrent install; database immutability; digest, module-version and identity refusals at install; denials audited; tenant extensions refused; unchanged authorization (EX-PC-011); refused downgrade; registry scope; ETERNAL/EVENT/STATE commits and mismatches through the real route; report, review, activation refusal matrix, concurrent activation, rollback history, split scenario, EX-ONT-003/004, two-tenant scope |
| Regression | Full engine suite; F0007/F0008/F0009 suites unchanged | Commit path, registry and range changes do not regress shipped behaviour |
| Contract | F0011 pipeline: `generate.py --check`, Python jsonschema/Pydantic + AJV conformance, contract unit tests, install smoke | Three new resources, the widened `fact-version-read-v1`, branch witnesses for every new conditional |
| Semantic examples | `validate_semantic_examples.py`, `validate_semantic_rdf.py --require`, `build_foundation_examples.py --check` | Account-scoped Cedar Bridge cases on foundation IRIs: isomorphism, entailments, forbidden domain typing, SHACL boundaries, exact and forbidden query rows |
| Release lock | `python -m brain_ontology.cli compile --check` | Committed foundation@1 outputs equal a fresh compile byte for byte |

## AC to test map

| Story / AC | Test(s) |
|---|---|
| S0001 AC1 | `test_ac1_foundation_module_validates_and_names_the_schema`, `test_ac1_minimal_module_is_valid`, `test_validate` (CLI) |
| S0001 AC2 | `test_ac2_singular_parent_is_retired`, `test_ac2_empty_parents_is_a_root`; no output: `test_compile_check_and_write` |
| S0001 AC3 | `test_ac3_definition_examples_regressions_required`, `test_ac3_missing_fields_each_reported`, `test_ac3_unresolved_references`, `test_ac3_reference_rules` |
| S0001 AC4 | `test_ac4_labels`, `test_ac4_duplicate_preferred_label_in_one_tag` |
| S0001 AC5 | `test_ac5_temporal_kind_required_and_closed` (missing, unknown, lowercase) |
| S0001 AC6 | `test_ac6_unsupported_term_constructs` (symmetric, transitive, equivalent_class, functional), `test_ac6_unsupported_constraint_construct`, `test_domain_and_range_never_infer`, RDF forbidden typing (`untyped-domain-probe.ttl`) |
| S0001 AC7 | `test_ac7_constraint_execution_context` (each field), `test_ac7_inferred_basis_names_the_ruleset`, `test_ac7_all_errors_in_deterministic_order`, `test_ac7_yaml_error_is_one_error_with_position`, CLI exit 1 |
| S0002 AC1 | `test_s0002_ac1_iri_mapping_and_grammar` |
| S0002 AC2 | `test_s0002_ac2_identity_reuse_rejected`, `test_s0002_ac2_additive_axiom_keeps_iri`, `test_check_identity_direct`, `test_identity_reuse_refused_at_install` |
| S0002 AC3 | `test_s0002_ac3_duplicate_ids_collide`, `test_s0002_ac3_cross_module_collision`, `test_cross_module_collision_and_duplicate_keys`; uppercase/non-ASCII refused by grammar |
| S0002 AC4 | `test_s0002_ac4_label_change_keeps_iri_and_digest`, `test_ac3_new_release_keeps_slot_identity` (relabelled foundation@2 installed beside @1), impact `rename_alias` |
| S0002 AC5 | `test_s0002_ac5_removal_needs_retirement`, `test_s0002_ac5_change_record_shapes`, impact split/retirement classification |
| S0002 AC6 | `test_s0002_ac6_tenant_namespace_reserved`, `test_tenant_extension_install_is_unsupported` |
| S0003 AC1–AC5 | `test_s0003_ac1_classes`, `test_s0003_ac2_temporal_kinds`, `test_s0003_ac3_role_kinds`, `test_s0003_ac4_scope_class`, `test_authoring_constraints_execute` (non-member scope), `test_s0003_ac5_constraints_and_no_majority` |
| S0003 AC6 | `test_vocabulary_grants_nothing` (decisions identical before/after install); policy.csv rows only for `ontology_release` |
| S0003 AC7 | `validate_semantic_examples.py`, `validate_semantic_rdf.py --require` (foundation folder) |
| S0004 AC1 | `test_ac1_committed_lock_matches_a_fresh_compile`, `test_ac1_fresh_checkout_and_shuffled_source`, CLI `compile --check` |
| S0004 AC2 | `test_same_module_version_with_new_content_refused`, `test_reinstall_is_idempotent` |
| S0004 AC3 | `test_ac3_manifest_fields`, `test_ac3_constraint_metadata_in_normalized_release`; actor/time on the installed row (`test_install_writes_one_immutable_release`) |
| S0004 AC4 | `test_ac4_dependencies` (exact, floating, ranged, wrong digest, missing, two versions) |
| S0004 AC5 | `test_ac5_projection_uncovered`, `test_ac5_projection_mapping_contents` |
| S0004 AC6 | `test_install_writes_one_immutable_release`, `test_failure_mid_install_leaves_no_rows`, `test_reinstall_is_idempotent`, `test_concurrent_install_gives_one_set_of_rows`, `test_installed_rows_are_immutable`, `test_truncate_refused_on_every_table`, `test_digest_mismatch_refused_before_any_row` |
| S0004 AC7 | `test_denied_install_is_audited_and_writes_nothing`, `test_unprovisioned_scope_fails_closed`, no selection on install, canonical table counts unchanged |
| S0005 AC1 | `test_s0005_ac1_predicate_contracts_from_manifest`, installed `ontology_term` predicate rows |
| S0005 AC2 | `test_ac2_registry_serves_installed_releases_of_the_scope_only`, `test_registry_strict_mode_detects_missing_prepare` |
| S0005 AC3 | `test_ac3_new_release_keeps_slot_identity`; changed major needs `semantic_change` (identity rules) |
| S0005 AC4 | `test_ac4_eternal_commit_shape_and_conflict`, `test_ac4_event_commit_is_one_period`, `test_ac4_state_commit_unchanged` |
| S0005 AC5 | Legacy inventory (G1 query + source scan), `test_ac5_no_legacy_row_rewritten` |
| S0005 AC6 | `test_ac6_existing_slot_uses_its_recorded_release`, `test_ac6_commit_authorization_unchanged` |
| S0006 AC1 | `test_rename_split_retirement_and_unclassified`, `test_first_release_report_review_activate` |
| S0006 AC2 | `test_ex_ont_003_entailment_change_in_an_additive_edit`, `test_bound_exceeded_is_unresolved_never_no_change`, `test_ex_ont_003_and_004_reported` |
| S0006 AC3 | `test_ex_ont_004_constraint_tightening_with_unchanged_closure`, `test_constraint_diffs_by_kind`, `test_ex_ont_003_and_004_reported` |
| S0006 AC4 | `test_report_reach_and_determinism`, `test_split_scenario_end_to_end` (reach), `test_scope_across_two_tenants`, unexamined list |
| S0006 AC5 | `test_activation_refusals` (each reason), `test_grants_are_enforced_and_audited`, first-release report has `predecessor: null` |
| S0006 AC6 | `test_rollback_history_and_no_rewrite`, `test_concurrent_activation_one_winner`, `test_selection_guard_is_the_database_backstop` |
| S0006 AC7 | `test_split_scenario_end_to_end` |
| S0007 AC1 | ADR-0045 case log in test-execution-report.md |
| S0007 AC2 | `semantic_rdf --require` (release isomorphism and entailments), `test_rdf_export_deterministic_and_equivalent` |
| S0007 AC3 | F0011 conformance (`conformance.json`), contract unit tests, install smoke |
| S0007 AC4 | Migration 0017 on populated F0007–F0009 data (checksums), full engine suite, `test_downgrade_refused_after_install` |
| S0007 AC5 | Changed-line coverage report; zero parse/model calls (no Docling/model import or call in the new paths; canonical counts unchanged by install/report/activate) |
| S0007 AC6 | `examples/README.md`, glossary, EX-ONT-007/008; ADR evidence notes |

## Entry and exit criteria

- Entry: G1 runtime preflight PASS (`g1-runtime-preflight.md`).
- Exit:
  - every test above passes in the runtime container;
  - the full engine suite shows no new failure beyond the three known `pg_dump` image limitations;
  - coverage on changed executable lines is at least 80%;
  - the conformance suite reports 0 mismatches.
