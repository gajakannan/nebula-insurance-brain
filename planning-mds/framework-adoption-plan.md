# Plan: Repo-specific instructions and checks

Status: Local implementation verified; lifecycle review and release/pin coordination pending.
Date: 2026-09-07 (design authored 2026-09-06)

The goal is to let each product own its instructions, review criteria, and scripts while `nebula-agents` supplies a reusable way to discover them and run required checks. Instructions are the first deliverable. Hooks provide automatic execution where a local check must affect a gate result.

## Ownership and scope

| Owner | Deliverables |
|---|---|
| `nebula-agents` | Versioned extension contract, instruction discovery, command execution, gate integration, evidence, generic tests and templates |
| `nebula-insurance-brain` | Local instructions, local review checklist, local validation script and fixtures, declarations selecting when to run them |
| Agent host or CI | Invoke the same framework entry points with an explicit product root |

The initial release supports instruction loading for framework action sessions and one validation extension point: `plan-review` PR2, before that stage completes. It does not introduce a new action orchestrator, replace framework checks or approvals, or implement general before/after hooks for every tool call. Native host hooks and additional action extension points can follow demonstrated need.

This does not amend the approved F0001 product scope. The generic work is reserved as framework F0009 and the adoption as Brain F0064 through authored feature shards. Both remain Planned pending lifecycle review and rollout; local implementation is not a delivery signoff.

## Existing foundations

- [BLUEPRINT.md](BLUEPRINT.md) already owns product process, scope, stack, and references to architectural authority. Preserve that ownership.
- [`CONSUMER-CONTRACT.md`](../../nebula-agents/CONSUMER-CONTRACT.md) and [`_product_root.py`](../../nebula-agents/agents/scripts/_product_root.py) define product-root indirection. Brain sessions are normally launched from the sibling framework directory.
- [`run-gate.py`](../../nebula-agents/agents/scripts/run-gate.py) already records stage state, operations, checkpoints, and evidence. A paused stage can return process exit code zero; process success alone is not action completion.
- [`gate_runtime.py`](../../nebula-agents/agents/scripts/gate_runtime.py) already executes argument arrays with explicit working directories, timeouts, and normalized command logs.
- [`plan-review.yaml`](../../nebula-agents/agents/actions/spec/plan-review.yaml) already separates PR2 validation from PR4 readiness judgment.
- At initial inspection, [`docs/framework-adoption.md`](../docs/framework-adoption.md) and [`validate_plan_compliance.py`](../scripts/kg/validate_plan_compliance.py) were untracked drafts. The placeholder validator has now been migrated to a compatibility entry point for the new structural validator, with failing exit codes preserved.
- The framework prompt renderer and generated prompts have existing local changes. Implement later changes against that work without overwriting it; do not hand-edit generated prompts.

## Proposed product contract

Use one optional root manifest, `.nebula-project.yaml`, because the contract covers both instructions and executable checks. This replaces the proposed separate `.nebula-hooks.yaml`; the mechanism can still be described as project validation hooks. The contract is implemented in the local candidate framework; the existing published pin predates it.

```text
nebula-insurance-brain/
  .nebula-project.yaml
  planning-mds/BLUEPRINT.md          # existing authority
  docs/agent-instructions.md        # local working conventions and source links
  docs/plan-review-checklist.md     # local review criteria and ownership
  scripts/validation/
    validate_plan_readiness.py      # deterministic local checks
    tests/                         # valid and invalid planning fixtures
```

Illustrative v1 manifest:

```yaml
version: 1
instructions:
  - path: docs/agent-instructions.md
  - path: docs/plan-review-checklist.md
    actions: [plan-review]
checks:
  - id: plan-readiness
    action: plan-review
    stage: PR2
    event: before_stage_complete
    argv:
      - python3
      - "{PRODUCT_ROOT}/scripts/validation/validate_plan_readiness.py"
      - --product-root
      - "{PRODUCT_ROOT}"
      - --plan-scope
      - "{PLAN_SCOPE}"
      - --target
      - "{TARGET}"
    cwd: product
    timeout_seconds: 60
    inputs:
      - planning-mds/BLUEPRINT.md
      - docs/plan-review-checklist.md
      - scripts/validation/**
      - "{FEATURE_PATH}/**/*.md"
```

All declared checks are required in v1. Success means all applicable framework checks and project checks pass; a successful project check never clears a framework failure. Guidance-only concerns belong in instruction files and reviewer findings.

The sample invocation is feature-scoped. Feature-set review must resolve and validate every target separately. Project review must have an explicit product-wide invocation that checks the local instruction/authority contract and applicable plans. Implement scope-aware argument binding before claiming support for those scopes; unresolved targets or unsupported scopes must be reported as blocked, never as successful skips.

