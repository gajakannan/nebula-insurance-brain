# F0016 — Semantic interpretation runs

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Semantic interpretation runs version every extraction over persisted content and are the unit of incremental reinterpretation (sections 28, 29). ADR-0060 adds pipeline/template identity, scoped provenance, and run-owned graph outputs.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0016](../../architecture/decisions/ADR-0016-semantic-reinterpretation-is-incremental.md), [ADR-0035](../../architecture/decisions/ADR-0035-interpretation-basis-is-first-class.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0016.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Load only the published native artifact for initial interpretation and later reruns. Record artifact hash, selected blocks, profile/template/schema/config hashes, explicit chunking/extraction settings, upstream revision, model/prompt identity, attempt, counters, costs, and complete/partial/failed outcome.
- Persist graph/provenance/effective configuration separately from the parse bundle. Record upstream chunk/item-to-Nebula evidence mappings; preserve unresolved and coarse grounding.
- Prove targeted-block extraction retains original references and does not silently expand to the full document. Reject unsupported scope configurations explicitly.
- Keep authorization, job idempotency, cancellation, and acceptance in Nebula. No extraction graph export may publish canonical facts or write AGE directly.
