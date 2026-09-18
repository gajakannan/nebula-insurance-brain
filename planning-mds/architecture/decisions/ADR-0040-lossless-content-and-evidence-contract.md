# ADR-0040: Lossless Content and Evidence Contract

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Settled:** 2026-09-10 (F0001-S0007), from F0001-S0003's live proof run on 2026-09-09
**Deciders:** Architect (record owner); backend-developer and ai-engineer executed the proof
**Settled by:** F0001-S0003 (parse once, reinterpret twice, evidence resolves); results recorded by F0001-S0007
**Source:** `planning-mds/architecture/master-blueprint.md` section 116

## Context

Proposed in the master blueprint pre-build requirements to settle: Native DoclingDocument plus normalized views; honest evidence precision.

Example and reference: Reinterpret without OCR; section 108.

## Decision

**Accepted.** Native DoclingDocument plus normalized views; honest evidence precision.

Parsing happens exactly once per source document. The persisted six-file bundle
(`docling-document.json`, `normalized.md`, `blocks.jsonl`, `tables.jsonl`,
`layout.jsonl`, `manifest.json`) is the sole input to every later interpretation
run; no interpretation call ever re-converts or re-OCRs the source. Every
extracted value carries a declared evidence precision (`span`/`block`/`page`/
`unresolved`); when the source does not support a tighter grounding, the system
declares `unresolved` rather than fabricating a bounding box.

## Results (F0001-S0003, measured 2026-09-09; re-verified 2026-09-10 at S0007)

- **Parse-once, zero reconversion:** two independent interpretation runs
  (profiles `gl-limits-a`, `gl-limits-b`) against one persisted artifact both
  report `conversion_calls == 0` and `ocr_calls == 0` (`assert_no_reparse`), and
  the artifact's `manifest.json` sha256 is unchanged after both runs — proving
  interpretation never touches the source bytes again.
  Test: `neuron/tests/integration/test_parse_once_reinterpret.py::test_parse_once_reinterpret_twice_evidence_resolves`.
- **Precision observed per binding:** of 5 extracted fields
  (`each_occurrence_limit`, `named_insured`, both policy period dates,
  `general_aggregate_limit`), 4 resolved with a full span-level binding (page,
  `block_id`, `char_start`/`char_end`, `bbox` all populated) and 1
  (`general_aggregate_limit`) resolved to `precision: unresolved` — the honest
  outcome the decision requires, not a defect. See "Limitation" below.
- **Context-limit rejection edge case:** a context budget too tight for even
  the fixture is rejected client-side before any model call
  (`model_calls == 0`, warning "exceeds budget") — no truncated or partial
  extraction is ever silently accepted.
  Test: `neuron/tests/integration/test_parse_once_reinterpret.py::test_reinterpretation_over_context_limit_is_rejected_client_side`.
- **Scanned-variant OCR path (manually verified, not yet an automated assertion):**
  running `DoclingAdapter().parse()` directly against both
  `neuron/fixtures/gl-policy-declarations.pdf` (native) and
  `-scanned.pdf` (image-only, forces RapidOCR) on 2026-09-10 produced identical
  extracted content (4 text blocks, 542 characters) from both — real OCR
  recovers the same text as native parsing on this fixture. This was checked by
  hand at S0007, not by a pytest assertion; see Limitations.

## Limitations

1. **Dense-block extraction limit (real, not a defect):** `general_aggregate_limit`
   shares one text block with four other dollar amounts. `microsoft/Phi-4-mini-instruct`
   at a 4,096-token context returns a paraphrased composite string for it that
   cannot be found verbatim in the source; the system correctly resolves this to
   `precision: unresolved` instead of fabricating a location. Full narrative in
   `docker/DEPENDENCY-MATRIX.md`'s "ADR-0040 input" section. Tracked for a
   possible chunking/profile refinement in F0015; not a blocker to acceptance —
   it is itself evidence the honesty requirement works.
2. **Scanned-variant coverage gap:** the OCR path above is proven only by a
   manual, one-off check at S0007, not by an automated regression test — the
   only test file that runs live (`test_parse_once_reinterpret.py`) exercises
   the native fixture alone. F0002 should extend that test (or add a sibling)
   to assert against the scanned variant too, so this stops depending on a
   human re-running it before every release.

## References

- `planning-mds/architecture/master-blueprint.md` section 116 and the section cited above
- `docker/DEPENDENCY-MATRIX.md` — "ADR-0040 input: Docling-Graph rejected as the extraction engine" (why `docling-graph` itself is not the extraction path; the extraction contract this ADR settles is honored through a direct OpenAI-compatible/vLLM call instead)
- `neuron/tests/integration/test_parse_once_reinterpret.py`
- `planning-mds/features/F0001-repository-and-engineering-foundation/STATUS.md` (AI Runtime Progress, Deferred Non-Blocking Follow-ups)

## Refinement — 2026-09-15

[ADR-0060](ADR-0060-docling-graph-document-pipeline-orchestration.md) proposes Docling-Graph document pipeline orchestration. The six-file content contract and measured F0001 results remain accepted. The selected future extraction path is Docling-Graph, subject to F0005 proving native JSON reuse, publication before extraction failure, and evidence translation. F0001 used a direct OpenAI-compatible adapter; its results do not establish Docling-Graph compatibility.
