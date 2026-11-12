# Validate plan-readiness structure

**Story ID:** F0064-S0003
**Feature:** F0064 — Repository instructions and planning-check adoption
**Title:** Validate plan-readiness structure
**Priority:** Medium
**Phase:** Infrastructure
**Status:** Not Started

## User Story

**As a** Dana the Platform Engineer
**I want** a deterministic structural validator for Brain planning packages with a fixed output and exit-code contract
**So that** an empty, incomplete or unresolvable plan fails plan-review PR2 and CI, while a plan that names future runtime files still passes.

## Context & Background

Delivered 2026-09-07 as `scripts/validation/validate_plan_readiness.py`, with fixtures and a compatibility entry point that replaced the earlier keyword draft. It checks structure only. Semantic adequacy remains reviewer judgment under S0002's checklist.

## Acceptance Criteria

- [ ] **AC1:** At project scope on the current repository, the validator prints JSON `{"schema_version": 1, "check_id": "plan-readiness", "status": "pass", "findings": []}` and exits 0. Each finding, when present, carries `rule_id`, `message` and a product-relative `path`.
- [ ] **AC2:** Exit codes: 0 on pass, 1 when any finding is present, and 2 with a `BRAIN-INVOCATION` finding for invalid invocation (project scope with a target other than `project`, a feature scope with several targets, duplicate or malformed feature IDs).
- [ ] **AC3:** The fixture suite `scripts/validation/tests/test_plan_readiness.py` passes. It covers a valid plan naming future runtime paths, each invalid-input mutation failing with its expected rule, feature-set and project scopes, a missing governing source, the required examples rule, non-mutation of plans, a deleted active PRD, and an unresolved story planning reference.
- [ ] **AC4:** Project scope selects every non-archived registry feature that is Active, In Progress or Done, or that has a `PRD.md`, and it excludes archived features.
- [ ] **AC5:** `scripts/kg/validate_plan_compliance.py <plan file>` maps a plan inside `planning-mds/features/F####-*/` to feature scope and returns the validator's exit code. A path outside the feature tree exits 2.
- [ ] **AC6:** At feature scope, `--target F0064` passes on this feature's own planning package.
- [ ] **AC7:** Repository files are byte-identical before and after any validator invocation. The validator writes no audit or timeline record; the gate's `commands.log` and run evidence are the audit trail.

**Edge cases:**

- A plan whose inline code names a not-yet-created runtime file passes. A markdown link into `planning-mds/` that does not resolve fails with `BRAIN-REFERENCE`.

## Interaction Contract

N/A — read-only story. The validator reads planning files and reports; it never writes.

## Data Requirements

Validator result fields as listed in the PRD Data Requirements.

## Role-Based Visibility

Not applicable: local CLI. No server-side authorization or product permissions apply.

## Non-Functional Expectations

Completes within the manifest's 60-second timeout at project scope.

## Dependencies

- F0064-S0002 (the checklist structure it validates).

## Out of Scope

Semantic or regulatory judgment, runtime proof, and checks for other actions or stages.

## Questions & Assumptions

**Assumptions (to be validated):**
- "Same result from any working directory" is proven through the `--product-root` argument. Executor-side working-directory handling belongs to framework F0009.

## Definition of Done

- [ ] Acceptance criteria met
- [ ] Edge cases handled
- [ ] Permissions enforced (N/A — local CLI)
- [ ] Audit/timeline logged (N/A — no runtime events)
- [ ] Tests pass
- [ ] Documentation updated (if needed)
- [ ] Story filename matches `Story ID` prefix (`F{NNNN}-S{NNNN}-...`)
- [ ] Story index regenerated if story file was added/renamed/moved

## Review Provenance

Recorded in the parent feature `STATUS.md` (`Required Signoff Roles (Set in Planning)` and `Story Signoff Provenance`).
