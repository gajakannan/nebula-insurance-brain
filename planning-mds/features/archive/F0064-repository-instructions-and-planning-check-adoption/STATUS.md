# F0064 — Repository instructions and planning-check adoption — Status

**Overall Status:** Done / Archived 2026-11-14 — feature run `2026-11-14-3325803a` (operator G4 `approve`); all 23 ACs re-verified at pin `d90bbb6`. Tooling delivered 2026-09-07
**Last Updated:** 2026-11-14
**Plan Run:** `2026-11-10-819c4124` (A+B, existing)
**Phase A:** Approved 2026-11-10 (`approve-phase-a`, G3 PASS)
**Phase B:** Approved 2026-11-14 (`approve-phase-b`, G5; [assembly plan](feature-assembly-plan.md), three capability nodes and bindings)
**Implementation:** Delivered 2026-09-07 (Brain PR #1, `nebula-agents` PR #91 at `c218bf1`). Re-verified at pin `d90bbb6` in feature run `2026-11-14-3325803a` (PR #49).

## G1 Decisions (2026-11-10)

1. Scope is Brain-side deliverables only. The framework mechanism (framework F0009) is a pinned dependency and is not re-proven here.
2. Native host adapters and the native cockpit are an explicit non-goal. The shared CLI with an explicit product root is the supported path.
3. Every defect found during re-verification is fixed before closeout, including any that needs a framework change and pin advance.

## Story Checklist

| Story | Title | Status |
|-------|-------|--------|
| F0064-S0001 | Declare the product manifest | Done |
| F0064-S0002 | Provide agent instructions and the review checklist | Done |
| F0064-S0003 | Validate plan-readiness structure | Done |
| F0064-S0004 | Enforce checks in CI and document setup | Done |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|-------|---------|----------|----|----|-------------|----------|--------|---------|
| F0064-S0001 | not-in-scope | not-in-scope | not-in-scope | done | PASS | not-in-scope | done | done |
| F0064-S0002 | not-in-scope | not-in-scope | not-in-scope | done | PASS | not-in-scope | done | done |
| F0064-S0003 | not-in-scope | not-in-scope | not-in-scope | done | PASS | not-in-scope | done | done |
| F0064-S0004 | not-in-scope | not-in-scope | not-in-scope | done | PASS | not-in-scope | done | done |

Backend, Frontend and AI are not in scope: there is no runtime code, UI or model call. Security is not in scope (Security Reviewer not required, see below). Final state at closeout of feature run `2026-11-14-3325803a`.

## Required Role Matrix

Set by the Architect at Phase B (G5), 2026-11-10.

| Role | Required | Why Required | Set By | Date |
|------|----------|--------------|--------|------|
| Quality Engineer | Yes | Verification evidence for all 23 ACs (assembly Steps 1–4) | Architect | 2026-11-10 |
| Code Reviewer | Yes | Independent review of documentation repairs and any defect fix | Architect | 2026-11-10 |
| DevOps | Yes | S0004 covers the CI workflow and the framework pin contract | Architect | 2026-11-10 |
| Security Reviewer | No | No authn/authz, data-boundary or secret-handling change; checks run repository code under the existing build-script trust model and the manifest forbids shell evaluation | Architect | 2026-11-10 |
| Architect | No | No architecture-risk exception; no ADR created or changed | Architect | 2026-11-10 |

## Story Signoff Provenance

Append-only history. Feature run `2026-11-14-3325803a`.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|
| F0064-S0001 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/test-execution-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0001 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/code-review-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0001 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/deployability-check.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0002 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/test-execution-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0002 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/code-review-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0002 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/deployability-check.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0003 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/test-execution-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0003 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/code-review-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0003 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/deployability-check.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0004 | Quality Engineer | Claude (Opus 5.5) / Quality Engineer | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/test-execution-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0004 | Code Reviewer | Claude (Opus 5.5) / Code Reviewer | APPROVED | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/code-review-report.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |
| F0064-S0004 | DevOps | Claude (Opus 5.5) / DevOps | PASS | `planning-mds/operations/evidence/runs/2026-11-14-3325803a/deployability-check.md` | 2026-11-14 | PM verified role evidence after the G4 operator approval |

## Deferred Non-Blocking Follow-ups

None. Under G1 decision 3, no defect found by re-verification may be deferred.

## Tracker Sync Checklist

- [x] `planning-mds/features/REGISTRY.md` status/path aligned
- [x] `planning-mds/features/ROADMAP.md` section aligned (`Now/Next/Later/Completed`)
- [x] `planning-mds/features/STORY-INDEX.md` regenerated
- [x] `planning-mds/BLUEPRINT.md` feature/story status links aligned
- [x] Every required signoff role has story-level `PASS` entries with reviewer, date, and evidence

## Closeout Summary (PM, 2026-11-14)

- **Scope delivered:** the four stories, re-verified (23/23 ACs plus the S0001 edge case and the S0003 NFE) at framework pin `d90bbb6`, feature run `2026-11-14-3325803a`, PR #49.
- **Tests:** `scripts/validation/tests` 63 passed (11 plan-readiness fixtures); `scripts/kg/tests` 189 passed. Validator branch coverage 88%. CI on PR #49 passed 7/7 checks, including the project-extension steps.
- **Defects:** 0 in the delivered tooling. Three stale documentation statements were repaired (adoption status, adoption-plan header, CONTRIBUTING KG claim), plus code-review CR-1 (native-host wording). No framework change or pin advance was needed.
- **Reviews:** QE PASS, Code Reviewer APPROVED, DevOps PASS. Security Reviewer and Architect not required. Operator G4 `approve` on 2026-11-14.
- **Residual risk:** pin agreement between CI and BLUEPRINT section 0 remains a documented manual rule (PRD assumption). An automated guard is out of scope.
- **Deferrals:** none (G1 decision 3).

## Archival Criteria

All items above must be checked before moving this feature folder to `planning-mds/features/archive/`.
