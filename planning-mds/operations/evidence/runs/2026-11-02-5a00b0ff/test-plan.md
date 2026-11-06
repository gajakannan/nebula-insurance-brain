# F0006 Test Plan

- Run: `2026-11-02-5a00b0ff`
- NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`
- Owner: Codex / Quality Engineer
- Scope: five local stories, 35 acceptance criteria; approved assembly plan including correction-basis/persistence rework.
- Status: complete; all 35 ACs have observed mapped proof and final source-bound execution/coverage evidence is recorded in test-execution-report.md and coverage-report.md.

## Test Strategy

Use developer-owned pure contract/admission/normalization/eligibility tests for
exhaustive deterministic cases, then independent PostgreSQL tests for durable
claims, immutable evidence, scoped references, concurrency and current review /
commit integration. Existing authenticated HTTP, authorization, review, temporal,
persistence and worker-recovery suites protect the legacy boundary. An injected
failure at review insertion must roll back the whole claim/name/evidence effect;
replay must retain one logical effect.

All application validation executes in the run's application containers using
[artifacts/runtime/compose.yaml](artifacts/runtime/compose.yaml). PostgreSQL cases create fresh `f0006_qe_*`
databases and override the parent integration cleanup fixture; they do not
truncate or downgrade historical `brain`. The restricted SQL-role test grants
access only in its throwaway test database and cleans up its temporary role.

The canonical floor is `coverage_min_pct` from the active feature evidence
contract. Distinguish the measured assertion-surface denominator from coverage
of added/modified lines in shared consumers; do not infer one from the other.

## Source Fixtures and Limits

`engine/tests/fixtures/assertions/{harness.py,native-sources.json}` contains
independently authored synthetic development expectations, outside the frozen
holdout. The fixture publishes retained immutable source snapshots through the
existing authorized content publisher. Non-PDF cases retain their DOCX/XLSX/CSV
original assets and explicit native locators alongside a synthetic PDF rendition
required by the current F0004 bundle contract. No actual conversion, OCR,
extraction-quality or production-qualification proof is claimed. Admission tests
read those stored snapshots and never invoke a model or conversion pipeline.

The declared time-reference resolver in tests is a trusted scoped fixture port.
Its positive snapshot and foreign-reference rejection do not implement the future
F0016 time-mention store, resolver or lifecycle. Open/mood/described restrictions
remain independent; a genuine quote with a misread number must survive grounding
without becoming semantic truth.

## Test File Key

| Key | Product-relative test source |
|---|---|
| A | `engine/tests/integration/test_assertion_admission.py` |
| C | `engine/tests/integration/test_assertion_consumers.py` |
| M | `engine/tests/integration/test_assertion_migration.py` |
| O | `engine/tests/integration/test_assertion_ownership.py` |
| U | `engine/packages/brain-assertions/tests/test_admission.py` |
| K | `engine/packages/brain-assertions/tests/test_contracts.py` |
| N | `engine/packages/brain-assertions/tests/test_normalization.py` |
| E | `engine/packages/brain-assertions/tests/test_eligibility.py` |
| X | `engine/packages/brain-security/tests/test_execution.py` |
| R | `engine/packages/brain-review/tests/test_decisions.py`; existing `engine/apps/api/tests/test_reviews.py` and `test_facts.py` |
| I | `neuron/tests/integration/test_document_process_recovery.py` |
| P | `engine/tests/integration/test_assertion_authority_projection.py` |

## Acceptance Criteria Mapping

The following maps requirements to concrete assertions rather than equating test
counts or coverage with acceptance.
[g3-sec04-regression.xml](artifacts/test-results/g3-sec04-regression.xml)
contains 306 passing cases, including 157 feature cases with the mapped acceptance-gap
additions, ownership matrix and page/bbox INSERT-integrity regression. The focused
17-case migration and 25-case discovery/consumer executions overlap this final run.
P observes actual SQL projection boundaries for all source-discovery entry points
and denies payload reads for unauthorized/unproved callers or corrupt lineage.
Existing consumer, review-service and worker recovery artifacts are itemized in
test-execution-report.md. Coverage is assessed separately in coverage-report.md.

| Story / AC | Required observation | Concrete tests / evidence path |
|---|---|---|
| S0001 AC1 | Complete typed record and actor/time survive a fresh session | A `test_typed_competing_claims_reload_without_canonical_effects`; `test_dimensions_round_trip_independently_with_confidence_boundaries` |
| S0001 AC2 | Separate $5M/$10M sources retain separate claims and evidence; no facts | A `test_two_sources_retain_five_and_ten_million_claims` |
| S0001 AC3 | All independent mode/origin/basis values round-trip; unknowns have zero effects | A `test_dimensions_round_trip_independently_with_confidence_boundaries`; `test_invalid_dimensions_and_confidence_have_zero_claim_effects` |
| S0001 AC4 | Confidence boundaries and inherited INFERRED/AMBIGUOUS basis | A dimension/bad-confidence cases; C `test_v2_correction_preserves_basis_and_owns_new_evidence` |
| S0001 AC5 | Unauthorized and cross-tenant/KB run/ref/correction/evidence writes denied | A `test_unauthorized_producer_and_cross_scope_context_have_no_claim_effects`; O `test_composite_foreign_keys_reject_cross_scope_claim_links`; X source-denial/audit cases; P denied internal read and metadata-only discovery |
| S0001 AC6 | Corrections append; original claim/evidence cannot be overwritten | C correction-basis/mood cases; M `test_original_assertions_extensions_and_evidence_are_immutable`; `test_inserted_evidence_page_and_bbox_must_match_server_snapshot` and `test_matching_evidence_carriers_accept_honest_and_absent_regions` |
| S0001 AC7 | Real PostgreSQL round-trip/ownership/correction proof using retained sources | A/C/M/O suites; fixture harness uses published source bytes without conversion/OCR execution |
| S0002 AC1 | Open source wording, ENTITY/literal object and time refs survive reload | A `test_open_storage_and_replay_are_lossless`; `test_declared_entity_object_and_time_reference_survive_reload` |
| S0002 AC2 | Open null predicate/EXPLICIT/quote/reference constraints reject invalid items | K authored `open-predicate`, `open-inferred`, `empty-quote` cases; U unknown subject; A invalid-dimension cases |
| S0002 AC3 | Typed release/property required; open has no invented vocabulary | K authored `typed-no-release` and `open` cases; A open storage reload |
| S0002 AC4 | New strict schema preserves semantics alongside unchanged legacy payload | K `test_authored_contract_shape_expectations_and_packaged_schema_equality`; `test_v2_result_dispatch_and_legacy_behavior` |
| S0002 AC5 | Unsupported versions and old-reader v2 refusal happen before effects | K `test_every_other_explicit_version_is_unsupported`; `test_explicit_v2_is_refused_by_legacy_reader_before_shape_validation`; I v1 importer recovery |
| S0002 AC6 | Fixture open storage has no model/alignment/conversion; canonical use blocked | A open storage; C `test_independent_restrictions_prevent_canonical_effects[open]`; E independent guards |
| S0002 AC7 | Scoped/dangling entity/object/time/source references and actor identity | A positive ENTITY/time and `test_foreign_time_reference_fails_without_claim_effects`; U unknown/foreign source cases; O tenant/KB FK matrix |
| S0003 AC1 | Deterministic Unicode/spacing/hyphen mapping; absent quote rejected | N normalization/original-range cases; U `test_all_structural_failures_and_partial_outcomes_survive` |
| S0003 AC2 | Introducing-name and document name-ownership failures stay distinct | U simultaneous structural failures; A `test_name_conflict_does_not_reserve_failed_references`; `test_concurrent_document_name_claims_have_one_owner` |
| S0003 AC3 | Bad time words / missing subject rejected; undeclared object retained as signal | U `test_all_structural_failures_and_partial_outcomes_survive`; `test_unknown_subject_and_time_are_not_dropped_silently`; `test_undeclared_named_object_is_retained_as_literal_signal` |
| S0003 AC4 | Malformed/truncated/uninterpreted output keeps valid sibling items | A `test_partial_output_keeps_valid_siblings_and_explicit_outcomes`; U partial-batch and all-failures cases |
| S0003 AC5 | Typed protected outcomes retain reason/path/raw hash/model/prompt and partial obligation | U all-failures/raw-hash cases; K protected admission-result schema; A partial-result persistence boundary |
| S0003 AC6 | Four native locator types, repeated/multiregion/coarse evidence; no model offsets | A `test_native_formats_derive_locations_from_verified_stored_content`; N repetition, cell, casefold and coarse/unresolved cases; C new-locator correction |
| S0003 AC7 | Genuine $500K quote with misread $5M value passes grounding without truth claim | U `test_genuine_quote_keeps_misread_value_without_claiming_semantic_truth` |
| S0003 AC8 | Deny before protected reads, zero rejected-claim/canonical effects | U `test_foreign_evidence_is_rejected_before_the_source_port`; source-auth error propagation; A denied/cross-scope writer; O backstops; P all discovery/denied-payload/corrupt-lineage cases |
| S0004 AC1 | Mood words retained; confidence/mode/review cannot clear canonical restriction | A mood/open reload; E `test_supplied_mood_cannot_be_cleared_by_confidence_mode_or_review`; C mood rejection |
| S0004 AC2 | Subjectivity/offered/warranty/conditional cases remain restricted | E parametrized source-word mood cases; C supplied mood and independently restricted canonical attempts |
| S0004 AC3 | Policy's operative term can be accepted without asserting its embedded premise | C `test_operative_policy_terms_do_not_establish_the_embedded_condition`; E qualified operative support |
| S0004 AC4 | DESCRIBED support requires review and cannot auto-accept/close/supersede | A actual DESCRIBED origin; C described refusal and `test_reviewed_described_initial_use_cannot_close_or_supersede`; E described/mixed support |
| S0004 AC5 | OCR/transcribed confidence retained; unknown/unqualified is not promoted | A actual-origin parameters; E `test_unknown_origin_and_unresolved_support_keep_review_restrictions`; mixed unqualified/unresolved parameters |
| S0004 AC6 | Internal read/review keeps restrictions; unauthorized errors disclose no quote | A fresh read/open record; C correction-basis/mood/source-proof cases and `test_http_source_denial_precedes_sanitized_eligibility_error`; X combined authorization audits |
| S0005 AC1 | Current v1 import and recovery retain one logical claim/review/evidence effect | I `test_process_recovery_delivers_one_reviewed_assertion`; K legacy DTO behavior; M before/after legacy identity |
| S0005 AC2 | Raw legacy origin and correction provenance survive additive migration | M `test_additive_upgrade_preserves_legacy_identity_and_empty_rollback`; existing persistence full-review round-trip and R original-claim immutability |
| S0005 AC3 | Existing authenticated correction, stale/duplicate and evidence/audit behavior | Existing API reviewer correction/duplicate/authority tests; R `test_stale_assertion_version_is_recorded_stale_and_opens_a_new_item`; C v2 basis/evidence/correction tests |
| S0005 AC4 | Typed legacy commit retained; open/mood/described and mixed lineage refused before effects | Existing API fact round-trip; C independent restrictions, mixed/unknown/direct-caller, correction ancestry and described-close cases |
| S0005 AC5 | Cross-scope/revoked/malformed cases retain zero unauthorized effects and protected errors | O ownership/service-role cases; A denied producer; X foreign/revoked/expired source checks; C invalid correction, copied/expired proof and HTTP 404-before-422 cases |
| S0005 AC6 | Atomic claim/name/evidence/review rollback and one-effect retry; rollback guard | A review-insert fault/retry and replay; M occupied-downgrade refusal; I worker recovery matrix |
| S0005 AC7 | Independent synthetic expectations, PostgreSQL/current consumers and measured coverage | All mapped sources; fixture provenance above; execution/coverage reports and raw XML/JSON artifacts. Default/policy boundaries reviewed separately; no production activation or frozen evaluation claimed. |

## Required Evidence and Completion

Produce JUnit XML for the final feature, existing-consumer, review-service and
worker-recovery runs, plus machine-readable coverage and the executed commands.
Security's four scan classes are executed by parent orchestration and interpreted
by the Security Reviewer; dependency findings must not be silently labelled clean.
UI/component/accessibility/visual tests are not in scope because this feature has
no UI change. Admission performance has no invented latency SLO; elapsed times
are observations only. QE signs off only after final artifacts resolve the mapped
ACs and coverage scope, with no fabricated operator approval.


## QE Final Assessment

Reviewed by Codex / Quality Engineer at 2026-11-03T23:08:19+00:00. Final engine evidence is 306 passing cases (157 feature cases); earlier focused suites overlap that run. The clean current importer lane passes 15 cases, and the separate SQLite/PostgreSQL recovery artifacts cover all five crash points on each database. Changed executable-line coverage passes the active contract floor without waiver. The supplemental unchanged actual-OCR worker rerun also passes all five cases with explicit PostgreSQL configuration and bounded threads. Framework evidence-parser regressions pass 45 cases separately from product counts. See test-execution-report.md for final evidence and the preserved earlier error/termination/skip and page/bbox red/fixture-repair history. SEC-04/A-IMPL-02 metadata-only discovery is repaired and independently checked by nine new actual-SQL PostgreSQL tests; source proof/current READ precedes protected payload loading.
