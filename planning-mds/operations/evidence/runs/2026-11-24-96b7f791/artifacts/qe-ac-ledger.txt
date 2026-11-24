# F0011 acceptance-criterion evidence ledger

Owner: Codex / Quality Engineer
Run: 2026-11-22-885e8734
Date: 2026-11-23

The 41 criteria below are the feature-local story criteria. This ledger records
observed runtime proof; independent G3 judgments, G4 approval and PM closeout
remain separate. Synthetic development cases never establish business authority
or model accuracy. All artifact names below are relative to this run.

Evidence keys:

- UNIT: `artifacts/test-results/python-unit-final.xml` (1237 passed, no skips).
- INT: `artifacts/test-results/consumer-integration-ci.xml` (real owned PostgreSQL databases; final consumer verification).
- CASE: `artifacts/test-results/conformance-review-final.json` (443 cases, 1329 actual Python/source-gated Pydantic/AJV results, zero mismatches), with independently authored expectations in `scripts/contracts/cases.json`.
- JS: `artifacts/test-results/js-review-unit-final.tap` (19 passed).
- GEN: `artifacts/test-results/generation-final.txt` and UNIT's `scripts/contracts/tests/test_artifact_reproducibility.py`.
- INSTALL: `artifacts/install-final/installed-distribution-results.json` (wheel and sdist; fresh environments, no network, source checkout absent).
- NATIVE: `artifacts/test-results/native-baseline-ci-results.json`, `native-candidate-ci-results.json`, and `native-differential-ci-comparison.txt`.
- HISTORY: signed initial `stored-versions-{integration,dev}.json` and final `stored-versions-{integration,dev}-cutover-ci.json`, under `artifacts/test-results/`.

