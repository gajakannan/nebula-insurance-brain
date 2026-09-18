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
| Docling-Graph | **1.9.1 candidate**, locked in `neuron/uv.lock`; not activated | Installed from cache; real Graph stage tests cover native/scanned conversion, saved JSON reuse, and publication ordering with recorded model responses. Live model and operational gates remain open. | [F0005 evidence](../planning-mds/features/F0005-one-time-docling-ingestion/compatibility-evidence.md) |
| vLLM | 0.25.1 | `docker/local-inference-runbook.md`; matches the CRM's validated ADR-035 profile; served `microsoft/Phi-4-mini-instruct` live on this host's RTX 5070 for F0001-S0003's proof harness on 2026-09-09 | F0001 G1 clarification (2026-09-06); F0001-S0003 (live) |
| Inference model | `microsoft/Phi-4-mini-instruct` | Hugging Face revision pinned in `docker/local-inference-runbook.md`; `--max-model-len 4096` | F0001 G1 clarification (2026-09-06); ADR-0055 |
| Node (experience/ toolchain, proof scope only) | Node 24.16.0 (host tested); React 18.3.1, Vite 6.4.3, TypeScript 5.9.3, Vitest 5.0.0 | `experience/package.json`; `pnpm install`/`pnpm exec tsc -b`/`pnpm exec vitest run`/`pnpm exec vite build` all green on this host 2026-09-09. The full toolchain (ESLint theme rules, Playwright, Lighthouse, contract tests) is F0021's — this proof only needs build+unit-test+lint | F0001-S0004 |
| `pdf.js` (`pdfjs-dist`) | 4.10.38 | `experience/src/review-panel/Viewport.tsx`; real rendering verified via `pnpm exec vite build` (worker bundled, no CDN fetch) | F0001-S0004 |
| `fflate` | 0.8.3 | declared per the assumption ("bundled with the app, no third-party network request"); not yet exercised — this proof's fixture is PDF-only, so the OOXML/zip path (`fflate`'s actual use) is deferred to whichever future story adds a DOCX/XLSX fixture. See `Deferred Non-Blocking Follow-ups` in `STATUS.md` | F0001-S0004 |

## AGE build fallback record

Not exercised. The `PG18/v1.8.0-rc0` build succeeded after correcting the originally-cited
(nonexistent) `PG18/v1.6.0-rc0` tag; no 17.x fallback was needed.

## ADR-0040 input: Docling-Graph rejected as the extraction engine (F0001-S0003, 2026-09-09)

F0001 reported that its tested invocation could not reuse a parsed document and chose a direct OpenAI-compatible adapter. That implementation and its measured results remain the historical baseline; see the unchanged archived F0001 records.

**Correction, 2026-09-17:** the pinned 1.9.1 wheel has a separate native-JSON input path. F0005 tests now exercise that path with conversion prohibited, including JSON from the native and scanned PDF fixtures. The earlier inference that the entire package always reconverts was too broad. This does not establish what differed in F0001's environment or invocation, nor prove live extraction quality.

The direct baseline is now `openai_compatible_adapter.py`; `docling_graph_adapter.py` is a compatibility import. The candidate `docling_graph_pipeline.py` composes a pre-extraction publication stage into the pinned upstream orchestrator. Graph is installed for this candidate; activation remains gated by ADR-0060.

Two further findings from the same live run, retained in `openai_compatible_adapter.py`:
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

## Proposed migration — Docling-Graph (ADR-0060, 2026-09-15)

The table and F0001 finding above record the installed proof baseline. [ADR-0060](../planning-mds/architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) proposes Docling-Graph as the future document pipeline coordinator; Docling remains its converter. The 1.9.1 candidate is installed and has limited contract evidence; production activation and the complete proof gates remain pending.

| Candidate component | Activation requirement | Owner |
|---|---|---|
| `docling-project/docling-graph` | Exact release/source commit and package digest, tested native JSON reuse and durable conversion checkpoint before extraction; no floating `main` dependency | F0005 |
| Docling / docling-core and chunking/model dependencies | Compatible locked versions, native + scanned fixture conversion, stable item/evidence mappings; record any change from the F0001 pin | F0005 |
| Local vLLM / Phi profile | Revalidate supported backend configuration, structured templates, every-call context guard, and extraction quality at the existing context limit | F0005 / F0015 |

The [F0005 compatibility evidence](../planning-mds/features/F0005-one-time-docling-ingestion/compatibility-evidence.md) records the selected wheel digest and the tested stage seam. The [current input documentation](https://github.com/docling-project/docling-graph/blob/main/docs/fundamentals/pipeline-configuration/input-formats.md) describes native JSON reuse; it does not prove the previously tested package supported it. Record an immutable source identity as well as a version string. The [current orchestrator](https://github.com/docling-project/docling-graph/blob/main/docling_graph/pipeline/orchestrator.py) exports after extraction and disables disk output by default in API mode; verify a supported pre-extraction persistence seam before activation. Keep proof results separate from these pending acceptance requirements.
