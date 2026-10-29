# Self Review — F0005-one-time-docling-ingestion run 2026-10-25-4020923b

> Implementation self-review by the Backend, AI Engineer, QE and DevOps roles. The Architect check confirms the output against assembly-plan Steps 0a–7, and the Architect role made the contract decisions. Independent reviewers judge this at G3. Nothing here is a reviewer verdict.
>
> **Round 2 (2026-10-27).** Round 1's G3 failed: Code Review REJECTED (C1 critical, H1 high). At G4 the operator chose: fix C1 and H1; apply the Medium fixes (M1–M6, SEC-F5-L1–L3, the Architect baseline finding); add a controls ADR; re-run the kill lane; upgrade pypdf; then re-gate with fresh reviewers. This review covers both rounds.

## Round 3 Addendum (2026-10-28, after G4 round 2)

The operator approved closing on the rejection branch and ordered these fixes before closeout:
- **N1:** the conversion budget is checked before each launch.
- **SEC-F5-L5:** a refused restart stops its own server and keeps its refusal code.
- **SEC-F5-L4:** listener ownership is required when recording, before any signal, and before the credential is sent on restart. The provider log is 0600. The program-name check stays name-based (stated in ADR-0074).
- **SEC-F5-L6:** litellm 1.100.4.
- **Code Review L-N1–L-N4:** pypdf errors degrade to a warning; token-counter failures are recorded rejections; uncleared or leftover markers and usage beyond the reservation stop the worker.
- **Code Review round-1 L3:** boot id in receipts, failing closed if it is unreadable.
- **Architect Lows:** explicit legacy pipeline metadata; the stage guard comes from `brain_extraction.pins`; the RapidOCR import guard; the competing-worker recovery bound.
- **QA Lows:** exact assertions; `report_version` 2; timing margins; the neuron HEAD baseline.
- `# WHY:` tags.
- **ADR text:** ADR-0073 §6 (incompatible add-only change, deployment rules, OCR-count meaning, restore-drill proof gate), ADR-0060 consistency and hashes, ADR-0074 aligned and **Accepted**.

The independent delta review (`delta-review-report.md`) approved with recommendations, confirming N1 and L5 verified. Its D-1–D-5 Lows were fixed. One regression from D-1 (a hidden `model_timeout`) was caught live and fixed.

Final evidence:
- offline: neuron 260 / engine 424 passed, with only the pre-existing failures;
- coverage: 83.5% changed-line;
- all seven live lanes pass;
- the post-decision check passes;
- containers rebuilt; smoke and four scans re-run.

**Not done (recorded):**
- the queue-race orphan sweep (ADR-0074 known limitation);
- a minimal restart environment (ADR-0074, open before activation);
- converter OS isolation SEC-F5-M1 (activation precondition);
- the OCR-bearing restore drill (ADR-0073 proof gate).

## Scope Review

The implementation follows the approved assembly plan (Phase B, plan run `2026-10-25-50fcf658`) on branch `feature/f0005-live-qualification`, based on `plan/f0005-one-time-docling-ingestion` @ `3d99ceb`. Nothing is committed yet.

