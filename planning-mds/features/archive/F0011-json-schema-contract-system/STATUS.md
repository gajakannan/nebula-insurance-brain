# F0011 — JSON Schema contract system — Status

**Overall Status:** Done
**Last Updated:** 2026-11-23 (closeout)
**Planning:** Phase A and Phase B approved by the operator; token `approve-phase-b` recorded at G5 on 2026-11-20.
**Plan Run:** `2026-11-20-ccb1bd39` (approved A+B baseline).
**Plan Revision:** `2026-11-21-e4098d22` (B, existing; operator approved with `approve-phase-b` on 2026-11-22).
**Plan Review:** `2026-11-21-b4cd07e4` returned READY for the baseline; this revision addresses its six findings.

## Story Checklist

| Story | Title | Status |
|-------|-------|--------|
| F0011-S0001 | Resolve versioned offline contracts | Done |
| F0011-S0002 | Validate information state and scoped absence | Done |
| F0011-S0003 | Validate qualified money and scoped identifiers | Done |
| F0011-S0004 | Prove cross-language contract conformance | Done |
| F0011-S0005 | Preserve existing consumer contracts | Done |
| F0011-S0006 | Verify reproducible contract delivery | Done |

Implemented and closed in feature run `2026-11-22-885e8734` (G0–G8). All 41 ACs have observed
evidence in the run's `artifacts/test-results/ac-evidence.md`. Operator approval at G4 came
on 2026-11-23, after the three G3 Lows were fixed.

## Story x Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|-------|---------|----------|----|----|-------------|----------|--------|---------|
| F0011-S0001 | done | not-in-scope | not-in-scope | done | APPROVED | PASS | done | done |
| F0011-S0002 | done | not-in-scope | not-in-scope | done | APPROVED | PASS | done | done |
| F0011-S0003 | done | not-in-scope | not-in-scope | done | APPROVED | PASS | done | done |
| F0011-S0004 | done | done | not-in-scope | done | APPROVED | PASS | done | done |
| F0011-S0005 | done | not-in-scope | not-in-scope | done | APPROVED | PASS | done | done |
| F0011-S0006 | done | done | not-in-scope | done | APPROVED | PASS | done | done |

Frontend work is headless JS tooling only. No UI/theme/visual/accessibility surface
is introduced. AI Engineer consultation covers existing Neuron caller regression;
no model/prompt/runtime AI change is authorized. Architect signoff is also required
for every story as recorded below.

## Backend Progress

- [x] Contract inventory and versioned bundle/adapters implemented.
- [x] Information-state/money/identifier cases executed at real consumers.
- [x] Historical and current reader behavior verified.

## Frontend Progress

- [x] Headless AJV conformance consumer implemented; no screen changes.

## Cross-Cutting

- [x] Reproducible artifact generation/checking and installed-package proof.
- [x] All AC evidence and at least 80% changed executable-line coverage (Python 86.4%, JS 98.5%).
- [x] Existing access, audit and transaction behavior verified.

## Required Role Matrix

Reconfirmed by Codex / Architect at feature G0, run `2026-11-22-885e8734`, 2026-11-22. All five roles are required
for every story because shared schema publication can affect deployed packages,
authorization order, precision and current/historical consumer behavior.

| Role | Required | Why Required | Set By | Date |
|------|----------|--------------|--------|------|
| Quality Engineer | Yes | Every AC, language conformance, integration and changed-line coverage | Architect | 2026-11-20 |
| Code Reviewer | Yes | Independent correctness, generation and compatibility review | Architect | 2026-11-20 |
| Security Reviewer | Yes | Offline refs/parser trust, errors, source READ order and same-UoW refusals | Architect | 2026-11-20 |
| DevOps | Yes | Locked build, installed resources, CI, coherent deployment and rollback | Architect | 2026-11-20 |
| Architect | Yes | Shared-source ownership, model/API consistency and ADR proof conditions | Architect | 2026-11-20 |

## Story Signoff Provenance

Append-only table.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|-------|------|----------|---------|----------|------|-------|
| F0011-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/test-execution-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/code-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0001 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/security-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/deployability-check.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0001 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/architect-implementation-review.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/test-execution-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/code-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0002 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/security-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/deployability-check.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0002 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/architect-implementation-review.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/test-execution-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/code-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0003 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/security-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/deployability-check.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0003 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/architect-implementation-review.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/test-execution-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/code-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0004 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/security-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/deployability-check.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0004 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/architect-implementation-review.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0005 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/test-execution-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0005 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/code-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0005 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/security-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0005 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/deployability-check.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0005 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/architect-implementation-review.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0006 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/test-execution-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0006 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/code-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0006 | Security Reviewer | Claude (Opus 5.5) / Security Reviewer | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/security-review-report.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0006 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/deployability-check.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |
| F0011-S0006 | Architect | Claude (Opus 5.5) / Architect | PASS | `planning-mds/operations/evidence/runs/2026-11-22-885e8734/architect-implementation-review.md` | 2026-11-23 | PM verified role evidence after the G4 operator approval |

## Scope Boundaries and Later Owners

F0012/F0013 own vocabulary; F0015 owns extraction compilation; F0016 owns actual
searched scopes; F0014/F0023 own package completeness/display. ADR-0039 stays
Proposed pending all stated proofs. These are ownership boundaries, not waived
F0011 acceptance criteria. PR-L3 is a tracked Low audit follow-up: Security Reviewer must record the
internal-invariant decision and a fault-injection result at feature G3,
before the implementation approval gate. See the assembly plan,
"Read audit follow-up (PR-L3)". Disposition: Security accepted it at G3 in run
`2026-11-22-885e8734`; the fault-injection result is in the PostgreSQL consumer suite.

## Closeout Summary

Closed 2026-11-23 in feature run `2026-11-22-885e8734`. Every gate G0–G8 passed; the operator approved at
G4 after asking for all three G3 Lows to be fixed first. Delivered: one offline
21-resource JSON Schema 2020-12 bundle; source-gated generated Pydantic; a headless AJV consumer and
a shared OpenAPI snapshot; native-compat readers frozen with an explicit portable profile;
response guards on FactSlot read and commit. Evidence: 443 shared cases / 1329 results with
0 mismatches; unit 1239, PostgreSQL 83 and full Neuron suites green; changed-line coverage
86.4% Python / 98.5% JS; all four scan classes clean or triaged; five roles × six stories
signed. Low fixes at G4: 500-handler traceId logging, direct `facts.py` mismatch tests,
and Neuron SoupSieve 2.9.2 → 4.1.3. ADR-0079's acceptance proofs are met, but it stays
Proposed pending an explicit operator decision. ADR-0039 stays Proposed (F0023 display
condition). No deferred follow-ups, recommendations, waivers or omissions.

## Tracker Sync Checklist

- [x] Story index regenerated after Phase A story creation (60 total stories).
- [x] Registry, roadmap and blueprint references validated before G3 (zero errors/warnings).
- [x] Architect completed feature/story KG bindings and G4 ontology synchronization.
- [x] All seven ordered G5 pre-approval exit operations returned zero.
- [x] Operator explicitly approved Phase A at G3.
- [x] Operator explicitly approved Phase B after green G5 exit checks (`approve-phase-b`, 2026-11-20).

- [x] Operator approved review revision `2026-11-21-e4098d22` at G5 (`approve-phase-b`, 2026-11-22); final publication is recorded by the run journal/manifest.