### Discovery and instruction loading

1. Resolve the product once from `--product-root`, then `NEBULA_PRODUCT_ROOT`. The new extension commands require one of these; they must not silently select the CRM fallback. Leave unrelated legacy commands compatible.
2. Validate the selected root and echo its absolute path. Resolve the manifest, instructions, check scripts, and inputs against that root, independent of launch CWD.
3. Load the product's existing blueprint, then the manifest's applicable instruction files in declared order. Respect the action's prerequisites: an initial scaffold action may not have a blueprint yet. Select only the current action's additional guidance; provide paths and content hashes for audit. Do not recursively load every linked planning document.
4. Ensure the agent receives the actual applicable instruction text before action work, through prompt assembly or an explicit context-loading step in both generated prompt variants. Merely printing a filename is insufficient. Loading guidance is not proof that the model followed it.
5. Keep framework templates generic: commit the discovery procedure, never a consumer's instruction text. Local guidance supplies product decisions within the framework's scope and approval rules; report conflicts rather than silently overriding either contract.
6. A repository without a manifest keeps its existing behavior. An instruction-only manifest works with `checks: []`. A present but invalid manifest or missing declared instruction blocks the affected action.

The loader validates unknown fields, versions, action names, duplicate IDs, unsupported extension points, unresolved placeholders, and missing inputs. Resolve symlinks before verifying that product-owned paths stay inside the selected root. Reject configuration that requests arbitrary shell evaluation. Explicitly referenced instruction files must be surfaced even if a broad-search ignore rule hides them; record that targeted load.

### Gate execution and evidence

- Execute the existing PR2 operations, then its project checks, then mark PR2 complete. PR4 must verify that the required PR2 checks passed for the current inputs before issuing readiness.
- Reuse `gate_runtime.py` for execution and logging. The framework captures validator output into the base run's `artifacts/` directory; validators read product files and emit results, rather than modifying plans or approvals.
- Use a small output contract: JSON with `schema_version`, `check_id`, `status` (`pass` or `fail`), and `findings` containing rule IDs, messages, and product-relative source references. Exit code 0 means pass, 1 means validation failure, and 2 means invocation/configuration error. Crashes, timeouts, invalid JSON, and disagreement between exit code and result block the gate.
- Record run ID, action, target scope, framework pin, check ID, resolved command/CWD, input hashes, exit status, duration, and output references. Reuse `commands.log`, `lifecycle-gates.log`, and `gate-state.json`; extend their schemas through the framework's existing contract process where needed.
- Bind completion to the manifest, applicable instructions, validator and declared local dependencies, resolved input file set, and input contents. Missing previously recorded files, added inputs, or changed contents invalidate the result. Do not treat an already-completed journal entry as a fresh pass without checking this identity.
- Snapshot the manifest identity at run start. Removing a required check or deleting the manifest during a run cannot silently turn a failure into a pass. Report configuration drift and require a new validated run context.
- Keep checks repeatable. On resume, reuse only successful checks with unchanged inputs; rerun failed or invalidated checks. `--from`, `--force`, and direct PR4 invocation must not bypass required checks or existing approval checkpoints.
- `--list` and `--dry-run` show resolved instructions and applicable project checks without executing scripts or writing run state. Framework-only listing remains available without a product root.

These controls govern supported framework execution and CI. They do not sandbox arbitrary local scripts or guarantee that an agent cannot issue unrelated direct commands. Use the host's existing permissions, and treat project scripts as repository code under the same trust model as other build and test scripts.

## Delivery sequence

### 1. Define and implement instruction discovery

Framework work:

- Add the manifest schema and generic discovery module, proposed as `agents/scripts/project_context.py`, with a CLI for inspecting resolved context.
- Document the contract in `CONSUMER-CONTRACT.md` and session setup in `agents/docs/AGENT-USE.md`.
- Integrate discovery into the shared action context procedure in `agents/actions/spec/_contract.yaml` and `render-prompts.py`; regenerate operator and automation prompts.
- Verify launch and resume paths carry the explicit product identity. If the native launcher is used, inspect `engine/src/nebula_agents/application/runs.py` and its provider-entry boundary; do not depend on a shell export surviving an environment allowlist.

Product work:

- Author `docs/agent-instructions.md` with working conventions, links to the blueprint and authoritative architecture, and local script entry points.
- Reconcile the existing adoption draft with those sources. `BOUNDARY-POLICY.md` governs framework/product separation; it is not an insurance regulatory policy. Remove that conflation from the draft during implementation.
- Add an instruction-only manifest and a short blueprint reference. Avoid duplicating business rules or creating a competing source of truth.

