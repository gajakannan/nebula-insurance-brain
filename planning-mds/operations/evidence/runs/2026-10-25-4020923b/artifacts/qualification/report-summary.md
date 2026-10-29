# F0005 qualification report summary — run 2026-10-25-4020923b

**Report:** [`report.json`](report.json) (immutable; measured 2026-10-26 01:01–01:27 -04:00; `void: false`)
**Corpus:** `f0005-gl-qualification-v1`, 13 synthetic documents (6 native, 4 scanned, 2 mixed, 1 partial), 2 profiles, 26 document-profiles per engine, 58 present and 7 absent field expectations. Corpus hash `fbc5e263c861c401dea07e3deac4023a0f660d35bb2edc891f8297ee0a5e2dc9`; expectation-set hash `16a29d67dddddea4e18136465567f67cd63c790fa9eb68018c35e4636933390c`. Both were recorded at 2026-10-25T23:40, before any measured run.
**Configuration:** vLLM 0.25.1, `microsoft/Phi-4-mini-instruct` @ `cfbefacb99257ffa30c83adab238a50856ac3083` (model and tokenizer), context 4,096, client output reservation 512 tokens, 16 calls/run, Docling 2.126.0, Docling-Graph 1.9.1, RapidOCR 3.9.2 with pinned assets. Each engine ran in an isolated schema, content root and hashed temporary config, through the real worker composition and host guard. The committed config was unchanged throughout.
**Normalization:** whitespace collapse and Unicode NFC only (PRD).

## Thresholds — Graph dense vs. the direct baseline

| Metric | PRD threshold (Graph dense) | Direct baseline | Graph dense | Result |
|---|---|---|---|---|
| Schema validity | 100%, no silently invalid result | 100% (25/25 completed; 1 explicit failure) | 100% (8/8 completed; 18 explicit failures) | **MET** |
| Field accuracy | ≥ 90% and ≤ 5 pp below baseline | 41.4% (24/58) | 27.6% (16/58) | **MISSED** (below 90%; 13.8 pp below baseline) |
| Abstention | ≥ 95% | 42.9% (3/7) | 0.0% (0/7; no absent-field case completed) | **MISSED** |
| Fabricated evidence | 0 | 0 | 0 | **MET** |
| Evidence resolution | ≥ 80% and not below baseline | 66.7% | 50.0% | **MISSED** |
| Context budget | 0 calls over 4,096 | 0 | 0 | **MET** |
| Latency p95 | ≤ 120 s and ≤ 3× baseline p95 | 1.48 s | 9.84 s (limit 4.44 s) | **MISSED** (> 3× baseline) |
| Review workload | ≤ 1.25× baseline per document | 2.92 | 1.54 | **MISSED (corrected after G3)** — 1.54 is met only because the 18 failed runs add zero review items; per completed run Graph dense needs 1.42–1.64× (1.64× per completed run; 1.42× on the 7 cases both engines completed — corrected after G3 round 2) the baseline, over the 1.25× limit |
| Recovery | 0 reconversions/duplicates across injected failures | — | — | **MET** — S0002 suites: every fault mode, kill point and storage fault ended with single accepted effects; the competing-worker case asserts no second claim, provider concurrency 1, terminal states and (round 3) a recovery bound for the held job, not single effects; conversions stayed within reconvert-at-most-once (the storage-failure ×2 case had 2 conversions) |

**Outcome: five thresholds missed (accuracy, abstention, evidence resolution, latency and, read like for like, review workload). Per the PRD and S0004-AC3, a missed threshold blocks activation and is never re-run with relaxed budgets.** Graph dense cannot be activated. The remaining decision is the operator's recorded rejection (ADR-0060 stays Proposed, or becomes Rejected if the operator says so). The settings for that are `extraction.pipeline: direct-baseline` and `content.v2_writer_enabled: false`, which are already the committed values.

## Why Graph dense failed

- 18 of 26 document-profiles ended `failed` after three attempts, each with `model_malformed_output`. The failing documents are gl-q-001, 002, 003, 005, 008, 009, 010, 011, 012 and 013.
- The failures happen in Graph's first-stage *skeleton* call. Either the response is cut off at the 512-token output reservation (`finish_reason=length`, client `incomplete_response`), or Phi-4-mini returns JSON with duplicate keys, which the client rejects as ambiguous. Phi-4-mini at temperature 0 does the same thing on every retry.
- Once the skeleton fails, Graph falls back to a single direct call. The worker deliberately fails that attempt instead of reporting a direct-contract answer as dense.
- In the 8 runs that completed, no evidence selector contradicted its value (fabricated = 0), but 11 of the 20 dense values were unresolved. *(Corrected after G3; the earlier text wrongly said every value was grounded.)*

## Context for reviewers (not threshold changes)

- **Graph direct** is reported, not a candidate. It completed 26/26 with 84.5% accuracy (49/58), 14.3% abstention and 0% evidence resolution: its values are right but never located exactly. Review workload was 4.92 per document.
- **The direct baseline is the F0001 prompt, unchanged.** It sends only document text items, never tables, so table-borne limits are invisible to it. Each-occurrence accuracy was 2/12 and general-aggregate 1/11. This makes the baseline weak, which flatters the "≤ 5 pp below baseline" comparison. Graph dense misses the absolute thresholds regardless.
- **gl-q-004 expectation:** the `$` and the amount are in adjacent cells, so the expected value is `$ 500,000`. A model answer of `$500,000` is a miss under the PRD normalization. This affects all engines equally.
- **v2 fallback (S0005-AC3):** 2 of 13 documents publish v2 (gl-q-005, gl-q-009); 11/13 (84.6%) fall back to v1 with `ORIGIN_UNAVAILABLE`. Cause: table cells have no attributable origin in the pinned provenance hook. This is reported, not hidden.
- **Calls and tokens (reported, not thresholded):**
  - Baseline: 25 calls, 6,634 prompt / 1,161 completion tokens.
  - Graph dense: 16 completed-run calls, 24,698 / 4,314.
  - Graph direct: 26 calls, 18,674 / 1,408.
  - GPU memory sampled about 11.5 GiB (vLLM at 0.90 utilization).
- **A non-measured diagnostic** ([`diagnostic-dense-subset-NOT-MEASURED.json`](diagnostic-dense-subset-NOT-MEASURED.json)) reproduced the skeleton truncation before this run. It is not part of the measurement.

## Options the operator may weigh (none applied)

These change the recorded configuration or the candidate, so any of them would be a new plan decision and a full re-measurement, never a re-score of this report:

1. Reject Graph dense now; keep the direct baseline. This is the only outcome the current thresholds allow.
2. Re-plan with a larger output reservation or a different serving model, then re-measure both engines in full.
3. Re-plan around Graph direct as a candidate. It is excluded by the approved PRD; it would need new thresholds and an evidence-resolution fix.

## Corrections after G3 review (2026-10-26)

The independent QA review (`../../qa-qualification-verdict-round1.md`) recomputed every metric from the per-case rows. All values match `report.json`. It corrected three statements in this summary:
- the review-workload verdict, which is like-for-like MISSED, not MET;
- the claim that every completed dense value was grounded;
- the recovery note's conversion count.

The fixes are inline above. `report.json` is unchanged.

The independent Code Review (`../../code-review-report-round1.md`, H1) found that pre-dispatch budget and deadline rejections leave no call record. A Graph-dense run could therefore be counted as complete after such a rejection, and `context_rejections` can never be non-zero. The recorded runs show no budget rejections (all 54 dense-to-direct fallbacks follow a recorded failure), so this measurement and its outcome stand. H1 must be fixed before any re-measurement.
