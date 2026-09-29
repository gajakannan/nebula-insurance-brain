# F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts — Status

**Overall Status:** Done and Archived — feature action run `2026-09-27-bb7c8d1d` complete (G0–G8 passed; G4 approved by the user after one fix-issues cycle)
**Last Updated:** 2026-09-28
**Archival note:** Moved to `planning-mds/features/archive/F0002-tenancy-aware-domain-kernel-and-principal-contracts/` on 2026-09-28. Other features reference F0002 through its kg-source shard `path:`; hand-authored links in the blueprint, ADRs, data model, glossary and examples were repointed in the same change.
**Feature run:** `2026-09-27-bb7c8d1d` (branch `feature/F0002-tenancy-kernel`)
**Planning:** Phase A approved; G1–G3 passed. Phase B design approved by user (`approve-phase-b`, 2026-09-25); G4 and all automated G5 checks passed.
**Plan run:** `2026-09-25-3c64470a`

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0002-S0001 | Preserve structural tenancy and tenant-scoped entity identity | Done |
| F0002-S0002 | Resolve verified credentials to stable typed principals | Done |
| F0002-S0003 | Resolve current memberships and intersect requested scope | Done |
| F0002-S0004 | Enforce parent, classification and source restrictions together | Done |
| F0002-S0005 | Bound delegated and autonomous service authority | Done |
| F0002-S0006 | Prove audited kernel behavior through existing consumers | Done |

## Story × Role Progress

Live during feature run `2026-09-27-bb7c8d1d`. Implementation, QA and DevOps cells flipped at G2; Code Review and Security resolved PASS at G3 (APPROVED WITH RECOMMENDATIONS / PASS WITH RECOMMENDATIONS; 0 critical, 0 high). Overall resolved Done at G8 after approval, signoff and closeout.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0002-S0001 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0002-S0002 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0002-S0003 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0002-S0004 | done | not-in-scope | done (worker CLI trusted submission) | done | PASS | PASS | done | Done |
| F0002-S0005 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |
| F0002-S0006 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | Done |

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
- [x] Implementation evidence and required review provenance captured in feature run `2026-09-27-bb7c8d1d`.

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

