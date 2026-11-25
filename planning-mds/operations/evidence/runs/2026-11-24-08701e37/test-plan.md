# F0009 Test Plan

Owner: Claude (Opus 5.5) / Quality Engineer
Date: 2026-11-24
Run: 2026-11-24-08701e37
Status: executed; results in [test-execution-report.md](test-execution-report.md)

## Scope and approach

All six stories and 41 ACs are in scope. The assembly plan's AC-to-proof map controls what each test must prove. Planning-time examples are not counted as runtime proof. The EX-PROV fixtures are synthetic development data and stay outside the frozen holdout.

QE authored its expectations independently of the implementation. [`engine/tests/fixtures/f0009_provenance.py`](../../../../../engine/tests/fixtures/f0009_provenance.py) derives the expected edges with raw SQL from the *stored basis* column of the plan's Edge Semantics table, and imports nothing from the reader's traversal (S0006 AC5). Each test compares those expected edges with the reader's actual output.

## Layers

| Layer | Suite | Database |
|---|---|---|
| Domain carriers and graph invariants | `engine/packages/brain-domain/tests/test_provenance.py` | none |
| Facade `prepare_reads` order, denial, expiry, audit | `engine/packages/brain-security/tests/test_provenance_prepared_read.py` | none (authority fake) |
| Reader orchestration and output guard | `engine/packages/brain-provenance/tests/test_reader.py` | none |
| Review service: reservation, stale retention, preflight | `engine/packages/brain-review/tests/test_f0009_decisions.py` | none |
| Review boundary through the unchanged HTTP route | `engine/tests/integration/test_f0009_corrections.py` | owned PostgreSQL 18 |
| Reader over v2 assertions and review history | `engine/tests/integration/test_f0009_provenance.py` | owned PostgreSQL 18 |
| Reader over the F0008 split fixture, mixed access | `engine/tests/integration/test_f0009_temporal_lineage.py` | owned PostgreSQL 18 |
| Migration 0016 and direct-SQL guards | `engine/tests/integration/test_f0009_migration.py` | owned PostgreSQL 18 |
| HTTP surface and envelope parity | `engine/apps/api/tests/test_f0009_review_compatibility.py` | none |
| Contract conformance (JSON Schema, Pydantic, AJV) | `scripts/contracts/check.py` + `experience/scripts/contracts/check.mjs` | none |
| Regression | full engine suite; host restore lane; Neuron shared bundle | dev `brain_f0009` plus owned databases |

## AC traceability

