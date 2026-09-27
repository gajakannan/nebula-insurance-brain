# F0032 — Knowledge Evolution Engine

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

When an ontology or profile release changes meaning, the engine determines affected profiles, content, derived facts, and candidates and schedules targeted reinterpretation (sections 30, 112).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0016](../../architecture/decisions/ADR-0016-semantic-reinterpretation-is-incremental.md), [ADR-0017](../../architecture/decisions/ADR-0017-knowledge-evolution-is-first-class.md), [ADR-0047](../../architecture/decisions/ADR-0047-controlled-learning-and-reinterpretation.md). Likely predecessors (inferred, confirm at Phase B): F0016, F0030.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0032.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

Proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) adds these implementation acceptance requirements:

- Determine the affected profiles and native block/item scope from the ontology/profile delta, then invoke F0016 with that scope and the saved native JSON.
- Prove excluded blocks do not enter model context; any necessary context expansion is declared, authorized, and budgeted before execution. Preserve references to the original immutable artifact when selecting or reconstructing input views.
- Assert zero physical conversion/OCR, unchanged artifact hashes, and a new run identity. A full-document pipeline rerun does not satisfy targeted reinterpretation; reject unsupported scope without silently broadening it.
- Exercise budget previews, canaries, deduplicated scheduling, pause/cancel, retry, and checkpointed resumption over affected content. F0016 supplies scoped runs; this feature owns evolution scheduling and impact analysis.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0068](../../architecture/decisions/ADR-0068-decision-basis-fingerprints.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- On the alignment route, recompute only signatures and implication rules whose basis changed; re-read no documents. On the template route, keep targeted block reinterpretation (ADR-0063, ADR-0068).
