# F0005 — One-time document ingestion

**Status:** Planned feature; synthetic development scope complete. Local qualification and gated activation re-planned and approved (Phase A and B) in plan run `2026-10-23-9a04b327`; feature action not started. ADR-0060 remains Proposed.
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Process each document version into an immutable content artifact and reuse it for later interpretations. Proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) evaluates Docling-Graph as the coordinator, with Docling underneath and Nebula owning persistence, evidence, durable jobs, and canonical authority. The existing folder path remains stable for references.

## Documents

- [PRD](PRD.md): scope and acceptance.
- [Assembly plan](feature-assembly-plan.md): reconciliation with shipped F0002–F0004, qualification steps, failure injection, pipeline selection, decision and rollback.
- [Status](STATUS.md): recommendation audit, pending proofs, and actual signoffs.
- [Acceptance criteria checklist](acceptance-criteria-checklist.md): per-criterion verification state.
- [Getting started](GETTING-STARTED.md): current baseline and planning checks.

## Stories

| ID | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | In Progress |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | In Progress |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | In Progress |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | In Progress — synthetic comparison complete |
| [F0005-S0005](F0005-S0005-qualify-text-origin-and-enable-v2-publication.md) | Qualify text origin and enable v2 publication | Not Started |

**Total Stories:** 5

F0004 is an explicit prerequisite. Fixed proof templates avoid a dependency cycle with the later F0015 compiler. F0016/F0032 carry the production run, document-date candidate production (operator decision 2026-10-23) and targeted-evolution requirements; F0026 carries release qualification. Archived F0001 remains unchanged.
