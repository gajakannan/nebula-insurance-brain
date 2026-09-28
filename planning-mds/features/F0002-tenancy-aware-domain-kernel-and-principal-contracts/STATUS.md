# F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts — Status

**Overall Status:** In Progress
**Last Updated:** 2026-09-27
**Feature run:** `2026-09-27-bb7c8d1d` (branch `feature/F0002-tenancy-kernel`)
**Planning:** Phase A approved; G1–G3 passed. Phase B design approved by user (`approve-phase-b`, 2026-09-25); G4 and all automated G5 checks passed.
**Plan run:** `2026-09-25-3c64470a`

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0002-S0001 | Preserve structural tenancy and tenant-scoped entity identity | Not Started |
| F0002-S0002 | Resolve verified credentials to stable typed principals | Not Started |
| F0002-S0003 | Resolve current memberships and intersect requested scope | Not Started |
| F0002-S0004 | Enforce parent, classification and source restrictions together | Not Started |
| F0002-S0005 | Bound delegated and autonomous service authority | Not Started |
| F0002-S0006 | Prove audited kernel behavior through existing consumers | Not Started |

## Story × Role Progress

Live during feature run `2026-09-27-bb7c8d1d`. Implementation, QA and DevOps cells flipped at G2; Code Review and Security resolved PASS at G3 (APPROVED WITH RECOMMENDATIONS / PASS WITH RECOMMENDATIONS; 0 critical, 0 high). Overall stays In Progress until approval, signoff and closeout.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0002-S0001 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | In Progress |
| F0002-S0002 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | In Progress |
| F0002-S0003 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | In Progress |
| F0002-S0004 | done | not-in-scope | done (worker CLI trusted submission) | done | PASS | PASS | done | In Progress |
| F0002-S0005 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | In Progress |
| F0002-S0006 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | In Progress |

## Backend Progress

- [x] Ownership and stable principal contracts implemented with compatible migration (0005 expand / 0006 constrain; reviewed reconciliation script).
- [x] Current scope and conjunctive resource checks integrated (shared pure evaluator; content/fact/review/commit/worker consumers).
- [x] Bounded delegation and durable audit implemented (execution facade; authentication-event sink).
- [x] Existing consumers and negative cases reproduce contract outcomes (EX-AUTHX-001–018 ledger in run `2026-09-27-bb7c8d1d` test-execution-report.md).

## Frontend Progress

N/A — no UI changes in F0002.

## Cross-Cutting

- [x] Phase A approved by user (`approve-phase-a`, 2026-09-25).
- [x] Phase B contracts, assembly plan and ontology synchronized; automated exit validation passed.
- [x] Phase B explicitly approved by user at G5 (`approve-phase-b`, 2026-09-25).
- [x] Regression and acceptance tests pass; changed kernel coverage at least 80% (93.74%; engine 277 passed, neuron 75 passed — run `2026-09-27-bb7c8d1d`).
- [ ] Implementation evidence and required review provenance captured in a later feature run.

## Required Role Matrix

Validator-read matrix (mirrors the planning table below; unchanged by the feature run).

| Role | Required |
|---|---|
| Quality Engineer | Yes |
| Code Reviewer | Yes |
| Security Reviewer | Yes |
| DevOps | Yes |
| Architect | Yes |

## Required Signoff Roles (Set in Planning)

Architect set the required matrix for all six stories on 2026-09-25. No implementation signoff has occurred.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | Acceptance, isolation, migration and negative-case evidence | Architect | 2026-09-25 |
| Code Reviewer | Yes | Independent correctness/regression review | Architect | 2026-09-25 |
| Security Reviewer | Yes | Identity, grants, restrictions, delegation and audit boundaries | Architect | 2026-09-25 |
| DevOps | Yes | Runtime configuration, migrations, recovery and deployment safety | Architect | 2026-09-25 |
| Architect | Yes | Shared contracts, ownership and cross-feature compatibility | Architect | 2026-09-25 |

## Story Signoff Provenance

Append-only; no implementation reviews have occurred.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Scope and Deferred Features

New business-role grants are not included. Session/BFF is F0021; full review UI is F0022; full canonical orchestration is F0018; cross-runtime parity and production hardening are F0026. These exclusions do not waive F0002’s own kernel and bounded-consumer acceptance criteria.

## Tracker Sync Checklist

- [x] REGISTRY/ROADMAP generated status and path remain Planned / Next.
- [x] STORY-INDEX regenerated for six Not Started stories.
- [x] BLUEPRINT section 3 links match these stories.
- [x] G2 story/tracker checks passed.

## Closeout Summary

Not applicable at plan. Implementation not started; no completion date, passing review or approved feature evidence package is asserted.
