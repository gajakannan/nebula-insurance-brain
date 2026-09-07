# F0020 — Minimal graph/temporal query API

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

A minimal graph and temporal query API answers the v0.1 acceptance questions as of valid time and recorded time (sections 20, 68, 87).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0022](../../architecture/decisions/ADR-0022-apache-age-is-the-graph-projection.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0020.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Assessment and example integration

Expose a consistent authorized canonical snapshot for F0065, including explicit valid/known coordinates and permitted completeness/conflict context. F0065 owns its assessment service contract; this query feature does not depend on the assessment UI.

See the [example coverage map](../../examples/README.md) and [F0065](../F0065-grounded-gl-guideline-assessment/README.md).
