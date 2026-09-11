# Dependency Matrix — Nebula Insurance Brain (F0001-S0002)

One exact, tested combination (master blueprint section 114.3). Do not rely on generic
compatibility claims — every row below was verified against the source cited. Update this
file and re-verify whenever any pin changes.

**Complete as of F0001-S0007 (2026-09-10):** every component this feature's proofs touch is
pinned, sourced, and verified below — the S0003-S0007 rows were re-checked for accuracy while
settling ADR-0040/ADR-0041/ADR-0044/ADR-0049/ADR-0050/ADR-0058, and one inaccurate claim (see the
Docling row) was corrected in the process rather than left standing.

| Component | Pin | Verified against | Source |
|---|---|---|---|
| Python (engine/, neuron/) | 3.13+ (host tested: 3.14.4) | `uv sync` on this host, `engine/pyproject.toml`/`neuron/pyproject.toml` `requires-python` | F0001-S0001 |
| PostgreSQL | `FROM postgres:18.0-trixie` in the Dockerfile; the tag's upstream content has since moved forward to server version 18.6 in place (Debian's `trixie`-suffixed point-release tags are not immutable across point releases) — measured live via `postgres --version` in the running container at F0001-S0006 | `docker/postgres/Dockerfile`; fallback 17.x only if the AGE build fails on 18 (record the failure here, never a silent downgrade) | F0001 G1 clarification (2026-09-06); version drift noted at S0006 |
| pgvector | v0.8.6 | Built from source in `docker/postgres/Dockerfile`, image built clean on this host 2026-09-08; v0.8.0 was tried first and **rejected** — its `hnswvacuum.c` calls the pre-PG18 single-argument `vacuum_delay_point()`, which PG18 changed to take a `bool is_analyze` argument, so it fails to compile against PG18 server headers | pgvector GitHub releases |
| Apache AGE | PG18/v1.8.0-rc0 | Built from source in `docker/postgres/Dockerfile`, image built clean on this host 2026-09-08; `CREATE EXTENSION age` in `docker/postgres/init/02-extensions.sql`; the plan's originally-cited `PG18/v1.6.0-rc0` tag does not exist upstream (AGE's PG18 release branch starts at v1.7.0-rc0) | Apache AGE GitHub releases (PG18 branch) |
| btree_gist | ships with PostgreSQL contrib | `CREATE EXTENSION btree_gist` in `docker/postgres/init/02-extensions.sql` | PostgreSQL 18 contrib |
| authentik | 2026.2.0 | `docker-compose.yml`; matches `nebula-insurance-crm`'s validated pin (ADR-006) | nebula-insurance-crm docker-compose.yml |
| Docling | 2.126.0 | `engine/apps/api/src/brain_api/versions.py` (`DOCLING_PINNED_VERSION`); installed as a `neuron/brain-ingestion` dependency, exercised live against the native fixture by the automated F0001-S0003 test, and against the scanned/OCR fixture by a manual check at F0001-S0007 (2026-09-10: RapidOCR recovers identical content, 4 blocks/542 chars, from both variants) — the OCR path itself is not yet covered by an automated assertion (see ADR-0040 Limitations) | F0001-S0001 (declared); F0001-S0003 (live, native); F0001-S0007 (live, scanned/OCR, manual) |
| Docling-Graph | **not used** — evaluated 1.9.1 and rejected at F0001-S0003; see ADR-0040 input below | `docling-graph==1.9.1` was installed and run live against this proof's fixture on 2026-09-09, then removed as a `neuron/` dependency | F0001-S0003 |
| vLLM | 0.25.1 | `docker/local-inference-runbook.md`; matches the CRM's validated ADR-035 profile; served `microsoft/Phi-4-mini-instruct` live on this host's RTX 5070 for F0001-S0003's proof harness on 2026-09-09 | F0001 G1 clarification (2026-09-06); F0001-S0003 (live) |
| Inference model | `microsoft/Phi-4-mini-instruct` | Hugging Face revision pinned in `docker/local-inference-runbook.md`; `--max-model-len 4096` | F0001 G1 clarification (2026-09-06); ADR-0055 |
| Node (experience/ toolchain, proof scope only) | Node 24.16.0 (host tested); React 18.3.1, Vite 6.4.3, TypeScript 5.9.3, Vitest 5.0.0 | `experience/package.json`; `pnpm install`/`pnpm exec tsc -b`/`pnpm exec vitest run`/`pnpm exec vite build` all green on this host 2026-09-09. The full toolchain (ESLint theme rules, Playwright, Lighthouse, contract tests) is F0021's — this proof only needs build+unit-test+lint | F0001-S0004 |
| `pdf.js` (`pdfjs-dist`) | 4.10.38 | `experience/src/review-panel/Viewport.tsx`; real rendering verified via `pnpm exec vite build` (worker bundled, no CDN fetch) | F0001-S0004 |
| `fflate` | 0.8.3 | declared per the assumption ("bundled with the app, no third-party network request"); not yet exercised — this proof's fixture is PDF-only, so the OOXML/zip path (`fflate`'s actual use) is deferred to whichever future story adds a DOCX/XLSX fixture. See `Deferred Non-Blocking Follow-ups` in `STATUS.md` | F0001-S0004 |

