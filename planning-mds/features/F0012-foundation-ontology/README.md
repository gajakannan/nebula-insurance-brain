# F0012 — Foundation ontology

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

The foundation ontology module is the versioned base that every insurance module composes on (sections 19 to 22).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0011](../../architecture/decisions/ADR-0011-ontology-is-versioned-and-modular.md), [ADR-0012](../../architecture/decisions/ADR-0012-flexible-authoring-normalized-runtime.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0012.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Every ontology property declares `temporal_kind` (`STATE`, `EVENT`, `ETERNAL`) (ADR-0064).
- Properties and classes carry a definition, examples, and regression cases, which alignment and the workbench rely on (ADR-0063).
