# F0006 — Assertion plane + origin + interpretation basis — Status

**Overall Status:** Draft — A+B planning approved; implementation not started
**Last Updated:** 2026-11-01
**Plan Run:** `2026-11-01-7d6d19ce` — A+B, new
**Phase A:** Approved by operator token `approve-phase-a` on 2026-11-01; G3 passed
**Phase B:** Approved by operator token `approve-phase-b` on 2026-11-01 after green preapproval exit checks; final G5 publication is recorded in the plan run manifest/journal
**Phase B rework:** Correction basis/persistence (plan-review AR-1/AR-2) re-approved by operator token `approve-phase-b` on 2026-11-01 in plan run `2026-11-01-512e9303` (PHASE=B, existing)
**Implementation:** Not started

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0006-S0001 | Preserve typed source claims | Not Started |
| F0006-S0002 | Retain open statements and version contracts | Not Started |
| F0006-S0003 | Check structural admission and evidence | Not Started |
| F0006-S0004 | Guard mood and described evidence | Not Started |
| F0006-S0005 | Preserve existing consumer boundaries | Not Started |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0006-S0001 | Not Started | — | — | Not Started | Not Started | Not Started | Not Started | Not Started |
| F0006-S0002 | Not Started | — | Not Started | Not Started | Not Started | Not Started | Not Started | Not Started |
| F0006-S0003 | Not Started | — | Not Started | Not Started | Not Started | Not Started | Not Started | Not Started |
| F0006-S0004 | Not Started | — | — | Not Started | Not Started | Not Started | Not Started | Not Started |
| F0006-S0005 | Not Started | — | Not Started | Not Started | Not Started | Not Started | Not Started | Not Started |

## Required Signoff Roles (Set in Planning)

Architect-set completion roles for the future feature action. None has signed off implementation.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | Acceptance criteria and regression evidence | Architect | 2026-11-01 |
| Code Reviewer | Yes | Independent correctness and compatibility review | Architect | 2026-11-01 |
| Security Reviewer | Yes | Source access, restriction inheritance and non-disclosure | Architect | 2026-11-01 |
| DevOps | Yes | Additive migration, packaged schemas and guarded rollout/rollback | Architect | 2026-11-01 |
| Architect | Yes | Semantic, evidence and legacy compatibility constraints | Architect | 2026-11-01 |

## Story Signoff Provenance

Append-only history. No implementation or role signoff has occurred. Latest row per story/role determines the current verdict; passing evidence belongs to the later feature action's run.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Planning Decisions and Delivery Boundaries

- F0006 is the storage/contracts/admission-checks/review-hooks feature described in the dated README amendment and PRD. It adds no screen or permission grant.
- Existing `direct-baseline` and v1 writer defaults follow the final F0005 rejection decision. New assertion contract versions do not enable v2 content publication or a new extraction pipeline.
- F0016 owns durable drops, full interpretation outcomes and time mentions; F0018 owns full canonical orchestration; F0022 owns new display; F0066 owns open extraction/alignment. Those are scope boundaries, not unfinished F0006 acceptance criteria.
- Proposed ADR-0065 remains Proposed; the plan does not claim its broader proof gates passed.

## Tracker Sync

Phase A strict story validation, story-index generation and tracker validation passed before G3, with zero tracker errors/warnings. Semantic educational examples also pass. The Architect-authored feature/node shards now map all five stories and the design contracts; G4 compiled the generated projections, removed the reserved exclusion and passed drift validation. Roadmap remains Next; planning this feature does not silently move implementation into Now.

## Closeout Summary

Not applicable yet. No implementation evidence, completion date or archive approval is claimed.
