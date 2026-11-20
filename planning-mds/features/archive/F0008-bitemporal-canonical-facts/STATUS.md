# F0008 — Bitemporal canonical facts — Status

**Overall Status:** Done / Archived after remediation, 2026-11-19. Current run `2026-11-18-bce4909b` was approved by the operator at G4. The prior completion `2026-11-17-1a4ae2f0` is retained as superseded history.
**Last Updated:** 2026-11-19
**Plan Run:** `2026-11-16-208a1193` (A+B, new)
**Phase A:** Approved 2026-11-16 (`approve-phase-a`, G3 PASS)
**Phase B:** Approved 2026-11-17 (`approve-phase-b`, G5)
**Implementation:** Remediation completed in `2026-11-18-bce4909b` after review `2026-11-18-d34a095e`; the original completion `2026-11-17-1a4ae2f0` is retained as superseded history.
**Feature Run:** `2026-11-17-1a4ae2f0`

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0008-S0001 | Record valid-time precision and zone | Done |
| F0008-S0002 | Distinguish open, bounded and unknown ends | Done |
| F0008-S0003 | Split intervals and close recorded time | Done |
| F0008-S0004 | Enforce temporal integrity under concurrency | Done |
| F0008-S0005 | Guard succession by start basis and state | Done |
| F0008-S0006 | Resolve facts at a valid and recorded coordinate | Done |
| F0008-S0007 | Preserve pilot versions through migration | Done |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0008-S0001 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0008-S0002 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0008-S0003 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0008-S0004 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0008-S0005 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0008-S0006 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |
| F0008-S0007 | done | not-in-scope | not-in-scope | done | PASS | PASS | done | done |

Frontend and AI are out of scope because F0008 has no UI and makes no model call. The Architect set the required roles at Phase B (below).

## Required Role Matrix

Set by the Architect at Phase B (G5), 2026-11-16.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | 46 ACs need PostgreSQL concurrency-grid, zone/DST, immutability-negative and migration evidence | Architect | 2026-11-16 |
| Code Reviewer | Yes | v1 commit path rewrite, new domain types, migration 0014 with triggers | Architect | 2026-11-16 |
| Security Reviewer | Yes | Attestation-date disclosure (T-08), close-only triggers under application roles, non-disclosing refusals, revoked-grant historical reads | Architect | 2026-11-16 |
| DevOps | Yes | Migration 0014 up/down/up on seeded pilot and F0007 data; revision coordination with F0011 | Architect | 2026-11-16 |
| Architect | Yes | ADR-0078 proof gates and KG reconciliation at feature G7 | Architect | 2026-11-16 |

## Story Signoff Provenance

