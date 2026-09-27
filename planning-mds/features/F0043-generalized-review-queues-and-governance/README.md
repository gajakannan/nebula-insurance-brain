# F0043 — Generalized review queues / governance

**Status:** Planned
**Phase:** v0.2B
**Roadmap:** Later

## Overview

Review queues generalize beyond extraction correction to conflicts, merges, candidates, and promotions, with the Nebula Review Panel kept for evidence-oriented adjudication and business approval kept separate (sections 75, 111.2, 125). Queues whose subject is a proposal rather than a document region use a governance workbench surface; both are native, and both produce Nebula-owned decisions.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0057](../../architecture/decisions/ADR-0057-nebula-owns-the-native-evidence-review-panel.md), [ADR-0044](../../architecture/decisions/ADR-0044-review-surface-and-approval-contract.md). Likely predecessors (inferred, confirm at Phase B): F0022.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0043.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md), [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), [ADR-0067](../../architecture/decisions/ADR-0067-automation-gated-by-unrecallable-impact.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Add `SIGNATURE_ALIGNMENT`, `IMPLICATION_RULE`, and `TIME_ANCHOR` queues (ADR-0063, ADR-0064).
- Automated deciders on any queue follow ADR-0067: human-only precedent, impact holds shown as reasons, the people's service paths with a recorded undo, and a revert fuse. Every automation type starts disabled until its agreement with human decisions is measured.