Append-only. Rows below record the feature run `2026-09-27-bb7c8d1d` signoffs (G5, 2026-09-28). The last twelve rows are the G8 closeout rows: `validate-trackers` counts only a `PASS`/`APPROVED` verdict, so Security Reviewer and DevOps are recorded as PASS once the PM accepted their recommendations. The G5 rows are left unchanged.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0002-S0001 | Quality Engineer | gajakannan (Claude, Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/test-execution-report.md | 2026-09-28 | EX-AUTHX ledger + coverage 94.04% |
| F0002-S0001 | Code Reviewer | gajakannan (Claude, Code Reviewer role) | APPROVED | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/code-review-report.md | 2026-09-28 | cycle 2; all recommendations fixed |
| F0002-S0001 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md | 2026-09-28 | 0 critical/high; medium edge rate limiting (F0021/F0026), low JWKS metric |
| F0002-S0001 | DevOps | gajakannan (Claude, DevOps role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/deployability-check.md | 2026-09-28 | migrations 0005–0007, round trip, restore drill; low isolated test DB |
| F0002-S0001 | Architect | gajakannan (Claude, Architect role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/g0-assembly-plan-validation.md | 2026-09-28 | as-built matches plan (g2-self-review Architect confirmation); schema/ADRs unchanged |
| F0002-S0002 | Quality Engineer | gajakannan (Claude, Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/test-execution-report.md | 2026-09-28 | EX-AUTHX ledger + coverage 94.04% |
| F0002-S0002 | Code Reviewer | gajakannan (Claude, Code Reviewer role) | APPROVED | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/code-review-report.md | 2026-09-28 | cycle 2; all recommendations fixed |
| F0002-S0002 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md | 2026-09-28 | 0 critical/high; medium edge rate limiting (F0021/F0026), low JWKS metric |
| F0002-S0002 | DevOps | gajakannan (Claude, DevOps role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/deployability-check.md | 2026-09-28 | migrations 0005–0007, round trip, restore drill; low isolated test DB |
| F0002-S0002 | Architect | gajakannan (Claude, Architect role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/g0-assembly-plan-validation.md | 2026-09-28 | as-built matches plan (g2-self-review Architect confirmation); schema/ADRs unchanged |
| F0002-S0003 | Quality Engineer | gajakannan (Claude, Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/test-execution-report.md | 2026-09-28 | EX-AUTHX ledger + coverage 94.04% |
| F0002-S0003 | Code Reviewer | gajakannan (Claude, Code Reviewer role) | APPROVED | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/code-review-report.md | 2026-09-28 | cycle 2; all recommendations fixed |
| F0002-S0003 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md | 2026-09-28 | 0 critical/high; medium edge rate limiting (F0021/F0026), low JWKS metric |
| F0002-S0003 | DevOps | gajakannan (Claude, DevOps role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/deployability-check.md | 2026-09-28 | migrations 0005–0007, round trip, restore drill; low isolated test DB |
| F0002-S0003 | Architect | gajakannan (Claude, Architect role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/g0-assembly-plan-validation.md | 2026-09-28 | as-built matches plan (g2-self-review Architect confirmation); schema/ADRs unchanged |
| F0002-S0004 | Quality Engineer | gajakannan (Claude, Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/test-execution-report.md | 2026-09-28 | EX-AUTHX ledger + coverage 94.04% |
| F0002-S0004 | Code Reviewer | gajakannan (Claude, Code Reviewer role) | APPROVED | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/code-review-report.md | 2026-09-28 | cycle 2; all recommendations fixed |
| F0002-S0004 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md | 2026-09-28 | 0 critical/high; medium edge rate limiting (F0021/F0026), low JWKS metric |
| F0002-S0004 | DevOps | gajakannan (Claude, DevOps role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/deployability-check.md | 2026-09-28 | migrations 0005–0007, round trip, restore drill; low isolated test DB |
| F0002-S0004 | Architect | gajakannan (Claude, Architect role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/g0-assembly-plan-validation.md | 2026-09-28 | as-built matches plan (g2-self-review Architect confirmation); schema/ADRs unchanged |
| F0002-S0005 | Quality Engineer | gajakannan (Claude, Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/test-execution-report.md | 2026-09-28 | EX-AUTHX ledger + coverage 94.04% |
| F0002-S0005 | Code Reviewer | gajakannan (Claude, Code Reviewer role) | APPROVED | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/code-review-report.md | 2026-09-28 | cycle 2; all recommendations fixed |
| F0002-S0005 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md | 2026-09-28 | 0 critical/high; medium edge rate limiting (F0021/F0026), low JWKS metric |
| F0002-S0005 | DevOps | gajakannan (Claude, DevOps role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/deployability-check.md | 2026-09-28 | migrations 0005–0007, round trip, restore drill; low isolated test DB |
| F0002-S0005 | Architect | gajakannan (Claude, Architect role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/g0-assembly-plan-validation.md | 2026-09-28 | as-built matches plan (g2-self-review Architect confirmation); schema/ADRs unchanged |
| F0002-S0006 | Quality Engineer | gajakannan (Claude, Quality Engineer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/test-execution-report.md | 2026-09-28 | EX-AUTHX ledger + coverage 94.04% |
| F0002-S0006 | Code Reviewer | gajakannan (Claude, Code Reviewer role) | APPROVED | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/code-review-report.md | 2026-09-28 | cycle 2; all recommendations fixed |
| F0002-S0006 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/security-review-report.md | 2026-09-28 | 0 critical/high; medium edge rate limiting (F0021/F0026), low JWKS metric |
| F0002-S0006 | DevOps | gajakannan (Claude, DevOps role) | PASS WITH RECOMMENDATIONS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/deployability-check.md | 2026-09-28 | migrations 0005–0007, round trip, restore drill; low isolated test DB |
| F0002-S0006 | Architect | gajakannan (Claude, Architect role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/g0-assembly-plan-validation.md | 2026-09-28 | as-built matches plan (g2-self-review Architect confirmation); schema/ADRs unchanged |
| F0002-S0001 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendations were PM-accepted as deferred follow-ups in pm-closeout.md |
| F0002-S0001 | DevOps | gajakannan (Claude, DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendation was PM-accepted as a deferred follow-up in pm-closeout.md |
| F0002-S0002 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendations were PM-accepted as deferred follow-ups in pm-closeout.md |
| F0002-S0002 | DevOps | gajakannan (Claude, DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendation was PM-accepted as a deferred follow-up in pm-closeout.md |
| F0002-S0003 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendations were PM-accepted as deferred follow-ups in pm-closeout.md |
| F0002-S0003 | DevOps | gajakannan (Claude, DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendation was PM-accepted as a deferred follow-up in pm-closeout.md |
| F0002-S0004 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendations were PM-accepted as deferred follow-ups in pm-closeout.md |
| F0002-S0004 | DevOps | gajakannan (Claude, DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendation was PM-accepted as a deferred follow-up in pm-closeout.md |
| F0002-S0005 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendations were PM-accepted as deferred follow-ups in pm-closeout.md |
| F0002-S0005 | DevOps | gajakannan (Claude, DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendation was PM-accepted as a deferred follow-up in pm-closeout.md |
| F0002-S0006 | Security Reviewer | gajakannan (Claude, Security Reviewer role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendations were PM-accepted as deferred follow-ups in pm-closeout.md |
| F0002-S0006 | DevOps | gajakannan (Claude, DevOps role) | PASS | planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/pm-closeout.md | 2026-09-28 | G8 closeout: the G5 PASS WITH RECOMMENDATIONS stands; its recommendation was PM-accepted as a deferred follow-up in pm-closeout.md |

## Scope and Deferred Features

New business-role grants are not included. Session/BFF is F0021; full review UI is F0022; full canonical orchestration is F0018; cross-runtime parity and production hardening are F0026. These exclusions do not waive F0002’s own kernel and bounded-consumer acceptance criteria.

## Tracker Sync Checklist

- [x] REGISTRY/ROADMAP regenerated from the kg-source shard: Archived / Completed (2026-09-28).
- [x] STORY-INDEX regenerated for six Done stories at the archive path.
- [x] BLUEPRINT section 3.3 moves F0002 to Completed with archive links; sections 4.7, 4.10 and 4.11 record ADR acceptance and the 0007 safeguards.
- [x] Scoped validate-trackers passes at G6 and G8 (run `2026-09-27-bb7c8d1d` lifecycle-gates.log).

## Closeout Summary

- **Completed:** 2026-09-28. Feature run `2026-09-27-bb7c8d1d` (evidence: `planning-mds/operations/evidence/runs/2026-09-27-bb7c8d1d/`, pm-closeout.md).
- **Delivered:** all six stories through every existing consumer (content, fact, review, commit, F0005 worker). EX-AUTHX-001–018 were observed as expected. Engine 282 and neuron 75 tests pass. Changed-kernel coverage is 94.04%. Migrations 0005–0007 were applied, round-tripped and restore-drilled.
- **Scope amendment:** BLUEPRINT §4.11 safeguards (immutable ownership, append-only audit, deferrable self-references), implemented as migration 0007 at the user's G4 selection.
- **Decisions:** ADR-0061/0062 accepted for the bounded F0002 scope; ADR-0042/0052/0053 remain Proposed.
- **Deferred follow-ups (accepted in pm-closeout.md):**
  - [medium] Edge rate limiting for authentication events (F0021/F0026).
  - [low] JWKS-outage metric.
  - [low] Isolated per-run database for the engine PostgreSQL suites.
