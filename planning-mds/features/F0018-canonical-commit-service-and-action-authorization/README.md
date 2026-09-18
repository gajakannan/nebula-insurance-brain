# F0018 — Canonical commit service + action authorization and policy-version audit

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

The canonical commit service is the only write path to truth, with action authorization, policy-version audit, transactional outbox, and projection delivery (sections 66, 109). Docling-Graph candidates follow the same authorized commit path (ADR-0060).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0002](../../architecture/decisions/ADR-0002-postgresql-is-the-authoritative-runtime-store.md), [ADR-0028](../../architecture/decisions/ADR-0028-temporal-owns-execution-brain-owns-semantic-state.md), [ADR-0041](../../architecture/decisions/ADR-0041-atomic-semantic-commit-and-projection-delivery.md), [ADR-0050](../../architecture/decisions/ADR-0050-native-policy-evaluation-and-resource-scope.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0018.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Exercise duplicate upstream outputs and activity/job retries through canonical commit idempotency. Extraction graph writes, local deduplication, and upstream schema validation cannot bypass review, authorization, or bitemporal integrity.
