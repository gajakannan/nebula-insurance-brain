# F0014 — Document Profile model

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Document profiles select which ontology modules and extraction profiles apply to a document type and business context (section 7). Nebula selects the released profile before the Docling-Graph pipeline executes.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0014](../../architecture/decisions/ADR-0014-document-profiles-drive-interpretation.md).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0014.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15)

> **F0005 outcome (2026-10-28) supersedes the scope amendment below.** Graph dense was qualified live and rejected (F0005 run `2026-10-25-4020923b`, PR #30).
> - **Defaults:** `direct-baseline` and the v1 writer stay the defaults.
> - **ADR-0060 status:** stays **Proposed**, with a reopen deadline. **At F0014/F0015 Phase A planning the operator decides** whether to re-plan a Graph candidate (a larger output reservation, another serving model, or Graph direct, each with full re-qualification) or to mark ADR-0060 **Rejected**.
> - **Until then:** plan against the direct baseline and the accepted execution controls in [ADR-0074](../../architecture/decisions/ADR-0074-local-document-job-execution-controls.md). Read the Docling-Graph requirements below as conditional on a re-plan.
> - **A Graph re-plan must also carry** F0005's activation preconditions (SEC-F5-M1 converter isolation, Docling ≥ 2.132 / pillow ≥ 13 requalification, the SEC-F5-L4 residual) and its qualification process fixes: commit the corpus with its generation command, write `commands.log` at execution time, retain predicted values, add a table-aware baseline, and define OCR-count semantics in the AC. Source: the [F0005 PM closeout](../../operations/evidence/runs/2026-10-25-4020923b/pm-closeout.md).

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governs this planned work. Carry these requirements into the feature PRD/stories; status remains Planned.

- Pass the selected profile/version to the F0015 compiler and F0016 run; do not delegate tenant policy, document classification authority, or ontology release selection to upstream graph inference.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Each document profile section declares `interpretation_route` (`TEMPLATE`, `OPEN`, `TEMPLATE_AND_OPEN`). v0.1 GL profiles use `TEMPLATE`; `OPEN` is activated per profile only after F0066's parity gate (ADR-0063).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