| Plan step | Delivered | Main paths |
|---|---|---|
| 0a Host singleton / provider recovery | flock guard per canonical endpoint; durable in-flight marker; provider record **validated when written, when used and before any signal** (`vllm serve` leader, guarded host/port, no `--api-key`); quiescence that also requires unauthenticated requests to be refused after restart; a marker-infrastructure fault stops the worker without failing jobs | `worker_guard.py`, `provider_supervisor.py`, `document_worker.py`, runbook |
| 2 Live conversion (S0001) | supervised conversion process group (300 s deadline, latch, receipts, TERM→KILL→reap, orphan reaper); empty or unreadable pages → failed pages/`partial`; **observed OCR pages and the pinned engine identity recorded on every bundle, v1 and v2** | `conversion_process.py`, `docling_adapter.py`, `item_provenance.py`, `bundle_writer.py`, `content_projection.py` |
| 3 Origin / OCR assets (S0005) | OCR asset capture and pins; one shared engine-identity rule (`identify_ocr_engine`) for item origins and the bundle OCR block | `item_provenance.py`, `ocr_asset_pins.json` |
| 4 Failure injection (S0002) | stable reasons, migrations 0009 + **0010** (`model_budget_exceeded`, `model_deadline_exceeded`, `model_contract_fallback`, `interpretation_failed`); every rejected or failed call fails the attempt, **including pre-dispatch rejections**; **reconvert at most once, counted from durable `conversion_started` events**; post-publication errors never spend conversion budget; queue depth bound | `queue.py`, `0009_*`, `0010_*`, `document_worker.py`, `vllm_graph_client.py`, `content_workflow.py` |
| 5 Interpretation / evidence (S0003) | pipeline-aware interpretation; **Graph-dense fallback to a direct call is never accepted**; `direct-baseline` uses the **shared F0001 prompt builder**; unsupported output fails closed | `graph_interpretation.py`, `openai_compatible_adapter.py` |
| 6 Pipeline selection / rollback | explicit committed `extraction.pipeline`; jobs pin it; legacy meaning `graph-direct` | `config.py`, `config/local.yaml`, `worker_cli.py` |
| 1 / 7 Corpus, comparison | independent corpus; immutable measured report (round 1); the harness now reports rejections, all-attempt p95 and per-completed-run review workload for any future measurement | `neuron/fixtures/qualification/`, `neuron/benchmarks/f0005_qualification.py` |

**Contract and architecture records (Architect role):**
- the ADR-0073 amendment for the optional add-only `extraction_quality.ocr` block, in the v1 and v2 schemas, with matching repo and package copies;
- the new **ADR-0074** (Local document-job execution controls, Proposed);
- the ADR-0060 qualification outcome (stays Proposed, failed gates recorded, reopen condition).

**Dependency change:** `neuron/uv.lock` moves pypdf from 6.19.0 to **6.21.2** (minimum fixed version; 6.21.3, released the day before, was rejected as too new). Floor `pypdf>=6.21.2`. No measured pin changed.

**Out-of-feature edit (disclosed):** `engine/tests/integration/test_content_migration_states.py:306` (F0004). Its `publication` fixture now upgrades to `head`, not `0008`.

**Not done, by design:** no activation. Committed config stays `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`.

**Not done, recorded:**
- **SEC-F5-M1 converter OS isolation:** an activation precondition in ADR-0074.
- **Queue-bound race:** a known limitation in ADR-0074, as the Architect recommended.
- **Code Review Lows L1, L3–L6:** follow-ups. L2 was fixed as part of the Architect's baseline finding.

## Acceptance Criteria Review

