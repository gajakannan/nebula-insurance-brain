# F0007 — FactSlot model — Status

**Overall Status:** In Progress — remediation run `2026-11-09-81798e61`; prior completion retained as history.
**Last Updated:** 2026-11-09
**Plan Run:** `2026-11-09-60865e32` (A+B, new)
**Phase A:** Approved 2026-11-09 (`approve-phase-a`, G3 PASS)
**Phase B:** Approved 2026-11-09 (`approve-phase-b`; assembly plan, ADR-0077, three design schemas)
**Implementation:** Current remediation `2026-11-09-81798e61`; original run `2026-11-09-b94cfa12` closed 2026-11-09 and is retained as history.

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0007-S0001 | Resolve stable FactSlot identity | In Progress |
| F0007-S0002 | Distinguish single, multi-valued and relationship slots | In Progress |
| F0007-S0003 | Carry information state separately from value | In Progress |
| F0007-S0004 | Type money and identifiers | In Progress |
| F0007-S0005 | Define name FactSlots | In Progress |
| F0007-S0006 | Preserve pilot slots and ownership | In Progress |

## Story × Role Progress

Current remediation run only. Prior passing verdicts below are history, not current signoff.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0007-S0001 | done | not-in-scope | not-in-scope | validating | pending | pending | validating | in-progress |
| F0007-S0002 | done | not-in-scope | not-in-scope | validating | pending | pending | validating | in-progress |
| F0007-S0003 | done | not-in-scope | not-in-scope | validating | pending | pending | validating | in-progress |
| F0007-S0004 | done | not-in-scope | not-in-scope | validating | pending | pending | validating | in-progress |
| F0007-S0005 | done | not-in-scope | not-in-scope | validating | pending | pending | validating | in-progress |
| F0007-S0006 | done | not-in-scope | not-in-scope | validating | pending | pending | validating | in-progress |

Frontend and AI are out of scope: F0007 has no UI and no model call. The Architect set the required roles at Phase B (below).

## Required Role Matrix

Set by the Architect at Phase B (G5), 2026-11-09.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | 39 ACs need independent PostgreSQL, concurrency and negative-fixture evidence | Architect | 2026-11-09 |
| Code Reviewer | Yes | New application package, migration and commit-path change | Architect | 2026-11-09 |
| Security Reviewer | Yes | Ownership keys, derived restrictions, non-disclosing denial (T-08) and RLS handoff | Architect | 2026-11-09 |
| DevOps | Yes | Additive migration 0012 with up/down/up proof on seeded pilot data | Architect | 2026-11-09 |
| Architect | Yes | Identity, legacy compatibility and ADR-0077 proof gates | Architect | 2026-11-09 |

## Story Signoff Provenance

Append-only history. Rows for `2026-11-09-b94cfa12` are prior completion provenance, not signoff for the current remediation run. New verdicts are appended after fresh review.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0007-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/test-execution-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/code-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0001 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/security-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/deployability-check.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0001 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/architect-implementation-review.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/test-execution-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/code-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0002 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/security-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/deployability-check.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0002 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/architect-implementation-review.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/test-execution-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/code-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0003 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/security-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/deployability-check.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0003 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/architect-implementation-review.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/test-execution-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/code-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0004 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/security-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/deployability-check.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0004 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/architect-implementation-review.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0005 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/test-execution-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0005 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/code-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0005 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/security-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0005 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/deployability-check.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0005 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/architect-implementation-review.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0006 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/test-execution-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0006 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/code-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0006 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/security-review-report.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0006 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/deployability-check.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |
| F0007-S0006 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-09-b94cfa12/architect-implementation-review.md` | 2026-11-09 | PM verified role evidence after the G4 operator approval |

## Prior Closeout Summary (PM, 2026-11-09; historical)

- **Delivered:** all six stories and all 39 ACs, with PostgreSQL evidence in run `2026-11-09-b94cfa12`:
  - KB-owned slot identity with authoritative qualifier rows;
  - SINGLE, MULTI and RELATIONSHIP slots, with members as child slots;
  - the `fact-answer/v1` carrier;
  - exact money and scheme-scoped identifiers;
  - the four system name predicates and the precedence-free hook;
  - additive migration 0012 with ownership keys and triggers;
  - the RLS inventory handed to F0018.
- **Tests:**
  - 819/819 engine tests on an owned database at head;
  - 151/151 in the F0007 CI step (`brain_factslots` 98.6%);
  - neuron 264 passed, 41 CI-equivalent skips;
  - changed-line coverage 99.0%.
- **Defects found and fixed:**
  - a naive `created_at` binding;
  - the backup inventory reading columns that later migrations add (it already failed on `main` because of 0011);
  - an F0006 test that hard-coded head `0011`;
  - at G3: SEC-F7-01 (name evidence READ before any reason), SEC-F7-02 (T-08 on the read path) and SEC-F7-03 (cross-KB evidence oracle).
- **Residual risks:**
  - The answer envelope is service-enforced; F0008 owns the database backstop.
  - Slot restrictions are fixed at creation; F0018 owns re-derivation.
  - The name hook authorizes per slot; a design note for F0017/F0023.
  - ADR-0077 is still Proposed, with all five proof gates evidenced. Formal acceptance is the operator's call.
- **Deferrals:** none. Every story is Done; the handoffs are owned by F0008, F0011, F0012/F0013, F0016, F0017/F0023, F0018, F0020 and F0026.

## Clarifications (G1, 2026-11-09)

1. **Row security:** F0007 binds new rows to tenant/KB ownership with composite keys and immutability triggers. F0018 Phase B designs and enables RLS on all tenant-owned tables, F0007's included.
2. **Predicate identity:** an opaque, versioned predicate key with a minimal F0007 system-predicate set (the four name predicates plus test fixtures). F0012/F0013 register real predicates.
3. **Display name:** F0007 provides the hook only. The order of preference is an open decision owned by F0017/F0023.
