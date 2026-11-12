# Enforce checks in CI and document setup

**Story ID:** F0064-S0004
**Feature:** F0064 — Repository instructions and planning-check adoption
**Title:** Enforce checks in CI and document setup
**Priority:** Medium
**Phase:** Infrastructure
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** CI to run the declared Brain check through the same shared executor the gate uses, and to fail closed at a framework revision without project-extension support
**So that** a broken plan cannot merge, and a fresh clone has documented setup that matches the CI pin.

## Context & Background

Delivered 2026-09-07 in the `framework-validators` job of `.github/workflows/ci-gates.yml`. The pin has since advanced to `d90bbb6` (2026-11-05) in CI and BLUEPRINT section 0 together. `docs/framework-adoption.md` and `planning-mds/framework-adoption-plan.md` still describe rollout and local hygiene as pending (plan-review `2026-10-30-ff4c758d` L1).

## Acceptance Criteria

- [ ] **AC1:** The `framework-validators` job checks out the framework at the pinned `ref:`. It fails with an explicit error when `agents/scripts/project_checks.py` is absent, runs `project_context.py --action plan-review --json`, and runs `project_checks.py --action plan-review --plan-scope project --target project` with a generated run ID. It uploads that run's evidence folder even when the check fails.
- [ ] **AC2:** The CI `ref:` and the framework pin in BLUEPRINT section 0 name the same full commit SHA.
- [ ] **AC3:** In a temporary copy of the repository with one checklist rule removed, the shared executor at project scope exits non-zero and records a failing `plan-readiness` result whose findings include `BRAIN-CHECKLIST`. The real working tree is not modified.
- [ ] **AC4:** CI on the F0064 closeout PR passes every job, including the project-extension steps.
- [ ] **AC5:** `CONTRIBUTING.md` documents per-clone setup (hooks path, explicit product root, local validation commands), and every script path it names exists. `nebula.code-workspace` lists the Brain and `nebula-agents` folders with paths that resolve from the workspace file.
- [ ] **AC6:** `docs/framework-adoption.md` and `planning-mds/framework-adoption-plan.md` state the current status (rollout complete, current pin, F0064 closeout). They retain the 2026-09-07 publication record as dated history and make no claim that hygiene or rollout steps remain pending.

**Edge cases:**

- A pin mismatch between CI and BLUEPRINT found at closeout is a defect, repaired before closeout (G1 decision 3).

## Interaction Contract

N/A — read-only story for CI behavior. Documentation edits under AC6 are authored changes reviewed in the PR; no user-facing save flow exists.

## Data Requirements

CI evidence artifact: the project-check run folder under `planning-mds/operations/evidence/runs/{run_id}/`.

## Role-Based Visibility

CI runs with the repository workflow token. No product permissions are involved.

## Non-Functional Expectations

The project-extension steps fit within the existing CI job; the check honours the manifest's 60-second timeout.

## Dependencies

- F0064-S0001 and F0064-S0003.

## Out of Scope

An automated CI guard for pin agreement (G3 assumption in the PRD), native host adapters, and other workflows' jobs.

## Questions & Assumptions

**Assumptions (to be validated):**
- Pin agreement remains a documented manual rule verified at closeout (PRD Risks & Assumptions).

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (N/A — CI tooling)
- [ ] Audit/timeline logged (N/A — CI artifacts serve as the record)
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] Story filename matches `Story ID` prefix (`F{NNNN}-S{NNNN}-...`)
- [ ] Story index regenerated if story file was added/renamed/moved

## Review Provenance

Recorded in the parent feature `STATUS.md` (`Required Signoff Roles (Set in Planning)` and `Story Signoff Provenance`).
