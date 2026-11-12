# F0064 — Repository instructions and planning-check adoption — Status

**Overall Status:** Draft — retroactive planning (tooling delivered 2026-09-07)
**Last Updated:** 2026-11-10
**Plan Run:** `2026-11-10-819c4124` (A+B, existing)
**Phase A:** Approved 2026-11-10 (`approve-phase-a`, G3 PASS)
**Phase B:** Drafted — [assembly plan](feature-assembly-plan.md), three capability nodes and bindings; pending operator review (G5)
**Implementation:** Delivered 2026-09-07 (Brain PR #1, `nebula-agents` PR #91 at `c218bf1`). Re-verification at pin `d90bbb6` happens in the feature run.

## G1 Decisions (2026-11-10)

1. Scope is Brain-side deliverables only. The framework mechanism (framework F0009) is a pinned dependency and is not re-proven here.
2. Native host adapters and the native cockpit are an explicit non-goal. The shared CLI with an explicit product root is the supported path.
3. Every defect found during re-verification is fixed before closeout, including any that needs a framework change and pin advance.

## Story Checklist

| Story | Title | Status |
|-------|-------|--------|
| F0064-S0001 | Declare the product manifest | Not Started |
| F0064-S0002 | Provide agent instructions and the review checklist | Not Started |
| F0064-S0003 | Validate plan-readiness structure | Not Started |
| F0064-S0004 | Enforce checks in CI and document setup | Not Started |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|-------|---------|----------|----|----|-------------|----------|--------|---------|
| F0064-S0001 | — | — | — | ⬜ | ⬜ | — | ⬜ | ⬜ Not Started |
| F0064-S0002 | — | — | — | ⬜ | ⬜ | — | ⬜ | ⬜ Not Started |
| F0064-S0003 | — | — | — | ⬜ | ⬜ | — | ⬜ | ⬜ Not Started |
| F0064-S0004 | — | — | — | ⬜ | ⬜ | — | ⬜ | ⬜ Not Started |

Backend, Frontend and AI are not in scope: no runtime code, UI or model call. The Architect confirms the role matrix at Phase B.

## Required Signoff Roles (Set in Planning)

Set by the Architect at Phase B (G5), 2026-11-10.

| Role | Required | Why Required | Set By | Date |
|------|----------|--------------|--------|------|
| Quality Engineer | Yes | Verification evidence for all 23 ACs (assembly Steps 1–4) | Architect | 2026-11-10 |
| Code Reviewer | Yes | Independent review of documentation repairs and any defect fix | Architect | 2026-11-10 |
| DevOps | Yes | S0004 covers the CI workflow and the framework pin contract | Architect | 2026-11-10 |
| Security Reviewer | No | No authn/authz, data-boundary or secret-handling change; checks run repository code under the existing build-script trust model and the manifest forbids shell evaluation | Architect | 2026-11-10 |
| Architect | No | No architecture-risk exception; no ADR created or changed | Architect | 2026-11-10 |

## Story Signoff Provenance

Recorded during the feature run.

## Deferred Non-Blocking Follow-ups

None. Under G1 decision 3, no defect found by re-verification may be deferred.

## Tracker Sync Checklist

- [ ] `planning-mds/features/REGISTRY.md` status/path aligned
- [ ] `planning-mds/features/ROADMAP.md` section aligned (`Now/Next/Later/Completed`)
- [ ] `planning-mds/features/STORY-INDEX.md` regenerated
- [ ] `planning-mds/BLUEPRINT.md` feature/story status links aligned
- [ ] Every required signoff role has story-level `PASS` entries with reviewer, date, and evidence

## Archival Criteria

All items above must be checked before moving this feature folder to `planning-mds/features/archive/`.
