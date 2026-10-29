# Coverage Report — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

> QE-owned. Policy floor: 80% of changed runtime scope (severity profile `standard`).
>
> - **Measured:** round 3 (2026-10-28, final code), on the offline lanes only. Round 2 measured 83.1% over 1,291 lines.
> - **Not instrumented:** the live lanes, so the figures understate what the live suites exercised.
> - **Round 1** measured 82.0% over 1,123 lines; its XML was replaced by round 2.

## Coverage Target And Actual Per Layer

| Layer | Scope | Changed executable lines | Covered | Coverage | Floor |
|---|---|---|---|---|---|
| Engine (`brain_jobs`, `brain_content`) | changed lines in `queue.py`, `config.py`, `manifest.py` | 101 | 88 | 87.1% | 80% |
| Neuron (`brain_ingestion`, `brain_extraction`, `brain_interpretation`) | changed lines in 17 modules (4 new files counted whole) | 1,301 | 1,083 | 83.2% | 80% |
| **Total changed runtime scope** | | **1,402** | **1,171** | **83.5%** | **80%** |

Whole-package line coverage, for context: neuron packages 84% (`TOTAL 2492 / 400 missed`).

### Per file (changed lines)

| File | Kind | Changed lines | Covered | Coverage |
|---|---|---|---|---|
| `engine/packages/brain-content/src/brain_content/config.py` | modified | 32 | 32 | 100.0% |
| `engine/packages/brain-content/src/brain_content/manifest.py` | modified | 19 | 14 | 73.7% |
| `engine/packages/brain-jobs/src/brain_jobs/queue.py` | modified | 50 | 42 | 84.0% |
| `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_pipeline.py` | modified | 4 | 3 | 75.0% |
| `neuron/packages/brain-extraction/src/brain_extraction/graph_interpretation.py` | modified | 66 | 63 | 95.5% |
| `neuron/packages/brain-extraction/src/brain_extraction/openai_compatible_adapter.py` | modified | 6 | 6 | 100.0% |
| `neuron/packages/brain-extraction/src/brain_extraction/pins.py` | new | 2 | 2 | 100.0% |
| `neuron/packages/brain-extraction/src/brain_extraction/vllm_graph_client.py` | modified | 62 | 62 | 100.0% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/bundle_writer.py` | modified | 6 | 6 | 100.0% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/content_projection.py` | modified | 1 | 1 | 100.0% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/content_workflow.py` | modified | 26 | 11 | 42.3% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/conversion_process.py` | new | 345 | 266 | 77.1% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/docling_adapter.py` | modified | 40 | 35 | 87.5% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py` | modified | 130 | 120 | 92.3% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/item_provenance.py` | modified | 75 | 68 | 90.7% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/provider_supervisor.py` | new | 116 | 84 | 72.4% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/submission.py` | modified | 9 | 8 | 88.9% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/worker_cli.py` | modified | 73 | 47 | 64.4% |
| `neuron/packages/brain-ingestion/src/brain_ingestion/worker_guard.py` | new | 334 | 295 | 88.3% |
| `neuron/packages/brain-interpretation/src/brain_interpretation/parsed_content.py` | modified | 6 | 6 | 100.0% |

## Raw Artifact Paths

- `artifacts/coverage/neuron-coverage.xml` — neuron full suite with subprocess measurement enabled through `artifacts/coverage/neuron.coveragerc` (`patch = subprocess`), so the supervised converter child and CLI subprocess tests are counted.
- `artifacts/coverage/engine-coverage.xml` — engine full suite.
- `artifacts/coverage/changed-line-coverage.md` — the changed-line computation: git diff hunks for modified files, whole file for new files, executable lines from the coverage XML.
- `artifacts/test-results/g2r3-neuron-full.log` and `artifacts/test-results/g2r3-engine-full.log` — the runs that produced the XML.

## Feature-Scoped Notes

- **Files below the floor:**
  - `conversion_process.py` (77%), `provider_supervisor.py` (70%) and `worker_cli.py` (64%) contain deadline, SIGKILL fallback, quiescence/restart and CLI exit paths. Only the live 300 s deadline, kill-point and competing-worker lanes reach them, and those run uninstrumented and passed in round 2.
  - `content_workflow.py` (42%): the supervised-conversion handoff runs only with real Docling in a child process; it is covered by the live conversion lane.
  - `engine/.../manifest.py` (74%): the new `OcrQuality` validator is exercised by `neuron/packages/brain-ingestion/tests/test_ocr_quality.py`, which the engine-only coverage run does not include.
- **G3 rework tests (48 new neuron cases, plus engine migration 0010):**
  - `test_ocr_quality.py`: C1, with real conversions on the v1 path;
  - `test_interpretation_rejections.py`: H1 dense fallback and budget rejection, S0003-AC4, baseline prompt identity;
  - additions to `test_vllm_graph_client.py`: rejection records;
  - `test_document_worker_reasons.py`: M1/M2/M3 and the new reasons;
  - `test_worker_guard.py`: SEC-F5-L1 record validation and unauthenticated restart;
  - `test_job_event_reason_migration.py`: 0010 expand and downgrade guards.
- **The pre-existing failing tests** (11 engine authx; `test_content_worker_v2[False]`) do not touch F0005 lines.

## Waiver Block

None. The changed runtime scope exceeds the 80% floor in both layers.

## Result

PASS
