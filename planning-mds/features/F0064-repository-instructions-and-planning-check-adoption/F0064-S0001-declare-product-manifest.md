# Declare the product manifest

**Story ID:** F0064-S0001
**Feature:** F0064 — Repository instructions and planning-check adoption
**Title:** Declare the product manifest
**Priority:** Medium
**Phase:** Infrastructure
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** one version-1 `.nebula-project.yaml` at the repository root that declares the Brain's instructions and its required plan-review check
**So that** the shared framework resolves Brain guidance and runs the Brain check without any Brain-specific code in `nebula-agents`.

## Context & Background

Delivered 2026-09-07 (Brain PR #1). The placeholders were renamed from `{PRODUCT_ROOT}` to `{NEBULA_PRODUCT_ROOT}` with the pin advance in Brain PR #26. This story re-verifies the declaration at framework pin `d90bbb6`. The resolver and executor behavior itself belongs to framework F0009 (out of scope).

## Acceptance Criteria

- [ ] **AC1:** `.nebula-project.yaml` declares `version: 1`, the instructions `docs/agent-instructions.md` (all actions) and `docs/plan-review-checklist.md` (`plan-review` only), and exactly one check, `plan-readiness`, at action `plan-review`, stage `PR2`, event `before_stage_complete`, with `cwd: product` and `timeout_seconds: 60`.
- [ ] **AC2:** The check `argv` uses only the placeholders `{NEBULA_PRODUCT_ROOT}`, `{PLAN_SCOPE}` and `{TARGET}`, and it invokes `scripts/validation/validate_plan_readiness.py` with `--product-root`, `--plan-scope` and `--target`. No shell string is evaluated.
- [ ] **AC3:** From the framework root at `d90bbb6`, `python3 agents/scripts/project_context.py --product-root <brain> --action plan-review --json` exits 0 and lists, in order, `planning-mds/BLUEPRINT.md`, `docs/agent-instructions.md` and `docs/plan-review-checklist.md`, each with a SHA-256. With `--action plan`, the checklist is absent and the other two remain.
- [ ] **AC4:** `project_checks.py --list` for `plan-review` at project scope resolves the single `plan-readiness` check without an unresolved-placeholder error.
- [ ] **AC5:** Every declared `inputs` pattern matches at least one tracked file. Every file the validator reads (blueprint, instructions, checklist, governing sources, registry and feature planning files) falls under a declared pattern, so an edit to any of them invalidates a prior check result.

**Edge cases:**

- Removing a declared instruction file makes context resolution fail visibly rather than silently omitting it. Verified at the pinned revision; a silent omission is a defect that blocks closeout.

## Interaction Contract

N/A — read-only story. The manifest is authored configuration; no user-facing capture or save flow exists.

## Data Requirements

Manifest fields as listed in the PRD Data Requirements. No persisted product data.

## Role-Based Visibility

Not applicable: repository configuration readable by anyone with repository access. No server-side authorization or product permissions apply.

## Non-Functional Expectations

Resolution output is deterministic for unchanged inputs (identical manifest hash and instruction hashes across two runs).

## Dependencies

- Framework project-extension support at pin `d90bbb6` (framework F0009).

## Out of Scope

Framework resolver internals, additional extension points, native host adapters.

## Questions & Assumptions

**Assumptions (to be validated):**
- Verification uses temporary copies of the repository for the negative edge case. The working tree is never modified to stage a failure.

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (N/A — local configuration, no server-side authorization)
- [ ] Audit/timeline logged (N/A — no runtime events)
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] Story filename matches `Story ID` prefix (`F{NNNN}-S{NNNN}-...`)
- [ ] Story index regenerated if story file was added/renamed/moved

## Review Provenance

Recorded in the parent feature `STATUS.md` (`Required Signoff Roles (Set in Planning)` and `Story Signoff Provenance`).
