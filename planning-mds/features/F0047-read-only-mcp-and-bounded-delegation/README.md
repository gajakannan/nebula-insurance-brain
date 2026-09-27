# F0047 — Read-only MCP + verified principal, bounded delegation, and evidence access

**Status:** Planned
**Phase:** v0.2A
**Roadmap:** Later

## Overview

Read-only MCP tools use the same verified principal, resource scope, and evidence restrictions as the API; agents receive bounded delegation and no canonical write path (sections 69, 120.4).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0031](../../architecture/decisions/ADR-0031-agent-memory-is-separate.md), [ADR-0052](../../architecture/decisions/ADR-0052-delegated-agents-and-review-authority.md), [ADR-0053](../../architecture/decisions/ADR-0053-permission-safe-retrieval-and-historical-access.md). Likely predecessors (inferred, confirm at Phase B): F0002, F0046.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0047.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0069](../../architecture/decisions/ADR-0069-action-attempts-and-uncertain-outcomes.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Future mutation tools execute through action attempts; read-only tools are unaffected (ADR-0069).
