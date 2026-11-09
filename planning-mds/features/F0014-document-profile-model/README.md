# F0014 — Document Profile model

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Document profiles select which ontology modules and extraction profiles apply to a document type and business context (section 7). Nebula selects the released profile before the direct-baseline extraction pipeline executes.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0014](../../architecture/decisions/ADR-0014-document-profiles-drive-interpretation.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0004, F0012 (previously F0001).
- ADR-0060 was Rejected by the operator on 2026-11-08 (the reopen decision this feature previously recorded). Plan against the direct-baseline pipeline (ADR-0055) and the ADR-0074 execution controls.
- Carry master blueprint 107.4 and ADR-0039 rule 6: a profile declares expected forms, pages and attachments; each package records expected versus received and is INCOMPLETE when a component is missing.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0014.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

> **F0005 outcome (2026-10-28) supersedes the scope amendment below.** Graph dense was qualified live and rejected (F0005 run `2026-10-25-4020923b`, PR #30).
> - **Defaults:** `direct-baseline` and the v1 writer stay the defaults.
> - **ADR-0060 status:** **Rejected** by the operator on 2026-11-08 (the reopen decision).
> - **Plan** against the direct baseline and the accepted execution controls in [ADR-0074](../../architecture/decisions/ADR-0074-local-document-job-execution-controls.md). The Docling-Graph-specific requirements below are withdrawn.
> - **A Graph re-plan must also carry** F0005's activation preconditions (SEC-F5-M1 converter isolation, Docling ≥ 2.132 / pillow ≥ 13 requalification, the SEC-F5-L4 residual) and its qualification process fixes: commit the corpus with its generation command, write `commands.log` at execution time, retain predicted values, add a table-aware baseline, and define OCR-count semantics in the AC. Source: the [F0005 PM closeout](../../operations/evidence/runs/2026-10-25-4020923b/pm-closeout.md).

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Pass the selected profile/version to the F0015 compiler and F0016 run; do not delegate tenant policy, document classification authority, or ontology release selection to upstream graph inference.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0063](../../architecture/decisions/ADR-0063-open-statements-and-signature-alignment.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Each document profile section declares `interpretation_route` (`TEMPLATE`, `OPEN`, `TEMPLATE_AND_OPEN`). v0.1 GL profiles use `TEMPLATE`; `OPEN` is activated per profile only after F0066's parity gate (ADR-0063).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).