| Criterion | Observed test / evidence and boundary | Runtime result |
|---|---|---|
| F0011-S0001-AC1 | UNIT `test_installed_bundle_resource_count_and_identity`, `test_closed_registered_relative_refs_and_escaped_pointers`; GEN verifies 21 identities and reference closure. | covered |
| F0011-S0001-AC2 | G0 `artifacts/diffs/g0-resource-mappings.json` and `g0-mapping-check.txt`; UNIT `test_bundle_corruption_never_exposes_partial_registry` rejects duplicated identity/hash claims. Operational sources.yaml reconciles now-existing paths. | covered |
| F0011-S0001-AC3 | UNIT `test_schema_failures_are_closed_before_any_instance`, unsupported-version/ref selectors; JS closed reference/unsupported vocabulary cases. Dormant unresolved refs are checked before instances. | covered |
| F0011-S0001-AC4 | UNIT schema annotation/type/format admission, detached metadata and `test_portable_formats_are_explicit_and_consistent`; JS metadata parity; CASE executes 29 keywords and four formats. Metadata grants no authority. | covered |
| F0011-S0001-AC5 | UNIT `test_detached_source_and_metadata_no_defaults_or_coercion`, generated-model round trips, JS no mutation/default/coercion assertions; CASE closed additional properties and opaque open data. | covered |
| F0011-S0001-AC6 | UNIT bundle corruption/admission and `test_errors_never_contain_instance_values`; API startup corruption and generic output failures. Errors expose fixed codes/trusted schema coordinates only. | covered |
| F0011-S0001-AC7 | INSTALL both actual distributions in fresh nonroot environments, no checkout/network; GEN hash manifest and commands.log; JS installed resources. No business mutation from validation/generation. | covered |
| F0011-S0002-AC1 | CASE nine state fixtures and INT `test_s0003_ac1_all_nine_states_are_accepted` at the actual answer boundary. | covered |
| F0011-S0002-AC2 | CASE state/value mismatch and invalid-state/null cases; INT `test_s0003_ac2_state_value_mismatch_writes_no_version`, unknown state refusals. | covered |
| F0011-S0002-AC3 | CASE scope page/block bounds and required shape; INT `test_s0003_ac3_absence_scope_required_and_owned` checks actual source ownership. | covered |
| F0011-S0002-AC4 | CASE absent/empty/duplicated selections, invalid UUID, omitted release, scope forbidden for NOT_PROCESSED/NOT_APPLICABLE. | covered |
| F0011-S0002-AC5 | Existing EX-OWN-002/003 and glossary links in examples/README; INT `test_s0003_ac5_ex_own_003_three_kinds_of_no_value` compares actual scoped no-value outcomes; CASE preserves independent structural expectations. | covered |
| F0011-S0002-AC6 | CASE rejects ACCESS_DENIED state; INT `test_s0003_ac6_unreadable_scope_is_denied_before_any_explanation`, `test_s0003_ac6_reads_never_expose_a_scope_the_reader_cannot_read`. | covered |
| F0011-S0002-AC7 | CASE distinguishes temporal validity-unknown from information state; INT actual F0008 temporal reader and source/ownership/evidence checks. Structural accept never substitutes for these checks. | covered |
| F0011-S0003-AC1 | CASE exact/scientific notation/length money; UNIT `test_canonical_decimal_is_exact`, bounded canonical round trips; source-gated generated serialization retains original lexical precision/currency. | covered |
| F0011-S0003-AC2 | CASE decimal and malformed/missing/type fixtures; INT `test_s0004_ac2_exact_decimal_canonical_form_and_round_trip` and numeric canonical boundary proof. | covered |
| F0011-S0003-AC3 | UNIT `test_money_rules_in_order`; INT `test_s0004_ac1_basis_required_where_the_predicate_requires_it`, `test_s0004_ac1_ac3_money_rejections`. Unsupported currency/wrong basis remain domain refusals. | covered |
| F0011-S0003-AC4 | CASE identifier required/type/date/length fixtures; actual domain identifier tests and INT `test_s0004_ac4_ac5_identifier_values`. | covered |
| F0011-S0003-AC5 | CASE source-gated round trips and UNIT `test_identifiers_are_scheme_scoped_and_normalized_per_type`; INT issuer-change versus equivalence check. Equal strings under different schemes/types remain different. | covered |
| F0011-S0003-AC6 | Same domain/INT tests verify normalized_value and reversed effective interval; CASE deliberately separates structurally valid data from invalid normalization/ordering. | covered |
| F0011-S0003-AC7 | Independently authored case notes plus UNIT `test_money_rules_in_order`, identifier/domain refusals; converted money without provenance and bare identifiers refused. Extreme exponents use memory-bounded regression proof. | covered |
| F0011-S0004-AC1 | CASE uses real JSON Schema, generated/source-gated Pydantic and AJV; versions and every case result recorded. No consumer replaced by a mock. | covered |
| F0011-S0004-AC2 | CASE behavior_coverage: 21 source conditionals, 79 executed branch witnesses, 66 behavior entries, 29 validation keywords and all four formats. Behavior map is checked against actual schemas/instances. | covered |
| F0011-S0004-AC3 | CASE 1329/1329 matched; UNIT `test_case_join_refuses_missing_duplicate_or_changed_results` rejects incomplete, duplicate and incorrect expected/results; runner crashes return failure. | covered |
| F0011-S0004-AC4 | UNIT parametrized `test_generated_source_gated_case` runs all cases; `test_a_lossy_or_hand_edited_model_cannot_be_accepted`, `test_explicit_null_absence_and_open_payload_keys_survive`; CASE exact round trips. | covered |
| F0011-S0004-AC5 | GEN builds self-contained OpenAPI from same source definitions; UNIT `engine/apps/api/tests/test_contract_openapi.py` checks actual route parity/ref closure/snapshots; deliberate drift refused. | covered |
| F0011-S0004-AC6 | GEN source-derived ui-metadata and generated SOURCE_METADATA; UNIT detached metadata and JS exact metadata/source comparison. All eight allowed annotations preserved; unsupported annotations refused. | covered |
| F0011-S0004-AC7 | UNIT `test_check_refuses_tampered_generated_artifact_without_writing`, bundle hash corruption, `test_case_join_refuses_missing_duplicate_or_changed_results` explicit expected-result mutation and canonical-seed tampering. No payload content in result summaries. | covered |
| F0011-S0005-AC1 | G0 raw inventory reconciles 21 resources and 68 mappings; sources.yaml records each adopt/delegate/retained boundary, profile and explicit selector. | covered |
| F0011-S0005-AC2 | UNIT actual content/assertion readers and Neuron's eight shared-bundle integration tests; INT actual normalized FactSlot/answer/temporal/API consumers. Standalone conformance is supporting proof only. | covered |
| F0011-S0005-AC3 | UNIT existing F0006 dispatch tests; NATIVE seven exact old/candidate comparisons including disabled v2, unknown version, malformed v2 and legacy path. No failed-reader fallback. | covered |
| F0011-S0005-AC4 | INT actual F0007/F0008 regressions and legacy path; HISTORY complete real environment sweeps passed before activation, then again at cutover. Actual databases have zero stored versions; owned PostgreSQL tests separately cover nonempty legacy/temporal/closed/remainder history. | covered |
| F0011-S0005-AC5 | INT `test_result_contract_failure_rolls_back_slots_and_qualifiers`, normalized/serialized-commit failure tests verify slots/qualifiers/versions/changes/outbox with fresh authoritative reads; existing refusal audit tests remain passing. | covered |
| F0011-S0005-AC6 | INT source READ/tenant/KB/evidence/domain-order and PR-L3 fault injection prove actual ordering. Authorized read audit SUCCEEDED can precede generic delivery-invariant500; denied source404 precedes guard. Security accepted PR-L3 at G3 (security-review-report.md, Recommendation Disposition). | covered |
| F0011-S0005-AC7 | Diff has no migration/source schema/producer activation changes; HISTORY uses database-enforced READ ONLY snapshots, no cleanup; existing dev restored only through already-shipped0015. Neuron smoke makes no model call or PDF reparse. | covered |
| F0011-S0006-AC1 | docker/contracts/README, CI workflow, commands.log, exact locked versions; clean Docker engine/Node verification, full UNIT/INT/CASE/Neuron and INSTALL results. See DevOps report for precise image/source provenance. | covered |
| F0011-S0006-AC2 | GEN86 byte-exact artifacts; UNIT reproducibility, missing/tampered output, failed-publication rollback and nonroot-readable permissions tests. | covered |
| F0011-S0006-AC3 | INSTALL real wheel/sdist under network-none and hidden checkout; headless JS source/ref closure tests and clean Node image execute same443 cases. No planning path at runtime. | covered |
| F0011-S0006-AC4 | examples/README F0011 carry-in links glossary/EX-GL-001/EX-OWN and owning stories/contracts; original74 plus imported102 frozen expectations tracked by case-provenance.json; additional187 behavior cases independently authored synthetic development data. CASE validates structured expectations. | covered |
| F0011-S0006-AC5 | This41-row ledger, actual final counts and coverage-report.md/changed-line-coverage.json. Build/readiness checks not substituted for runtime or ADR acceptance. | covered |
| F0011-S0006-AC6 | GETTING-STARTED.md and docker/contracts/README describe source authority, subset, profiles, retained readers, adoption, regeneration and coherent rollback; generation has artifact audit only. ADR0079/0039 remain Proposed, display/completeness belongs to later owners. | covered |

All final evidence keys must resolve before G2 passes. Earlier failed attempts
remain historical evidence; only the final passing executions above support this
runtime assessment. This ledger does not accept PR-L3 or approve the feature.
