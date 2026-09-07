# F0055 — Native reasoning

**Status:** Planned
**Phase:** v0.4+
**Roadmap:** Later

## Overview

Generalized native ontology inference and broader business-rule composition extend the bounded F0065 v0.1 evaluator, preserving exact inputs, rule versions, evidence, and explicit rejection of unsupported constructs (sections 45, 92, 112, 124).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0001](../../architecture/decisions/ADR-0001-the-brain-owns-semantics.md), [ADR-0012](../../architecture/decisions/ADR-0012-flexible-authoring-normalized-runtime.md). Likely predecessors (inferred, confirm at Phase B): F0030, F0056.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0055.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Scope amendment and required story acceptance (2026-09-07)

- F0065 owns the v0.1 fixed monetary comparison, immutable assessment, and on-demand evaluation contract.
- F0055 owns broader ontology inference, rule composition/chaining, and additional supported constructs. Reuse F0065 identities and provenance; do not redefine confidence or approval semantics.
- F0030/F0056 remain likely dependencies for this broader feature, not prerequisites for F0065.

Reference: [EX-GL-001](../../examples/neurosymbolic-gl/README.md), [cases](../../examples/neurosymbolic-gl/cases.md), and [F0065](../F0065-grounded-gl-guideline-assessment/README.md). These requirements must be carried into this feature's PRD/stories when planned; runtime and feature status remain Planned.