Acceptance: two synthetic products load different instructions from the same unchanged framework; launch from a workspace root, framework root, or product subdirectory produces the same selected product context. A missing manifest preserves legacy behavior; a broken declared instruction fails visibly.

### 2. Make the local readiness validator useful on its own

- Replace the draft keyword-based compliance check with `scripts/validation/validate_plan_readiness.py`; preserve or migrate existing user work deliberately when implementation begins.
- Define the check list from accepted Brain requirements, with a source reference for each rule. Separate deterministic checks from architectural judgment.
- First automate nonempty/resolvable target plans, required planning sections and authored planning references, and structural completeness of the local review checklist. Require each applicable checklist item to name its governing source and planning evidence reference, or an explicit not-applicable rationale. Distinguish existing planning artifacts from explicitly proposed implementation paths; a readiness check must not require future runtime files or completed runtime proofs simply because a plan names them.
- Leave semantic adequacy of tenancy, provenance, parse-once behavior, and proposed ADR decisions to the assigned reviewers, using the local checklist. Do not label keyword presence or structural validation as regulatory compliance or proof of architectural correctness.
- Implement explicit paths, the structured output/exit-code contract, declared input coverage, and tests for meaningful failures. Support feature, feature-set, and project scopes explicitly as described above.

Acceptance: a valid fixture passes, including one that names future implementation files; empty plans, missing required planning references, incomplete required checklist entries, invalid scope, and malformed inputs fail for the expected reason. The same invocation works from different CWDs and does not modify source artifacts.

### 3. Connect local checks to the existing gate runner

- Add the generic check resolver/executor, proposed as `agents/scripts/project_checks.py`, using the discovery module and existing runtime.
- Extend the action-spec schema to declare supported project validation points. Initially expose only `plan-review` PR2 before completion.
- Integrate resolved checks into `run-gate.py`, including listing, dry-run, evidence, completion identity, and resume behavior.
- Carry the action's `PLAN_SCOPE` and `TARGET` into the runner's structured context so feature-set and project invocations do not inherit an unresolved single-feature placeholder. Resolve feature targets from the registry and preserve the same scope through checks, logs, and readiness.
- Require PR4 to consult current PR2 evidence; retain distinct statuses for paused, failed, and completed operations.
- Enable the Brain check in its manifest after the standalone validator passes its fixtures.

Acceptance: a project failure prevents PR2 completion and PR4 readiness, even when every framework validator passes. A framework failure stays a failure. Missing scripts, timeout, invalid output, changed inputs, removed declarations, and attempts to resume past the check are covered by regression tests.

### 4. Verify host-independent usage and CI

- Document one shared invocation/context-loading procedure using explicit product root, action, scope, and run ID. Interactive hosts and automation use the same instruction resolver and gate/check implementation.
- Keep any host-specific instructions or launcher shims thin. Each forwards context to the shared interface; it does not reimplement validation. Verify Claude Code, Codex, and Hermes integrations separately when those hosts are available; record untested adapters explicitly.
- Add product CI for manifest validation, local validator fixtures, and the declared check set over the relevant planning scope. CI reruns deterministic checks without launching an LLM or asserting reviewer approval.
- Have CI invoke the same resolver/executor used by the action gate. Keep existing lifecycle and tracker checks. Install the project's test dependencies explicitly.
- Expand generic regression fixtures to include a second consumer without insurance vocabulary. Confirm that its rules work without a framework source change.

Acceptance: the same product inputs yield the same selected instructions, commands, and check outcomes through the shared CLI and CI. A deliberately invalid plan fails CI. Guidance to an interactive agent is documented as an invocation convention; mandatory completion checks are enforced by the runner and CI.

### 5. Roll out and pin the adoption

- Land and validate the generic framework change first; coordinate with the in-progress F0007 renderer work and record any action/evidence contract version change.
- Update Brain's framework pin in `BLUEPRINT.md` and `.github/workflows/ci-gates.yml` together, then enable its manifest/check declaration.
- Correct `CONTRIBUTING.md` so product commands and sibling-framework commands resolve properly. Document direct local validation and normal action usage.
- Run one successful and one deliberately failing review against fixtures in a temporary test product. Record that the framework gate, local result, and final readiness agree.
- Adopt the mechanism in a second real consumer only after the fixture-based isolation check passes. Additional hooks or provider-specific automation remain follow-up work.

Acceptance: a fresh Brain checkout has documented dependency setup, loads its own instructions from a framework-root session, and runs its required local checks before readiness. Framework and product tests plus applicable lifecycle gates pass at the coordinated pins.

## Completion criteria and boundaries

The work is complete when a product can add or change local instructions and an existing declared check without editing `nebula-agents`, all participating execution paths resolve the intended product, and required check failures are reflected in durable gate state and CI.

