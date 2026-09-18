# F0005 — One-time document ingestion

**Status:** Planned feature; candidate compatibility work in progress. Production delivery and ADR acceptance remain pending.
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Process each document version into an immutable content artifact and reuse it for later interpretations. Proposed [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) evaluates Docling-Graph as the coordinator, with Docling underneath and Nebula owning persistence, evidence, durable jobs, and canonical authority. The existing folder path remains stable for references.

## Documents

- [PRD](PRD.md): scope and acceptance.
- [Assembly plan](feature-assembly-plan.md): package ownership, checkpoint handoff, sequencing, and proof gates.
- [Status](STATUS.md): recommendation audit, pending proofs, and actual signoffs.
- [Getting started](GETTING-STARTED.md): current baseline and planning checks.

## Stories

| ID | Title | Status |
|---|---|---|
| [F0005-S0001](F0005-S0001-pin-and-process-source-documents.md) | Pin and process source documents | In Progress |
| [F0005-S0002](F0005-S0002-persist-artifacts-and-recover-jobs.md) | Persist artifacts and recover jobs | In Progress |
| [F0005-S0003](F0005-S0003-reinterpret-saved-json-and-map-evidence.md) | Reinterpret saved JSON and map evidence | In Progress |
| [F0005-S0004](F0005-S0004-evaluate-and-activate-proven-pipeline.md) | Evaluate and activate the proven pipeline | Not Started |

**Total Stories:** 4

F0004 is an explicit prerequisite. Fixed proof templates avoid a dependency cycle with the later F0015 compiler. F0016/F0032 carry the production run and targeted-evolution requirements; F0026 carries release qualification. Archived F0001 remains unchanged.
