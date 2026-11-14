# F0064 — Repository instructions and planning-check adoption

**Status:** Done / Archived — feature run `2026-11-14-3325803a`, operator approved 2026-11-14
**Archived:** 2026-11-14
**Phase:** Repository Tooling
**Roadmap:** Completed

This user-requested repository tooling work is separate from the master blueprint's F0001–F0063 runtime epics. It adds local agent instructions, a review checklist, a structural validator, and a manifest consuming the generic framework extension. It does not change the approved F0001 scope.

Design and progress: [adoption plan](../../../framework-adoption-plan.md). Rollout record: [framework adoption](../../../../docs/framework-adoption.md).

Rollout is complete: the framework extension was published as `nebula-agents` PR #91 (`c218bf1`, 2026-09-07) and adopted by Brain PR #1. The pin in CI and BLUEPRINT section 0 has since advanced, and the project checks run at the `plan-review` extension point.

Lifecycle fidelity is restored (plan-review `2026-10-30-ff4c758d` L1). The feature has a PRD and stories describing only the delivered scope, KG bindings for the manifest and its checks, a re-verification run (`2026-11-14-3325803a`, all 23 ACs pass at pin `d90bbb6`), and PM closeout with archive transition. Local validation is not an architecture or regulatory approval.

## Documents

- [PRD](PRD.md) · [STATUS](STATUS.md) · [GETTING-STARTED](GETTING-STARTED.md)

## Stories

| ID | Title | Status |
|----|-------|--------|
| [F0064-S0001](F0064-S0001-declare-product-manifest.md) | Declare the product manifest | Done |
| [F0064-S0002](F0064-S0002-provide-agent-instructions-and-review-checklist.md) | Provide agent instructions and the review checklist | Done |
| [F0064-S0003](F0064-S0003-validate-plan-readiness-structure.md) | Validate plan-readiness structure | Done |
| [F0064-S0004](F0064-S0004-enforce-checks-in-ci-and-document-setup.md) | Enforce checks in CI and document setup | Done |

**Total Stories:** 4
