# F0022 — Document 360 + native evidence review panel + parent/classification and reviewer authority

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

Document 360 with the Nebula Review Panel is the v0.1 human-correction loop, including parent and classification checks and reviewer authority (sections 71, 75, 111, 125).

This feature owns the panel: the renderer set (pdf.js for PDF, fflate over the OOXML parts for DOCX and XLSX, `TextDecoder` for delimited text), the selector resolvers behind [ADR-0058](../../architecture/decisions/ADR-0058-evidence-anchoring-and-selector-contract.md), the review batch and its submission, and the reviewer-authority checks that keep adjudication separate from canonical approval. Evidence is rendered inside the authorized session and never exported to another service.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap), section 115.3 (sequencing), and section 125 (the panel). Governing ADRs: [ADR-0057](../../architecture/decisions/ADR-0057-nebula-owns-the-native-evidence-review-panel.md), [ADR-0058](../../architecture/decisions/ADR-0058-evidence-anchoring-and-selector-contract.md), [ADR-0037](../../architecture/decisions/ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md), [ADR-0044](../../architecture/decisions/ADR-0044-review-surface-and-approval-contract.md), [ADR-0052](../../architecture/decisions/ADR-0052-delegated-agents-and-review-authority.md).

A working prototype of the panel — real PDF, DOCX, XLSX, and CSV byte streams parsed in the browser, with every coordinate, paragraph path, cell reference, and character offset derived at runtime — is [`planning-mds/examples/nebula-review-panel-live-files.html`](../../examples/nebula-review-panel-live-files.html). It is design evidence, not an implementation: it uses clean generated documents and exercises no OCR path.

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0009, F0016, F0018, F0021 (previously F0001).
- ADR-0052 decision recorded 2026-11-08 - the reviewer is the session principal, review is adjudication not approval, grants are checked at batch assembly and submission, and a stale task fails closed. Show reviewers which ADR-0038 source-authority rule applied.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0022.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Test chunk-relative to block/code-point mapping, page/bbox conventions, repeated values, and table-cell references in the native panel. Node-level provenance must not be displayed as property-level support.
- Preserve ADR-0058 failure behavior when translated evidence cannot resolve. The pipeline switch does not replace the native review surface or its authority checks.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0065](../../architecture/decisions/ADR-0065-assertion-admission-text-origin-and-mood.md), [ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Show a time mention's words beside its resolved interval and grade, and let an authorized reviewer set a document's date, which triggers re-resolution without re-parsing (ADR-0064).
- Show interpretation drops per document, separately from review items, and show text origin beside evidence. `DESCRIBED`-only evidence arrives as a `DESCRIBED_EVIDENCE` review item (ADR-0065).
- Capture an optional free-text `why` beside reason codes on every decision; it becomes precedent for automation (ADR-0067).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
- **Schema versioning (validate finding A-5):** the optional free-text `why`, the `DESCRIBED_EVIDENCE` reason, and reviewer-set document dates need a versioned addition to `schemas/review-decision.schema.json` with compatible readers.