The earlier review also found copied KG tests, inactive local Git configuration, and unused path-class extensions in the pinned evidence validator. Those remain separately tracked findings. This plan addresses instruction discovery and local check execution; it does not claim that those other defects are fixed by adding hooks. In particular, general path-class evidence enforcement should be repaired in its owning validator rather than hidden inside Brain's plan-readiness script.

## Implementation decisions and remaining rollout

- Local instructions, strict manifest discovery, the structural validator, generic executor, gate integration, generated prompts, tests, and CI wiring are implemented. Both repositories have changes; no Brain business rule was embedded in the framework.
- The checklist's governing sources and evidence-inspection guidance are machine-validated. Feature-specific outcomes and explicit not-applicable rationales are required in the reviewer report by the instructions, not automatically judged by the structural validator.
- The optional project manifest and result use version 1. Journal fields are additive; historical action/evidence bundles are unchanged. Declared extension points participate in action behavioral diffs.
- The native cockpit was inspected: its prompt binder does not bind a separate product root and its provider environment allowlist excludes `NEBULA_PRODUCT_ROOT`. No native adapter was changed or claimed verified. Use the explicit shared CLI/context-loading convention for this rollout.
- Git sees the child-repository changes. This clone's existing hooks and merge driver are now configured, and a two-repository editor workspace is provided. The parent directory remains outside Git; no repository history was rewritten or nested repository flattened.
- The published framework pin is intentionally unchanged. **Before merging the consumer rollout, publish the generic framework change and update both the blueprint and CI ref together. The added CI compatibility gate fails at the old pin.** Existing overlapping renderer work is preserved, not silently committed.
- Neither registered feature is marked Done and no reviewer signoff or runtime approval has been manufactured. Formal lifecycle review, publication, and native-host integration tests remain outstanding.

## Local verification handoff — 2026-09-07

- Framework script tests plus Brain validator fixtures: **249 passed, 1 skipped** (`nebula-agents/.venv/bin/python -m pytest -q -p no:cacheprovider agents/scripts/tests ../nebula-insurance-brain/scripts/validation/tests`, from the framework root).
- Framework lifecycle: all **6 gates passed**, including genericness, generated-prompt drift, action-spec validation, and historical contract conformance.
- Brain planning lifecycle: both **2 gates passed** (KG integrity and reproducibility). Both repositories' tracker validation passed after compiling the new reserved feature shards.
- Brain registry-wide feature-evidence validation passed with **0 completed feature packages validated**; this is not evidence of runtime completion.
- The shared executor ran the actual Brain project-wide check successfully from the framework directory, recording `review_approval: false`. Diagnostic output is in the Git-ignored `.kg-state/project-check-verification/2026-09-07-a93d074b/`, not an approved action evidence package. The compatibility entry point also passed for F0001.
- Regression fixtures exercise successful and failing shared CLI runs for feature, feature-set, and project scopes, failed-check readiness rejection, resume, input/evidence changes, timeouts, malformed results, explicit-root isolation, and preservation of framework failures.
- Workflow YAML, matching existing blueprint/CI pins, editor workspace paths, generated prompt freshness, and both tracked diffs' whitespace checks passed. Git reports tracked and untracked changes in both child repositories. No commits or pushes were made.
- The full copied Brain KG test suite was not rerun for this change. Its **5 previously observed framework-specific lookup fixture failures** remain a separate finding; the applicable KG lifecycle gates pass.

Remaining: publish/review the framework change, advance both consumer pins together, run hosted CI at that revision, and perform any desired native-host adapter integration work. The consumer CI compatibility gate intentionally fails at the unchanged old pin. Do not merge the consumer rollout as if those release checks had passed.

## Coordinated publication handoff — 2026-09-07

The operator subsequently authorized committing all current framework/Brain changes and pushing them, with local synchronization after squash merging. Framework commit `9a68f7a9c6ba9a0b13d2b5814e06b7fed055e836` includes all 46 pending framework files. Brain's changes are prepared on `codex/brain-project-adoption-20260907` rather than committed directly to main.

Additional verification before publication: **433 agents/product-validator tests passed, 1 skipped**; the framework KG suite had **186 passed, 1 skipped**; all 6 framework lifecycle gates passed. The framework staged additions passed the repository's regex credential checks.

Publication is blocked by the environment, not by a merge conflict: direct Git transport cannot resolve GitHub, and the connected API denied remote branch creation because approval is unavailable. An equivalent framework commit object was uploaded, but it has no publication branch/PR. Main refs were not changed, there was no squash merge, and no final release SHA exists to use for the coordinated pin update. See [publication status](../docs/framework-adoption.md) for branch names and the safe continuation sequence.
