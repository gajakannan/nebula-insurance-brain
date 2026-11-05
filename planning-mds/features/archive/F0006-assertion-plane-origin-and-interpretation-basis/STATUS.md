# F0006 — Assertion plane + origin + interpretation basis — Status

**Overall Status:** Done — archived; approved trusted local synthetic-fixture scope
**Last Updated:** 2026-11-05
**Plan Run:** `2026-11-01-7d6d19ce` — A+B, new
**Phase A:** Approved by operator token `approve-phase-a` on 2026-11-01; G3 passed
**Phase B:** Approved by operator token `approve-phase-b` on 2026-11-01 after green preapproval exit checks; final G5 publication is recorded in the plan run manifest/journal
**Phase B rework:** Correction basis/persistence (plan-review AR-1/AR-2) re-approved by operator token `approve-phase-b` on 2026-11-01 in plan run `2026-11-01-512e9303` (PHASE=B, existing)
**Implementation:** Run `2026-11-02-5a00b0ff`; all five stories and 35 acceptance criteria verified, required signoffs complete, operator G4 mitigation approval recorded; PM archive checkpoint 2026-11-05

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0006-S0001 | Preserve typed source claims | Done |
| F0006-S0002 | Retain open statements and version contracts | Done |
| F0006-S0003 | Check structural admission and evidence | Done |
| F0006-S0004 | Guard mood and described evidence | Done |
| F0006-S0005 | Preserve existing consumer boundaries | Done |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0006-S0001 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0006-S0002 | done | not-in-scope | done | done | PASS | PASS | done | done |
| F0006-S0003 | done | not-in-scope | done | done | PASS | PASS | done | done |
| F0006-S0004 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0006-S0005 | done | not-in-scope | done | done | PASS | PASS | done | done |

All required implementation, QE, review and deployability cells are complete. AI cells cover shared result/importer compatibility only. The operator approved the SEC-01 bounded mitigation at G4; all five required roles have current named evidence below. No model, prompt or live producer activation is included.

## Required Role Matrix

Architect-set completion roles reaffirmed at G0; PM verified all required role verdicts at G5 in run `2026-11-02-5a00b0ff`. See evidence and provenance below.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | Acceptance criteria and regression evidence | Architect | 2026-11-01 |
| Code Reviewer | Yes | Independent correctness and compatibility review | Architect | 2026-11-01 |
| Security Reviewer | Yes | Source access, restriction inheritance and non-disclosure | Architect | 2026-11-01 |
| DevOps | Yes | Additive migration, packaged schemas and guarded rollout/rollback | Architect | 2026-11-01 |
| Architect | Yes | Semantic, evidence and legacy compatibility constraints | Architect | 2026-11-01 |

## Story Signoff Provenance

Append-only history. PM records the required reviewers' report verdicts and verifies their evidence. Latest row per story/role determines the current verdict; source review dates remain in the reports.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0006-S0001 | Quality Engineer | Codex / Quality Engineer (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0001 | Code Reviewer | Codex / Code Reviewer (g3_code_review) | APPROVED | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/code-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0001 | Security Reviewer | Codex / Security Reviewer (g3_security_review) | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/security-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0001 | DevOps | Codex / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/deployability-check.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0001 | Architect | Codex / Architect (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/architect-implementation-review.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0002 | Quality Engineer | Codex / Quality Engineer (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0002 | Code Reviewer | Codex / Code Reviewer (g3_code_review) | APPROVED | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/code-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0002 | Security Reviewer | Codex / Security Reviewer (g3_security_review) | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/security-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0002 | DevOps | Codex / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/deployability-check.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0002 | Architect | Codex / Architect (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/architect-implementation-review.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0003 | Quality Engineer | Codex / Quality Engineer (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0003 | Code Reviewer | Codex / Code Reviewer (g3_code_review) | APPROVED | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/code-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0003 | Security Reviewer | Codex / Security Reviewer (g3_security_review) | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/security-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0003 | DevOps | Codex / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/deployability-check.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0003 | Architect | Codex / Architect (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/architect-implementation-review.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0004 | Quality Engineer | Codex / Quality Engineer (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0004 | Code Reviewer | Codex / Code Reviewer (g3_code_review) | APPROVED | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/code-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0004 | Security Reviewer | Codex / Security Reviewer (g3_security_review) | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/security-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0004 | DevOps | Codex / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/deployability-check.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0004 | Architect | Codex / Architect (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/architect-implementation-review.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0005 | Quality Engineer | Codex / Quality Engineer (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0005 | Code Reviewer | Codex / Code Reviewer (g3_code_review) | APPROVED | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/code-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0005 | Security Reviewer | Codex / Security Reviewer (g3_security_review) | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/security-review-report.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0005 | DevOps | Codex / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/deployability-check.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |
| F0006-S0005 | Architect | Codex / Architect (g0_architect) | PASS | `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/architect-implementation-review.md` | 2026-11-04 | PM verified role evidence; SEC-01 bounded mitigation accepted at G4 where applicable |