| AC | Self-assessment | Evidence |
|---|---|---|
| S0001-AC1 pins | Met | G1 `uv sync --locked`; report `pins`; container smoke |
| S0001-AC2 bundle identities | **Met in round 2.** Parser name, version and configuration; OCR engine name and version; OCR page count and pages; failed pages; warnings; source hash; asset digests — on v1 and v2. | `g2r-live-conversion.log`, `test_ocr_quality.py` |
| S0001-AC3 checkpoint before model | Met | live conversion |
| S0001-AC4 partial | Met (gl-q-013) | live conversion |
| S0001-AC5 stage guard | Met | live conversion; `test_conversion_process.py` |
| Audit ACs (S0001-AC6, S0002-AC7, S0003-AC7, S0004-AC8, S0005-AC6) | Partly met. Job history records job, generation, event, reason and time, with no source text; authorization decisions are in `audit_event`. No test asserts one record carrying every field the AC lists. | migration tests; `test_queue.py` |
| S0002-AC1 provider faults | Met on both engines | `g2r-live-provider-storage-auth-faults`, `g2r-live-timeout-faults` |
| S0002-AC2 kills | Met, re-run on current code | `g2r-live-kill-points-and-competing-workers` |
| S0002-AC3 storage | Met; at most 2 conversions, counted durably | storage ×2 = 2 conversions, `failed` |
| S0002-AC4 duplicates / competing / cancel / concurrency | Met, with the provider busy during the uncertain request; Graph internal fan-out is bounded by the single model slot | timeout and competing-worker lanes |
| S0002-AC5 / AC6 | Met | revocation and cancellation cases |
| S0003-AC1/AC2/AC5/AC6 | Met | `g2r-live-reinterpretation` |
| S0003-AC3 provenance retained | **Met in round 2** (8 completed live runs) | `g2r-live-reinterpretation` |
| S0003-AC4 unsupported output | **Met in round 2**, deterministically | `test_interpretation_rejections.py` |
| S0004-AC1/AC2/AC3 | Met; activation blocked | `report.json`, `report-summary.md` |
| S0004-AC4/AC7 | Pending re-run G3/G4 | — |
| S0004-AC5/AC6 | AC5 unreachable; branches tested in isolation, including v2 readability on rollback | `g2r-live-decision-branches` |
| S0005-AC1/AC2/AC3 | Met; 11/13 fall back to v1 (reported) | live conversion; `test_ocr_asset_provenance.py` |
| S0005-AC4 consumers | Met, except the pre-existing `test_content_worker_v2[False]` | `g2r-neuron-full.log` |
| S0005-AC5 | Not applicable (gated on S0004 acceptance) | — |

## Implementation Risks

1. **Graph dense fails qualification** (5 thresholds, read like for like). Recorded in ADR-0060.
2. **Converter isolation (SEC-F5-M1):** same OS user, no memory cap. Open; required before activation or real documents.
3. **Queue-bound race:** a lost race leaves a source object and access rows behind. The bound itself holds; the limitation is recorded in ADR-0074.
4. **The ADR-0073 OCR amendment needs readers and writers deployed together.** Readers built before it reject bundles carrying the field.
5. **Dependency advisories in the locked neuron environment:**
   - pillow 38: fixing it needs Docling ≥ 2.132 / pillow 13 and requalification;
   - docling/docling-slim 15;
   - aiohttp 8;
   - filelock 3;
   - litellm 1: GHSA-7hp6-4w63-5g45, published after round 1, fixed in 1.100.4;
   - certifi 1;
   - setuptools 1.
6. **Quiescence restarts the shared development vLLM.**
7. **Pre-existing failures outside F0005** (11 authx; `test_content_worker_v2[False]`), identical on HEAD.
8. **Lint debt** in the independent corpus author's `build_corpus.py`. Left unchanged; it is outside the corpus hash.
9. **Process deviations:**
   - `hint.py` was consulted after the edits, not before, for ten F0005 runtime files during the rework. The bindings it reported would not have changed the edits.
   - `commands.log` entries are written in batches after execution.

## Validation Evidence

- **Offline:** `artifacts/test-results/g2r-neuron-full.log` (235 passed, 29 live skips, 1 pre-existing failure) and `g2r-engine-full.log` (424 passed, 11 pre-existing failures).
- **Coverage:** `coverage-report.md`; changed-line coverage 83.1% (1,073/1,291).
- **Live:** `artifacts/test-results/g2r-live-*`; history in `g2r-attempt1/` and round-1 `live-*`.
- **Measurement:** `artifacts/qualification/report.json` and `report-summary.md` (G3 corrections inline).
- **Lint/type:** `artifacts/test-results/g2r-lint-typecheck.log`.
- **Security scans:** `artifacts/security/g2r/` (current) and `artifacts/security/` (round 1).
- **Deployability:** `deployability-check.md`.

## Result

PASS WITH RECOMMENDATIONS
