# F0031 — Document/Extraction Profile Workbench

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

Profile authoring with release hashes pinned to interpretation runs so changing a profile never silently reinterprets history (sections 7, 8, 112). Includes compiled profile/configuration previews and release hashes.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0014](../../architecture/decisions/ADR-0014-document-profiles-drive-interpretation.md), [ADR-0015](../../architecture/decisions/ADR-0015-extraction-profiles-are-composable.md), [ADR-0045](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md). Likely predecessors (inferred, confirm at Phase B): F0014, F0015.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0031.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Show unsupported schema mappings and estimated context/cost before execution. A new extraction mode, template, or upstream revision requires a versioned run and evaluation; profile edits do not mutate prior artifacts or results.
