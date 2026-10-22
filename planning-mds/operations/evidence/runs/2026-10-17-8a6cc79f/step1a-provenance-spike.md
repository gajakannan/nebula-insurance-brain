# Step 1a — pinned converter per-item provenance

Run: `2026-10-17-8a6cc79f`; feature: F0004; owner: Codex (AI Engineer role).
Executed in the neuron validation container after G1 passed and after restoration
of its non-root RapidOCR model cache. Synthetic development fixtures only.

## Reproduction

From the selected product root:

```sh
docker compose -f planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/runtime/compose.yaml exec -T neuron-validation python neuron/packages/brain-ingestion/tests/spikes/test_item_provenance.py --output planning-mds/operations/evidence/runs/2026-10-17-8a6cc79f/artifacts/test-results/step1a-provenance
```

Exit: 0. Full log: `artifacts/test-results/step1a-provenance-run.txt`.
The retained pytest regression also passes: **1 passed** in the same application
container; see `artifacts/test-results/step1a-pytest.txt`. Dependency warnings
are retained in that log. Ruff check passes and the source was formatted.
Per-cell receipts, expected/observed results and counts:
`artifacts/test-results/step1a-provenance/item-provenance.json`.
The same directory retains the three PDFs and their actual native JSON exports.

## Environment and observed hook

Python 3.14.4; Docling 2.126.0; docling-core 2.95.0; docling-parse 7.18.0;
RapidOCR 3.9.2; Torch 2.14.0. Actual OCR selected the Torch CPU backend.

The converter's preprocessing boundary retains a positive `PdfTextCell` receipt
with the actual `ThreadedDoclingParsePageBackend` class before backend release.
The actual `RapidOcrModel.post_process_cells` call retains positively tagged OCR
cells and the observed engine class. Reading-order hooks bind those actual
cluster cells to the returned stable item reference; merged elements contribute
all receipts. No text/geometry search guesses an output-item relationship, and
no page OCR count or generic `from_ocr=False` cell establishes native origin.
The wrappers belong to one initialized converter instance; no global class or
production adapter was modified.

## Expected versus observed

| Fixture | Native item | Expected | Observed | Producer |
|---|---|---|---|---|
| native | #/texts/0 — NATIVE ALPHA POLICY | STATED | STATED | ThreadedDoclingParsePageBackend; Docling/docling-parse versions above |
| native | #/texts/1 — NATIVE BETA COVERAGE | STATED | STATED | Same observed backend |
| scanned | #/texts/0 — two scanned lines | OCR | OCR | RapidOcrModel; RapidOCR 3.9.2, Torch 2.14.0 |
| mixed | #/texts/0 — NATIVE ALPHA POLICY | STATED | STATED | Observed PDF backend |
| mixed | #/texts/1 — NATIVE BETA COVERAGE | STATED | STATED | Observed PDF backend |
| mixed | #/texts/2 — two scanned lines | OCR | OCR | Observed RapidOcrModel |

All three conversions succeeded and retained every expected fixture token.
Unattributable items: native **0/2**, scanned **0/1**, mixed **0/3**.
The mixed-fixture per-document v1 fallback count is **0/1**. This is an observed
synthetic fixture result, not an estimate for production documents.

## Diagnostics preserved

The initial runtime cache denial is retained separately as
`step1a-runtime-cache-failure.txt` and `runtime-cache-failure.json`; it occurred
before conversion. The subsequent observer diagnostic captured the native
backend too late in the lifecycle; `step1a-late-native-hook.txt` and
`late-native-hook.json` preserve it. Moving the observer to the actual extraction
boundary supplied the missing producer receipt without inferring an origin.
These are not the final spike verdict.

## Result and limits

PASS for the approved three-fixture Step 1a criteria. The Architect must record
the exit decision in `gate-decisions.md` before Step 1b. Private hooks remain
version-sensitive and require the retained regression test when upgrading the
converter. A future unobserved or mixed producer must return ORIGIN_UNAVAILABLE
for that item; this spike does not authorize guessing or splitting text without
actual subspan evidence. The production v2 writer remains unimplemented and
disabled until the Step 4 compatibility proofs pass. ADR-0073 remains Proposed.