## AGE build fallback record

Not exercised. The `PG18/v1.8.0-rc0` build succeeded after correcting the originally-cited
(nonexistent) `PG18/v1.6.0-rc0` tag; no 17.x fallback was needed.

## ADR-0040 input: Docling-Graph rejected as the extraction engine (F0001-S0003, 2026-09-09)

`docling-graph==1.9.1`'s public `run_pipeline()` API always reconverts the source document
itself (`docling_graph.core.extractors.document_processor.DocumentProcessor
.convert_to_docling_doc` calls `DocumentConverter.convert(source)` unconditionally); it has no
path to accept an already-parsed `DoclingDocument`, and its internal converter only registers
`InputFormat.PDF`/`InputFormat.IMAGE` — not `InputFormat.JSON_DOCLING` — so even a
serialized-DoclingDocument-as-source workaround is closed off. This was confirmed by a live
run, not by reading the source alone. It directly conflicts with ADR-0003 (parse once) and
this story's own acceptance criterion 2 (zero conversion/OCR calls on reinterpretation).

**Decision:** `neuron/brain-extraction`'s `docling_graph_adapter.py` calls the OpenAI-compatible
backend directly (the same contract ADR-0001/ADR-0055 already specify) against the
already-persisted `docling-document.json`, using vLLM's native structured/guided JSON output
(`response_format: json_schema`, `strict: true`) instead of the `docling-graph` package.
`docling-graph` is not a `neuron/` runtime dependency.

Two further findings from the same live run, both applied in `docling_graph_adapter.py`:
- Pydantic's `model_json_schema()` omits `required`/`additionalProperties`; OpenAI/vLLM's
  `strict: true` mode needs both on every property to reliably constrain generation — without
  them the model returned `null` for a present field and fabricated a composite string for
  another, non-deterministically.
- `temperature=0` is required for the reproducibility the harness needs (business rule 3:
  `model_confidence` is a signal, not a calibrated probability — determinism at least removes
  sampling as a source of run-to-run variance).

Even with both fixes, a value crammed into a single dense text block alongside four other
similar values (`general_aggregate_limit`, sharing one block with four other dollar amounts)
was extracted as a paraphrased composite string that could not be found verbatim in the
source — correctly resolved to `precision: unresolved` rather than fabricating a bounding box
(business rule/edge case: "no bounding box is fabricated"). Simpler, less densely-packed
fields (`each_occurrence_limit`, `named_insured`, both policy period dates) extracted
correctly and deterministically across repeated runs. This is a real, measured limit of
`microsoft/Phi-4-mini-instruct` at 4,096 tokens on densely-packed source text, not a tooling
defect — recorded here for ADR-0040 and F0001-S0007's settlement of context adequacy.