## Planning Decisions and Delivery Boundaries

- F0006 is the storage/contracts/admission-checks/review-hooks feature described in the dated README amendment and PRD. It adds no screen or permission grant.
- Existing `direct-baseline` and v1 writer defaults follow the final F0005 rejection decision. New assertion contract versions do not enable v2 content publication or a new extraction pipeline.
- F0016 owns durable drops, full interpretation outcomes and time mentions; F0018 owns full canonical orchestration; F0022 owns new display; F0066 owns open extraction/alignment. Those are scope boundaries, not unfinished F0006 acceptance criteria.
- Proposed ADR-0065 remains Proposed; the plan does not claim its broader proof gates passed.

## Tracker Sync

PM archive checkpoint 2026-11-05T01:08:31.640933+00:00: the feature shard records Archived/Completed and archive paths. `compile.py` generates REGISTRY/ROADMAP and feature mappings from that shard; the story index is regenerated from the five Done stories. BLUEPRINT section 4.12 records the bounded implementation. Actual tracker, story and KG results are in `planning-mds/operations/evidence/runs/2026-11-02-5a00b0ff/lifecycle-gates.log` and `gate-state.json`; G8 must pass before completion is published.

## Closeout Summary

| Field | Value |
|---|---|
| Closeout review date | 2026-11-05 |
| Implementation date | 2026-11-05 |
| Archived date | 2026-11-05 |
| Feature run | `2026-11-02-5a00b0ff` |

- Implementation and archive date: 2026-11-05; feature run `2026-11-02-5a00b0ff`.
- Scope delivered: five stories / 35 ACs for typed/open assertion storage, versioned contracts, structural admission, source/evidence integrity and current consumer guards.
- Final product lanes: 306 engine + 15 importer + ten recovery + five existing content-worker cases = 336 unique passing cases. Additional focused/migration lanes overlap; two basis-boundary probes are separate diagnostics.
- Changed-code coverage: 1170/1266 executable changed production lines (92.4171%), 20 files, no waiver or instrumentation gaps.
- Review repairs: A-IMPL-01 carrier page/bbox integrity and SEC-04/A-IMPL-02 pre-READ payload materialization fixed and independently verified. Historical failures/retries remain preserved.
- Operator G4 approval explicitly accepts SEC-01 for trusted local synthetic fixtures only. Dependency remediation/qualification and verified memory/CPU/process isolation are required before untrusted or production PDFs.
- Required role signoffs: five roles for all five stories (25 provenance entries), with reviewer, ISO date and durable run evidence. SEC-05 disposition is verified in the Architect's G7 and Security reports.
- No orphaned stories. Existing direct-baseline/v1 defaults remain; ADR-0065/0075 stay Proposed. F0016/F0018/F0022/F0066 scope remains with those features.
- Evidence: [PM closeout](../../../operations/evidence/runs/2026-11-02-5a00b0ff/pm-closeout.md), [test report](../../../operations/evidence/runs/2026-11-02-5a00b0ff/test-execution-report.md), [Security review](../../../operations/evidence/runs/2026-11-02-5a00b0ff/security-review-report.md).

## Deferred Non-Blocking Follow-ups

| Item | Severity | Owner | Follow-up |
|---|---|---|---|
| SEC-01 conversion dependencies/PDF resource exposure | High | AI Engineer + DevOps; Security verifies | 2026-11-10 and before untrusted/production PDF ingestion; trusted local synthetic fixtures only until remediation and resource-isolation qualification |
| SEC-02 inherited global security-planning audit gaps | Medium | Security + Architect | 2026-11-10 and before production security qualification; complete baseline artifacts and rerun strict audit |
| SEC-03 public nosniff header | Low | Backend Developer + DevOps | 2026-11-17; harden public/protected/error responses and verify |

Named acceptance: Codex / Product Manager under the operator's explicit G4 approval. Exact accepted wording and scope are in gate-decisions.md and mirrored in pm-closeout.md under the run. These remain technical follow-ups; no production or new producer activation is granted.
