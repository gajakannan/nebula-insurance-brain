# F0026 — v0.1 hardening + Golden Corpus workflow + AuthX negative tests and policy parity

**Status:** Planned
**Phase:** v0.1C
**Roadmap:** Later

## Overview

v0.1 hardening closes Golden Corpus, AuthX, recovery, revocation, and independent frozen evaluation gates, including F0065 assessment correctness, lineage, temporal freshness, and complete derived-result access (sections 96, 115, 121, 124).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0048](../../architecture/decisions/ADR-0048-pilot-evidence-and-operational-readiness.md), [ADR-0053](../../architecture/decisions/ADR-0053-permission-safe-retrieval-and-historical-access.md), [ADR-0057](../../architecture/decisions/ADR-0057-nebula-owns-the-native-evidence-review-panel.md).

The Golden Corpus is exported from Nebula review decisions, not from an external labeling project: ground-truth creation and production correction are the same surface producing the same records (section 96, ADR-0057).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0026.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Scope amendment and required story acceptance (2026-09-07)

- Map EX-GL-001 CASE-01–19 to runtime evidence; prove the real F0024 neural-to-symbolic path and F0025 temporal reassessment.
- Report extraction precision/recall, severe errors, abstention and review workload separately from deterministic rule correctness and end-to-end assessment outcomes; record sample sizes, latency, and cost.
- Cover unsupported rules, exact-decimal boundaries, unknown/conflict, stale-result prevention, idempotency, concurrency, and revocation through result/history/title/count/explanation/citation.
- Keep worked examples outside the independently frozen holdout. Production quality thresholds and licensed corpus/owners must be settled before release.
- Require the example/contract/story links and executable reproduction evidence; planning schema validation alone does not pass this gate.

Reference: [EX-GL-001](../../examples/neurosymbolic-gl/README.md), [cases](../../examples/neurosymbolic-gl/cases.md), and [F0065](../F0065-grounded-gl-guideline-assessment/README.md). These requirements must be carried into this feature's PRD/stories when planned; runtime and feature status remain Planned.
