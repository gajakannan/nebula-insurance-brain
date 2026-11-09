# F0009 — Provenance + human-correction lineage

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

No authoritative fact exists without evidence, and human corrections append with lineage that feeds the Golden Corpus (sections 17, 75).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0010](../../architecture/decisions/ADR-0010-provenance-is-mandatory.md), [ADR-0037](../../architecture/decisions/ADR-0037-human-corrections-append-they-do-not-rewrite-evidence.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0006, F0008 (previously F0001).
- Carry the master blueprint 88 LearningCandidate hook: human corrections persist a reserved LearningCandidate reference for the Golden Corpus. No learning behaviour ships in v0.1 (F0041 owns it).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0009.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
