# F0015 — Extraction Profile compiler

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Composable extraction profiles compile a shared base with line-of-business extensions; reinterpretation without reparse depends on them (section 8). ADR-0060 targets trusted Docling-Graph templates and explicit pipeline configuration.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0015](../../architecture/decisions/ADR-0015-extraction-profiles-are-composable.md), [ADR-0016](../../architecture/decisions/ADR-0016-semantic-reinterpretation-is-incremental.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0015.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Compile composed base/LOB profiles into trusted Pydantic templates and explicit pipeline settings while preserving units, qualifiers, ontology mappings, and evidence requirements. Reject unsupported mappings; profile authors cannot select arbitrary Python imports.
- Version and hash the schema, template, prompt, and pipeline configuration. Exercise both fixed F0005 proof templates and compiler-produced templates against the accepted adapter.
- Budget schema/prompt/input and output tokens before every model call, including retries, repair, fill, or reconciliation. A strategy change must not silently truncate or widen scope. Measure the dense-limit case recorded in ADR-0040.
