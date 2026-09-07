# F0033 — pgvector retrieval

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

pgvector adds exact and approximate vector retrieval as a tenant-scoped projection; vectors locate evidence and never define truth (section 50).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0023](../../architecture/decisions/ADR-0023-pgvector-is-a-retrieval-projection.md). Likely predecessors (inferred, confirm at Phase B): F0003.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0033.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Assessment and example integration

F0065 already combines neural interpretation and symbolic rule evaluation in v0.1. This feature retains v0.2A vector retrieval scope: source/model/version-linked embeddings rank candidate evidence without defining facts or assessment confidence. See EX-FUTURE-001.

See the [example coverage map](../../examples/README.md) and [F0065](../F0065-grounded-gl-guideline-assessment/README.md).
