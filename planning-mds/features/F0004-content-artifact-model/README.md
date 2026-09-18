# F0004 — Content artifact model

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The content artifact contract (native DoclingDocument plus normalized views, blocks, coordinates, manifest) is what parse-once preserves and what every interpretation reads (sections 5, 80, 81, 108). ADR-0060 separates immutable parse artifacts from Docling-Graph interpretation outputs.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0003](../../architecture/decisions/ADR-0003-one-time-content-extraction.md), [ADR-0004](../../architecture/decisions/ADR-0004-source-content-artifact-and-interpretation-are-separately-versioned.md), [ADR-0040](../../architecture/decisions/ADR-0040-lossless-content-and-evidence-contract.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0004.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Keep the six-file parse bundle and parser identity from ADR-0040. Record Docling-Graph pipeline revision/configuration separately; the converter remains Docling.
- Publish and hash-verify the bundle through ContentArtifactStore. Store graph, provenance ledger, and effective extraction configuration as run-owned outputs; a new profile must not mutate the content artifact.
- Preserve source and bundle access controls, retention, and backup/restore coverage for the additional run outputs.
