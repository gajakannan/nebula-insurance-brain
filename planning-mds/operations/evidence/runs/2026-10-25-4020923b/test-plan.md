# Test Plan — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

> QE-owned. Maps every F0005 acceptance criterion to the test that validates it. Live lanes run on the development host against the dedicated Brain vLLM server (RTX 5070, Phi-4-mini-instruct @ `cfbefacb…`), PostgreSQL 18 in Docker, real Docling 2.126.0 / RapidOCR 3.9.2. Offline lanes run in CI.

## Story-to-AC Mapping

| Story | AC | Lane | Test ID | Owner |
|-------|----|------|---------|-------|
| S0001 | AC1 lock/pin | preflight + live | G1 `uv sync --locked`; `pins` block of `artifacts/qualification/report.json`; `DOCLING_GRAPH_VERSION` guard | DevOps |
| S0001 | AC2 bundle identities | live + offline | `test_live_conversion_qualification.py::test_every_corpus_document_publishes_before_the_first_model_request` (OCR page count, pages and engine asserted on every manifest, round 2); `test_ocr_quality.py` (real conversions, v1 path; unidentified engine; handoff; contract validation) | QE |
| S0001 | AC3 checkpoint before model | live | same test (provider stopped at proxy: bundle ready, `model_unavailable`, 1 conversion, 0 provider requests) | QE |
| S0001 | AC4 partial conversion | live + unit | same test (gl-q-013 `partial`, failed page 2); empty-page rule in `docling_adapter.py` | QE |
| S0001 | AC5 stage guard | live subprocess + unit | `test_installed_stage_layout_mismatch_raises_before_extraction_and_registers_nothing`; `test_conversion_process.py::test_child_errors_are_stable_codes[stage_guard]` | QE |
| S0001 | AC6 audit | integration | `document_job_event` rows with reason (migration 0009) + `audit_event` authorization decisions; `test_job_event_reason_migration.py`, `test_queue.py` | Backend |
| S0001 | NFR 300 s bound | unit + live | `test_conversion_process.py` (hung, SIGTERM-ignoring, escaped helper, late completion, blocked staging, cancellation, orphan, PID reuse); `test_production_300_second_deadline_with_a_real_hung_child` | AI/Backend; QE/DevOps check |
| S0002 | AC1 provider faults | live + offline (`test_document_worker_reasons.py`, `test_vllm_graph_client.py` rejection records, `test_interpretation_rejections.py` H1) | `test_fault_injection_qualification.py::test_provider_fault_records_distinct_reason_and_resumes_from_saved_json[{stopped,http_5xx,malformed_json,schema_invalid,timeout}-{direct-baseline,graph-dense}]` | QE |
| S0002 | AC2 process kills | live subprocess | `test_worker_killed_at_each_point_recovers_with_single_effects[{bundle,run,import,imported}]` | QE |
| S0002 | AC3 storage failure | live + offline | `test_storage_failure_before_marker_is_never_ready_and_reconverts_at_most_once[1,2]`; launch-counted rule in `test_document_worker_reasons.py::test_failures_reconvert_at_most_once_and_terminal_reasons_never_retry` | QE |
| S0002 | AC4 duplicates/competing/cancel/concurrency | live subprocess + unit | `test_second_worker_is_refused_and_killed_holder_requires_confirmed_quiescence`; `test_cancellation_stops_scheduling_and_temporary_exports_are_removed`; `test_worker_guard.py` (20 cases); PostgreSQL queue fencing `brain-jobs/tests/test_postgres.py` | QE / Backend |
| S0002 | AC5 tenant/revocation | live | `test_revoked_grant_between_attempts_denies_audits_and_stops` | Security / QE |
| S0002 | AC6 temporary exports/retention scope | live | `test_cancellation_stops_scheduling_and_temporary_exports_are_removed`; conversion staging cleanup asserts in `test_conversion_process.py` | QE |
| S0002 | AC7 audit | integration | as S0001-AC6 | Backend |
| S0003 | AC1 saved JSON only | live | `test_live_reinterpretation_qualification.py::test_both_profiles_reinterpret_saved_json_with_zero_conversion` | QE |
| S0003 | AC2 evidence | live + harness | same test (fabricated = 0) and harness `evidence_check` per case | QE |
| S0003 | AC3 provenance retained | live | `test_both_profiles_reinterpret_saved_json_with_zero_conversion` asserts run files and that every ledger `doc_item_ref` resolves in the saved DoclingDocument (round 2) | AI / QE |
| S0003 | AC4 unsupported output | offline (deterministic) + live probe | `test_interpretation_rejections.py::test_relationship_output_fails_closed_with_no_assertions[direct-baseline,graph-direct]`; live `test_relationship_output_fails_closed_with_no_rows` | QE |
| S0003 | AC5 budgets | live + offline | reinterpretation test (`max_reserved_tokens ≤ 4096`); report `over_budget_calls`; `test_vllm_graph_client.py` | QE |
| S0003 | AC6 targeting | live | `test_targeted_request_fails_before_any_model_call` | QE |
| S0004 | AC1 corpus | corpus author session | `artifacts/qualification/corpus-author-report.md` (hashes recorded 2026-10-25T23:40, before any measured run) | QE (corpus author) |
| S0004 | AC2/AC3 report & thresholds | live harness | `neuron/benchmarks/f0005_qualification.py` → `artifacts/qualification/report.json`, `report-summary.md` | QE / AI |
| S0004 | AC4 verdicts | review sessions | independent QA / Architect / Security sessions (G3) | QA, Architect, Security |
| S0004 | AC5–AC7 activation/rollback/rejection | live + offline | `test_pipeline_selection.py` (committed default, unknown values, no env override, guard override rejection, legacy meaning, live decision branches) | Backend |
| S0005 | AC1 origin | live + unit | `test_ocr_asset_provenance.py`; live conversion test (OCR producers per page in v2 records) | AI |
| S0005 | AC2 asset identity | unit + live | `test_ocr_asset_provenance.py` (pins = installed bytes; altered digest / unresolvable → no identity); live manifests carry 3 pinned digests | AI / QE |
| S0005 | AC3 fallback + rate | live | live conversion rows (`contract` per document); report `bundle_contract` per case | QE |
| S0005 | AC4 consumers | integration + live | F0004 consumer suites (`test_content_consumer_versions.py`, `test_content_worker_v2.py`, `test_content_restore_v2.py`); harness importer/evidence reads over corpus v2 bundles | QE |
| S0005 | AC5 switch | gated | only after operator acceptance (G4) | PM / Operator |

