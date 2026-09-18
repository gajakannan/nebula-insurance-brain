# F0014 — Document Profile model

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Document profiles select which ontology modules and extraction profiles apply to a document type and business context (section 7). Nebula selects the released profile before the Docling-Graph pipeline executes.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0014](../../architecture/decisions/ADR-0014-document-profiles-drive-interpretation.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0014.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Pass the selected profile/version to the F0015 compiler and F0016 run; do not delegate tenant policy, document classification authority, or ontology release selection to upstream graph inference.
