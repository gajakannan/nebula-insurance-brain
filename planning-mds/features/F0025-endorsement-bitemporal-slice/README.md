# F0025 — Endorsement bitemporal slice

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

The endorsement slice proves both fact and F0065 assessment answers at distinct valid/recorded coordinates after retroactive endorsement, preserving historical results and current access checks (sections 87, 124).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0007](../../architecture/decisions/ADR-0007-full-bitemporality.md), [ADR-0009](../../architecture/decisions/ADR-0009-explicit-change-semantics.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0025.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Scope amendment and required story acceptance (2026-09-07)

- Integrate F0065 reassessment: July 5 as known July 8 uses the old limit; July 5 as known July 11 uses the endorsement accepted July 10; June 30 remains unchanged.
- Preserve old assessments and exact input/rule versions. Current requests recompute from a new consistent snapshot; historical requests never restore historical grants.
- Include correction/retraction and concurrent-commit cases from the shared challenge table.
- Depends on F0065 for assessment integration; the full F0056 propagation engine is not required.

Reference: [EX-GL-001](../../examples/neurosymbolic-gl/README.md), [cases](../../examples/neurosymbolic-gl/cases.md), and [F0065](../F0065-grounded-gl-guideline-assessment/README.md). These requirements must be carried into this feature's PRD/stories when planned; runtime and feature status remain Planned.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- **v0.1 decision (operator, 2026-09-25; validate finding P-1, option b):** F0025 acceptance does not depend on Proposed ADR-0064. The endorsement's valid time comes from the template route's typed effective-date field, reviewed as usual. Recorded time comes from canonical acceptance, and receipt time never dates the document.
- F0016 still stores the time mentions and document time context for every run, so v0.1 captures the data ADR-0064 needs. Resolving a date from a time mention replaces the template field only after ADR-0064 passes its proof gates.
- The grade-C "as of inception" case and the unknown-end case are ADR-0064 proof-gate cases, qualified by F0026. They are not F0025 acceptance criteria.
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