## Test Strategy

- **Unit (developer-owned):** `brain-ingestion/tests/test_conversion_process.py`, `test_worker_guard.py`, `test_ocr_asset_provenance.py`; `brain-jobs/tests/test_queue.py`; `test_vllm_graph_client.py`.
- **Integration (QE-owned):** PostgreSQL migration/restore (`engine/tests/integration/test_job_event_reason_migration.py`), PostgreSQL queue fencing, existing F0004 consumer suites, offline recovery (`test_document_process_recovery.py`).
- **Live qualification (QE-owned, opt-in `BRAIN_RUN_LIVE_QUALIFICATION=1`):** conversion, fault injection, reinterpretation, pipeline selection, and the measured harness. Every engine uses an isolated PostgreSQL schema, content root and hashed temporary config, and shares the fixed host guard.
- **E2E / API / Accessibility:** not applicable. F0005 has no UI or endpoint.

## Developer-vs-QE Test Ownership

The AI and Backend implementation sessions own the unit tests and the supervised-conversion and guard negative controls. QE owns the live suites, corpus scoring and the report. The corpus author session owns the corpus and its expectations: it never ran or read extraction code. Independent review sessions judge the evidence; they did not author it.

## Test Data / Fixtures

- Synthetic qualification corpus `neuron/fixtures/qualification/`: 13 documents (6 native, 4 scanned, 2 mixed, 1 partial), 65 field expectations, corpus hash `fbc5e263…`, expectation-set hash `16a29d67…`.
- Service principal with `ServicePrincipal` grant, seeded per isolated schema with the F0002 fixtures. The policy release comes from `planning-mds/security/policies`.
- Real PostgreSQL 18 (`brain-postgres`), real filesystem object store per test, and the real vLLM provider. The fault proxy is the only test double in the live lanes.

## Happy / Edge / Error / Auth / Accessibility / Regression Cases

- **Happy:** all corpus documents convert and both profiles run under each engine.
- **Edge:** partial page, scanned-only pages, mixed image regions, split values, absent fields, repeated values.
- **Error:** connection refused, ambiguous timeout, HTTP 5xx, malformed JSON, schema-invalid JSON, storage write failure before the marker (once and twice), stage-layout mismatch, unsupported relationship output, targeted request, hung/term-ignoring converters, PID reuse, marker fsync failure.
- **Auth:** grant revocation between attempts; tenant/KB scoping of sources, runs and bundles.
- **Regression:** G1 baseline (40 tests), full neuron suite, brain-jobs suite.
- **Round 2 (G3 rework):** `test_ocr_quality.py`, `test_interpretation_rejections.py`, rejection-record and reason cases, provider-record tampering, migration 0010 expand/downgrade, the busy-provider timeout mode (`fault_proxy.busy_at`) and decision branches asserting engine identity regardless of outcome.

## Risks And Mitigations

- **Synthetic bias** (agent-authored corpus): independence by construction plus reviewer verdicts. The residual risk is recorded and F0026 owns real-corpus acceptance.
- **Pre-existing environment drift:** `test_content_worker_v2.py::test_publication_import_and_second_profile_reuse[False]` fails on HEAD with the original adapter files, because Docling merges two lines of that fixture into one item on this host. It is not introduced by F0005. Logged for follow-up.
- **Provider restarts during qualification** touch the shared development server. They use the recorded command only, and a restart receipt is recorded for each.

## Result

PASS — plan complete; execution results are in `test-execution-report.md`.