Append-only history. Rows for `2026-11-17-1a4ae2f0` are the prior completion provenance, superseded by review `2026-11-18-d34a095e`. Rows for `2026-11-18-bce4909b` belong to the current remediation run.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0008-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0001 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0001 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0002 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0002 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0003 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0003 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0004 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0004 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0005 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0005 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0005 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0005 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0005 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0006 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0006 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0006 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0006 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0006 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0007 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/test-execution-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0007 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/code-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0007 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/security-review-report.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval; SEC-F8-02 (Low) deferred to F0018, accepted by the operator at G4 |
| F0008-S0007 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/deployability-check.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0007 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md` | 2026-11-18 | PM verified role evidence after the G4 operator approval |
| F0008-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0001 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0001 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0002 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0002 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0003 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0003 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0004 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0004 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0005 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0005 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0005 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0005 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0005 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0006 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0006 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0006 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0006 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0006 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0007 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0007 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0007 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0007 | DevOps | Claude (Opus 5.5) / DevOps | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0007 | Architect | Claude (Opus 5.5) / Architect | PENDING | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/g0-assembly-plan-validation.md` | 2026-11-18 | Remediation run opened after review 2026-11-18-d34a095e (NOT DONE); prior PASS row superseded pending fresh verdict |
| F0008-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0001 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0001 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0002 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0002 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0003 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0003 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0004 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0004 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0005 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0005 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0005 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0005 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0005 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0006 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0006 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0006 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0006 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0006 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0007 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/test-execution-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0007 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/code-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0007 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS WITH RECOMMENDATIONS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/security-review-report.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19; carried SEC-F8-02 (Low) deferred to F0018 |
| F0008-S0007 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/deployability-check.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |
| F0008-S0007 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/architect-implementation-review.md` | 2026-11-19 | Current role verdict after remediation; operator G4 approval 2026-11-19 |

## Clarifications (G1, 2026-11-16)

1. **Start basis:** each version stores how its start was obtained. A template field or a human-entered date counts as grade `A`. Grade `C` cannot close or split a predecessor (`SUCCESSION_START_UNANCHORED`). Routing the refusal to review belongs to F0018.
2. **State supersession:** a `PRESENT` value can be closed only by `PRESENT` or `EXPLICIT_NEGATIVE`. Any other state against `PRESENT` is refused (`STATE_SUPERSESSION_REFUSED`). Removing a value is an F0010 correction or retraction.
3. **Unknown start:** with no dated evidence the commit is refused (`START_UNATTESTED`). A start is never widened to minus infinity.
4. **Time zone:** the caller supplies the IANA zone of each bound. F0008 validates truncation in that zone and stores it.

## Closeout Summary (PM, 2026-11-18)

- **Run:** feature run `2026-11-17-1a4ae2f0` (G0–G8). The operator approved at G4 on 2026-11-18 and allowed the ZAP DAST scan.
- **Delivered:** migration 0014 (additive) and the `fact-temporal/v1` contract for identity-v1 slots:
  - per-bound granularity and zone;
  - OPEN/BOUNDED/UNKNOWN ends with attestation from F0004 date selections;
  - start-basis and information-state guards, where an end revision is not a succession;
  - remainder lineage;
  - close-only immutability, DELETE/TRUNCATE refusal and append-only changes, all enforced by the database;
  - the envelope backstop;
  - the two-coordinate reader with validity-unknown.

  The legacy pilot path keeps its shape, and its remainders now keep the predecessor's timestamps and review linkage.
- **Tests:** 46/46 ACs; the final full engine run is 1081 passed, 0 failed, 0 skipped; 213 F0008 cases; changed-line coverage 98.0%. All six ADR-0078 proof gates are evidenced on PostgreSQL 18.
- **Defects found and fixed in the run:**
  - an end revision leaving a remainder;
  - commit-side date disclosure;
  - the migration envelope helper;
  - CR-L1 (malformed instant code);
  - SEC-F8-01 (database text in the 409).
- **Residual and deferred:**
  - SEC-F8-02 (Low): application connection as a superuser → F0018 application role. Operator-accepted at G4.
  - Refusal reason-code persistence → F0018 (ADR-0078 D8 note).
  - CR-I1: the `brain-api.yaml` `FactVersion` `valid`/`recorded` drift predates F0008.
  - CR-I2: the ADR-0078 D4 wording on clears.
  - CR-I3: pin tzdata (PostgreSQL 2025b vs Python 2026e).
- **ADRs:** all ADR-0078 proof gates are met, but acceptance is an operator decision and the ADR stays Proposed. ADR-0064 and ADR-0039 stay Proposed.
- **Not delivered by F0008** (owned elsewhere): F0009 lineage use, F0010 change-reason vocabulary, F0016 mention grades, F0018 review routing, RLS and refusal reasons, F0019/F0025 endorsements, F0020 HTTP states, F0022 date selection producer, F0012/F0013 `temporal_kind` activation.
- **Evidence:** `planning-mds/operations/evidence/runs/2026-11-17-1a4ae2f0/pm-closeout.md`.

## Remediation Closeout Summary (PM, 2026-11-19)

- **Run:** `2026-11-18-bce4909b` (G0–G8). The operator decided the remediation scope on 2026-11-18 and approved at G4 on 2026-11-19. It supersedes `2026-11-17-1a4ae2f0`.
- **Resolved:**
  - CR-F8-01: the commit response returns `versions[].temporal` (S0002 AC7); S0007 AC6 amended.
  - FR-ARCH-M1: a legacy read omits `temporal`.
  - QE-M1: S0004 AC1 amended, keeping the F0002 failed-decision audit.
  - FR-ARCH-L2: migration 0015 adds the same-slot lineage guard.
  - FR-ARCH-L1: ADR prose.
  - PM-M1: F0018 handoffs recorded.
  - PM-L1, PM-L2, SEC-L1, QE-L1: corrected through `prior-run-errata.md`.
- **Tests:** full engine run 1085/0/0; changed-line coverage 100%; all 46 ACs (as amended) evidenced.
- **Framework:** the G6/G7 reentry defect was fixed upstream (nebula-agents PR #101) rather than waived.
- **Residual:**
  - SEC-F8-02 → F0018 (operator-accepted).
  - ADR-0078 acceptance (operator decision).
  - F0011 renumbers its migration after 0015.
- **Evidence:** `planning-mds/operations/evidence/runs/2026-11-18-bce4909b/pm-closeout.md`.

