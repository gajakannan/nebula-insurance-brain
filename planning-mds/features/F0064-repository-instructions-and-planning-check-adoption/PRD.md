# F0064 — Repository instructions and planning-check adoption

**Feature ID:** F0064
**Feature Name:** Repository instructions and planning-check adoption
**Priority:** Medium
**Phase:** Infrastructure — Repository Tooling (outside the master blueprint section 95 runtime epics)
**Status:** Planned — tooling delivered 2026-09-07; Phase A and B approved (2026-11-10, 2026-11-14); re-verification and closeout in the feature run
**Plan Run:** `2026-11-10-819c4124` (A+B, existing)

## Feature Statement

**As a** platform engineer running framework actions against this repository
**I want** the Brain to declare its own agent instructions, plan-review criteria and required structural check, in files the shared framework discovers and executes
**So that** every planning session and plan-review loads Brain guidance, and a structurally incomplete plan fails the gate and CI without any change to `nebula-agents`.

## Business Objective

- Goal: record, re-verify and close out the Brain-side adoption of the framework project-extension contract, delivered on 2026-09-07 by Brain PR #1 against `nebula-agents` PR #91 (`c218bf1`).
- Baseline: the tooling runs at the current framework pin `d90bbb6` and in CI. It has no PRD, stories, KG bindings or feature evidence. Plan-review `2026-10-30-ff4c758d` finding L1 recorded that its tracker description is stale.
- Target: all story acceptance criteria are re-verified at the current pin with no open defect, the delivered files are bound in the knowledge graph, and the feature is archived as Completed.

## Problem Statement

The adoption shipped outside the feature lifecycle, so the repository cannot answer, from its own trackers and graph, what the tooling guarantees, which files implement it, or whether it still works. Retrieval for the manifest, instructions, checklist and validator resolves to no feature. The adoption documents still describe rollout and local hygiene as pending.

## Scope & Boundaries

**In Scope (Brain-side deliverables only — G1 decision 1):**

- `.nebula-project.yaml` (version 1): two instruction declarations and the required `plan-readiness` check at `plan-review` PR2.
- `docs/agent-instructions.md` and `docs/plan-review-checklist.md`.
- `scripts/validation/validate_plan_readiness.py`, its fixtures in `scripts/validation/tests/test_plan_readiness.py`, and the compatibility entry point `scripts/kg/validate_plan_compliance.py`.
- The project-extension steps of the `framework-validators` CI job in `.github/workflows/ci-gates.yml`, and the pin agreement between that job and BLUEPRINT section 0.
- Contributor and workspace guidance: `CONTRIBUTING.md`, `nebula.code-workspace`, `docs/framework-adoption.md`, `planning-mds/framework-adoption-plan.md`.
- Re-verification evidence at the current pin, and repair of every defect that re-verification finds before closeout (G1 decision 3).

**Out of Scope:**

- The generic framework mechanism: `project_context.py`, `project_checks.py`, run-gate integration, resume and input-hash invalidation, and PR4 enforcement. These are tracked as `nebula-agents` framework F0009 and consumed here at the pinned revision; this feature does not re-prove them.
- Native host adapters (Claude Code, Codex, Hermes) and the native cockpit. They are untested and are an explicit non-goal (G1 decision 2). The supported path is the shared CLI with an explicit `--product-root` or `NEBULA_PRODUCT_ROOT`.
- New extension points, new required checks, or semantic adequacy judgment. Architectural adequacy remains a reviewer decision under the checklist.
- Any runtime product behavior, insurance business rule, API, schema, permission or migration.

## Personas

- Dana the Platform Engineer — `../../examples/personas/platform-engineer.md`. Owns CI, pins and repository setup; runs framework actions with an explicit product root.

## Acceptance Criteria Overview

- [ ] The manifest validates and resolves the intended instructions and check at the pinned framework revision (S0001).
- [ ] The instructions and checklist name resolvable governing sources, and no Brain review text is copied into the framework (S0002).
- [ ] The validator honours its output and exit-code contract across feature, feature-set and project scopes, and its fixtures pass (S0003).
- [ ] CI fails closed without project-extension support, runs the declared check through the shared executor, and keeps the pin agreement; a deliberately broken plan fails the check (S0004).
- [ ] Contributor and adoption documents describe the current state (S0004).

## UX / Screens

No UI — repository tooling, CLI and CI only.

## Screen Layouts (ASCII)

No UI — repository tooling, CLI and CI only. No screen, zone or user-visible flow is introduced or changed.

## Data Requirements

- Manifest: `version`, `instructions[]` (`path`, optional `actions`), `checks[]` (`id`, `action`, `stage`, `event`, `argv`, `cwd`, `timeout_seconds`, `inputs`).
- Validator result: JSON `schema_version`, `check_id`, `status` (`pass`/`fail`), `findings[]` (`rule_id`, `message`, product-relative `path`). Exit 0 pass, 1 failed checks, 2 invalid invocation.
- No persisted product data.

## Role-Based Access

Not applicable: local CLI and CI tooling with no server-side authorization. Anyone with repository access runs the scripts; CI runs them with the workflow token.

## Success Criteria

- Every story acceptance criterion passes at framework pin `d90bbb6` with recorded evidence.
- CI on the closeout PR passes, including the project-extension steps.
- KG lookup for each delivered file resolves to F0064.

## Risks & Assumptions

- **Assumption (G3 review):** pin agreement between CI and BLUEPRINT section 0 stays a documented manual rule verified at closeout. No new automated guard is added; adding one would be new scope.
- **Risk:** re-verification may find framework-side defects. They are out of this feature's write scope and would block closeout under G1 decision 3 until fixed in `nebula-agents` and the pin advanced.
- **Risk:** project-scope readiness now includes F0064 itself once this PRD exists, so this package must pass the Brain validator.

## Dependencies

- `nebula-agents` project-extension support (framework F0009) at the pinned revision `d90bbb6`.
- No Brain runtime feature dependency. Tracker governance per [TRACKER-GOVERNANCE.md](../TRACKER-GOVERNANCE.md).

## Related Stories

- [F0064-S0001](F0064-S0001-declare-product-manifest.md) — Declare the product manifest
- [F0064-S0002](F0064-S0002-provide-agent-instructions-and-review-checklist.md) — Provide agent instructions and the review checklist
- [F0064-S0003](F0064-S0003-validate-plan-readiness-structure.md) — Validate plan-readiness structure
- [F0064-S0004](F0064-S0004-enforce-checks-in-ci-and-document-setup.md) — Enforce checks in CI and document setup

## Rollout & Enablement

Already enabled on `main` since 2026-09-07. Closeout changes no default behavior; it adds documentation, KG bindings and evidence, plus any defect repair re-verification requires.

## Source Traceability

- Design and delivery record: [framework adoption plan](../../framework-adoption-plan.md); rollout record: `docs/framework-adoption.md`.
- Finding: plan-review `2026-10-30-ff4c758d` L1. Roadmap decision: 2026-11-10 review (Now, retroactive closeout).
- G1 decisions: run `2026-11-10-819c4124` `gate-decisions.md`.
