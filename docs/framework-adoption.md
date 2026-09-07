# Framework adoption

Product instructions and review checks are declared in the repository-root `.nebula-project.yaml`.

- [Agent instructions](agent-instructions.md) describe local working conventions.
- [Plan review checklist](plan-review-checklist.md) names the Brain-specific review criteria and their governing sources.
- [Adoption plan](../planning-mds/framework-adoption-plan.md) records the design and rollout work.
- `scripts/validation/validate_plan_readiness.py` checks planning structure and returns a failing exit code for failed checks. It does not certify architectural adequacy or regulatory compliance.

The framework's `BOUNDARY-POLICY.md` governs the separation of reusable framework content and product content. Insurance requirements and authorization policy remain in this product's blueprint, architecture, and security artifacts.

Instruction discovery requires an explicitly selected product root. Required local checks run at the framework's declared `plan-review` PR2 extension point, before readiness is recorded. Native host hook configuration is optional; it is not the source of product policy.

## Rollout status

The implementation is prepared on local publication branches. The currently pinned framework commit (`4eaf7b3abef84687f6fda622c61a95d378a50888`) does not contain the new commands. Local validation works independently; integrated commands require the updated sibling framework checkout.

CI is wired to run local fixtures and the declared project checks. Its explicit compatibility gate will fail at the old pin rather than silently skip required checks. Before merging this rollout, publish the generic framework change, then update the framework ref in `.github/workflows/ci-gates.yml` and the commit in `planning-mds/BLUEPRINT.md` together. No replacement SHA or release approval is asserted here.

Native host adapters have not been tested. Use the shared CLI with explicit root arguments; the current native cockpit does not propagate a separate product selection. Structural check results do not replace a PR0–PR4 review or amend the approved F0001 runtime scope.

Git itself reports the local changes. For a source-control UI, select this repository as the project root, or open `nebula.code-workspace` in an editor that supports VS Code multi-root workspaces. The parent `nebula/` is not a Git repository. This clone's `.githooks` and `merge.ours` driver are configured; each new clone needs the setup commands in CONTRIBUTING.

### Publication attempt — 2026-09-07

All framework changes, including the pre-existing renderer/settings/review changes requested by the operator, were committed locally as `9a68f7a9c6ba9a0b13d2b5814e06b7fed055e836` on `codex/project-extensions-20260907`. The complete tree is `5756af1326c2c7986983df159d728bf85f4d2a73`.

Direct Git fetch/push transport cannot resolve GitHub in the current session. The connected GitHub API accepted an equivalent tree/commit object (`3a6f7f21b513f834ef4b7c1418d51cb8f849956a`), but branch creation was denied because tool approval is unavailable. No publication branch or PR was created remotely, and neither main branch was changed. The unreferenced API object is not a release pin.

The Brain candidate is prepared on `codex/brain-project-adoption-20260907`. Resume publication from an environment with working Git transport or permitted branch writes: push the framework branch, complete its normal squash-merge workflow, update both Brain pins to that final main SHA, then publish and squash-merge Brain. Finally switch each local checkout to main and fast-forward it from origin/main. Preserve the local publication branches until their contents are verified on remote main; do not merge their pre-squash histories back into main.
