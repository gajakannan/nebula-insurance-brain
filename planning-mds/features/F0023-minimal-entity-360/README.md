# F0023 — Minimal Entity 360

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

Minimal Entity 360 exposes current and historical facts with evidence pointers for the acceptance question (section 70).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0036](../../architecture/decisions/ADR-0036-nebula-keeps-a-native-semantic-ux-onyx-is-a-reference-implementation.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0023.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Assessment and example integration

Provide the host Entity 360 surface for F0065 S0005: assessment outcome, selected guideline/version, time basis, comparison and evidence/review links, with distinct loading/error/unknown/conflict states. F0065 owns the extension and depends on this base view; do not introduce the reverse dependency.

See the [example coverage map](../../examples/README.md) and [F0065](../F0065-grounded-gl-guideline-assessment/README.md).
