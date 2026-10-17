# F0004 — Content artifact model — Status

**Overall Status:** Planned\
**Delivery Status:** Planned — v0.1A; roadmap Next\
**Last Updated:** 2026-10-16\
**Plan Run:** `2026-10-15-bbd8df01`

## Planning Position

Phase A approved by operator “proceed with Phase B”; G1–G3 passed. Phase B design explicitly approved with `approve-phase-b` on 2026-10-16 after G4 and all seven G5 exit checks passed. The plan is ready for the separate feature action. Registry/roadmap retain Planned/Next. Planning does not authorize implementation or change delivery priority.

## Story Checklist

| Story | Title | Status |
|---|---|---|
| [F0004-S0001](F0004-S0001-publish-and-reuse-content-bundle.md) | Publish and reuse an immutable content bundle | Not Started |
| [F0004-S0002](F0004-S0002-content-structure-and-text-origin.md) | Preserve content structure and text origin | Not Started |
| [F0004-S0003](F0004-S0003-document-date-provenance.md) | Preserve document-date provenance | Not Started |
| [F0004-S0004](F0004-S0004-authorized-consumers-and-compatibility.md) | Protect artifact consumers and compatibility | Not Started |

## Story × Role Progress

All four stories are Not Started. Backend, document-intelligence integration and QA work remain for the feature action. No frontend screen is in scope. The final planned review matrix requires Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect for each story.

## Backend Progress

- [ ] Versioned content/date contracts and durable integration implemented.
- [ ] Publication, authorized consumer reads and history verified.
- [ ] Compatibility, restart, failure and restore cases pass.

## Frontend Progress

N/A — no new screen or control. Existing evidence consumers must stay compatible.

## Required Signoff Roles (Set in Planning)

| Role | Required | Why Required | Set By |
|---|---|---|---|
| Quality Engineer | Yes | Framework minimum; acceptance and negative cases | Product Manager — baseline |
| Code Reviewer | Yes | Framework minimum; contract/integration review | Product Manager — baseline |
| Security Reviewer | Yes | Current authorization, origin/date authority and owner constraints | Architect — Phase B |
| DevOps | Yes | Additive migration, restart and isolated restore proof | Architect — Phase B |
| Architect | Yes | Versioned contract and ADR reconciliation | Architect — Phase B |

All five roles apply to all four stories. No implementation review or signoff has occurred.

## Story Signoff Provenance

Append-only history; no signoffs yet.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Phase Boundaries and Design Handoff

- Approved assembly plan, versioned schemas/API boundary, compatibility matrix, ADR reconciliation and KG source bindings are the implementation baseline.
- Preserve accepted PDF/BoxSelector behavior; do not imply full W3C/OOXML or new transcription/description engine delivery.
- Document date and text origin are bounded storage/contract carry-ins; broader ADR-0064/0065 behavior stays Proposed.
- F0005 production activation and F0026 release qualification remain separate.

## Tracker Sync Checklist

Story index and BLUEPRINT links include all four stories. REGISTRY/ROADMAP remain Planned/Next. Story and tracker validation passed; the earlier strict story pass retained one nonblocking dependency advisory. KG drift/reproducibility and template validation passed. Phase A and Phase B approvals are recorded in the plan run. Implementation remains 0/4 stories.

## Closeout Summary

Planning approved; 0/4 stories implemented. Runtime tests and delivery signoffs remain for the feature action. ADR-0073 stays Proposed until its runtime proof gates pass.