| AC | Proof (test) |
|---|---|
| S0001 AC1 | provenance::test_ex_prov_001_exact_source_chain_is_complete |
| S0001 AC2 | temporal::test_ex_prov_003_remainder_names_its_predecessor_and_changes (exact root, no latest substitution); provenance::test_recorded_decision_link_follows_an_independent_commit |
| S0001 AC3 | provenance::test_ex_prov_001 (stored run/profile/semantics/content record); test_legacy_assertion_is_authorized_then_labelled_incomplete |
| S0001 AC4 | DERIVED → DERIVATION_UNAVAILABLE gap (reader); no derivation producer exists, and nothing is fabricated (domain edge table; test_legacy…) |
| S0001 AC5 | provenance::test_correction_chain_limit_refuses_at_limit_plus_one; domain test_record_limit…, test_correction_and_split_cycles…; temporal::test_concurrent_change… |
| S0001 AC6 | provenance::test_ex_prov_001 (byte snapshots unchanged; authorization audit only) |
| S0001 AC7 | provenance::test_unknown_inaccessible_and_mismatched_anchors_are_indistinguishable; test_legacy_assertion… |
| S0002 AC1 | corrections::test_effective_correction_appends_lineage_and_one_reservation |
| S0002 AC2 | same (v2 child of a v2 original; original row and artifacts unchanged) |
| S0002 AC3 | corrections::test_reservation_failure_rolls_back_the_whole_correction |
| S0002 AC4 | corrections::test_replay_returns_prior_outcome_without_new_effects |
| S0002 AC5 | corrections::test_stale_submission_is_retained_and_legacy_get_is_unchanged; decisions::test_stale_correction_retains… |
| S0002 AC6 | corrections::test_competing_correction_is_retained_as_a_non_applied_attempt; test_mixed_batch_refuses_whole_batch_and_sibling_reapplies_alone |
| S0002 AC7 | corrections::test_non_correcting_actions_reserve_nothing; test_unresolved_evidence_requires_blocked_and_creates_nothing |
| S0002 AC8 | corrections::test_reviewer_identity_cannot_be_supplied; test_effective_correction (zero canonical rows) |
| S0003 AC1 | temporal::test_ex_prov_003 (exact coordinates and temporal block) |
| S0003 AC2 | temporal::test_ex_prov_003 (remainder keeps its predecessor's payload, evidence and receipt) |
| S0003 AC3 | temporal::test_ex_prov_003 (stored split reason; no corrected_from); provenance::test_recorded_decision… (stored commit and actor) |
| S0003 AC4 | temporal::test_supporting_and_ending_evidence_stay_distinct |
| S0003 AC5 | provenance::test_ex_prov_002 (no version); test_recorded_decision_link_follows_an_independent_commit |
| S0003 AC6 | temporal::test_broken_split_and_cross_scope_links_cannot_be_stored; test_cross_kb_anchor_and_spoofed_slot_are_non_disclosing |
| S0003 AC7 | temporal::test_ex_prov_003 (canonical snapshots unchanged); F0008 suites unchanged and passing |
| S0004 AC1 | security::test_prepared_sources_are_decided_before_the_single_load; reader::test_discovery_and_authorization_precede_materialization |
| S0004 AC2 | provenance::test_unknown_inaccessible…; temporal::test_cross_kb… |
| S0004 AC3 | temporal::test_ex_prov_004_one_denied_source_refuses_the_whole_history; test_current_grant_governs_a_historical_coordinate |
| S0004 AC4 | provenance::test_review_records_need_current_review_task_read; corrections::test_unauthorized_annotator_leaves_zero_effects |
| S0004 AC5 | provenance::test_unknown_inaccessible… (arbitrary, foreign or wrong-kind anchor); migration guard tests |
| S0004 AC6 | provenance::test_revoked_grant_refuses_old_history_without_leaking; temporal::test_concurrent_change…; security expiry tests |
| S0004 AC7 | provenance::test_revoked_grant… (caplog, exception text); temporal::test_ex_prov_004 (caplog) |
| S0005 AC1 | corrections::test_effective_correction…; provenance::test_ex_prov_002 |
| S0005 AC2 | corrections::test_reservation_failure…; decisions::test_reservation_failure_propagates_before_audit |
| S0005 AC3 | corrections::test_replay…; migration unique constraints |
| S0005 AC4 | corrections non-correcting, stale and competing tests; migration::test_historical_decision_cannot_acquire_a_reservation |
| S0005 AC5 | corrections::test_learning_effects_are_zero |
| S0005 AC6 | provenance::test_ex_prov_002 (reservation reachable only inside authorized lineage); test_review_records_need_current_review_task_read |
| S0006 AC1 | migration::test_upgrade_preserves_legacy_rows_and_fabricates_nothing |
| S0006 AC2 | migration::test_downgrade_round_trip_when_empty_and_refusal_when_populated |
| S0006 AC3 | conformance (464 cases × 3 consumers); installed-package smoke; brain-contracts bundle test |
| S0006 AC4 | api::test_f0009_review_compatibility (exact route set, envelopes); existing test_reviews/test_facts |
| S0006 AC5 | EX-PROV-001–005 in provenance/temporal/corrections suites with QE-derived expected edges |
| S0006 AC6 | this plan + execution report; changed-line coverage ≥ 80%; G3 reviews |

## Entry and exit criteria

- **Entry:** G1 runtime preflight PASS; `brain_f0009` migrated to 0016.
- **Exit:** every listed test passes with zero skips; all regression lanes pass; changed executable-line coverage ≥ 80%; all four security scan classes have run.
