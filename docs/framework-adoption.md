# Framework adoption

Product instructions and review checks are declared in the repository-root `.nebula-project.yaml`.

- [Agent instructions](agent-instructions.md) describe local working conventions.
- [Plan review checklist](plan-review-checklist.md) names the Brain-specific review criteria and their governing sources.
- [Adoption plan](../planning-mds/framework-adoption-plan.md) records the design and rollout work.
- `scripts/validation/validate_plan_readiness.py` checks planning structure and returns a failing exit code for failed checks. It does not certify architectural adequacy or regulatory compliance.

The framework's `BOUNDARY-POLICY.md` governs the separation of reusable framework content and product content. Insurance requirements and authorization policy remain in this product's blueprint, architecture, and security artifacts.

Instruction discovery requires an explicitly selected product root. Required local checks run at the framework's declared `plan-review` PR2 extension point, before readiness is recorded. Native host hook configuration is optional; it is not the source of product policy.

## Rollout status

Rollout is complete. The framework extension change was published as `nebula-agents` PR #91 and squash-merged to its `main` on 2026-09-07 as `c218bf1776f509a30f71967a1ee79879caa9a000`. That revision carries `agents/scripts/project_checks.py` and `agents/scripts/project_context.py`, so the checks declared in `.nebula-project.yaml` run through the shared executor rather than only as standalone scripts.

Both pins now name that commit: `ref:` in `.github/workflows/ci-gates.yml` and the framework binding in `planning-mds/BLUEPRINT.md` section 0. Advance the two together; CI keeps an explicit compatibility gate that fails closed at a revision without project-extension support rather than silently skipping required checks.

The Brain adoption candidate was published as PR #1 from `codex/brain-project-adoption-20260907` and merged on 2026-09-07. Local validation continues to work independently of the framework checkout.

Native host adapters have not been tested. Use the shared CLI with explicit root arguments; the current native cockpit does not propagate a separate product selection. Structural check results do not replace a PR0–PR4 review or amend the approved F0001 runtime scope.

Git itself reports the local changes. For a source-control UI, select this repository as the project root, or open `nebula.code-workspace` in an editor that supports VS Code multi-root workspaces. The parent `nebula/` is not a Git repository. This clone's `.githooks` and `merge.ours` driver are configured; each new clone needs the setup commands in CONTRIBUTING.

### Publication record — 2026-09-07

The framework changes were prepared on `codex/project-extensions-20260907` (local commit `9a68f7a9c6ba9a0b13d2b5814e06b7fed055e836`). Git transport was unavailable in the authoring session, so publication was deferred rather than abandoned; it was subsequently completed from an environment with working transport. `nebula-agents` PR #91 merged that branch to `main` as `c218bf1776f509a30f71967a1ee79879caa9a000`, and Brain PR #1 merged `codex/brain-project-adoption-20260907` to this repository's `main`. The unreferenced API object created during the failed attempt (`3a6f7f21b513f834ef4b7c1418d51cb8f849956a`) is not a release pin and is not referenced by anything.

Remaining local hygiene: each sibling checkout should be switched to `main` and fast-forwarded from `origin/main`. The `nebula-agents` clone is still on `codex/project-extensions-20260907`, and its local `main` remains at the superseded `4eaf7b3`. Do not merge the pre-squash publication histories back into `main`; delete those branches once each clone is verified against remote `main`.
