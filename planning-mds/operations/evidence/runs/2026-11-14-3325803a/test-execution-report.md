# Test Execution Report — F0064 Repository instructions and planning-check adoption

Role: Quality Engineer (Claude Opus 5.5). Date: 2026-11-14.
Framework `nebula-agents` at `d90bbb6fc70dffcfa6d70379d42015e895a49fa0`. Product base `fcb249d`. Verification commit `db723d5` on `feature/F0064-retro-closeout` (PR #49).
Every command is recorded in `commands.log`. Raw outputs are under `artifacts/test-results/`.

## Summary

- **23 of 23 acceptance criteria PASS**, plus the S0001 edge case and the S0003 non-functional expectation.
- **Defects found in the delivered tooling: 0.** Two documentation statements were stale and are repaired, as the assembly plan anticipated (Step 4.5/4.6). Under the S0002/S0004 edge-case rule, a stale statement is a defect, so both are recorded below as repaired.
- **Suites:** `scripts/validation/tests` 63 passed (11 in `test_plan_readiness.py`); `scripts/kg/tests` 189 passed.
- **Lifecycle gates:** all 4 pass before the doc edits. After the edits, `knowledge_graph_sync` failed only because `coverage-report.yaml` was stale, which is expected. It was regenerated after `git add`, and `validate.py`, `--check-drift` and `--check-reproducible` then pass (`pre-commit-1-validate.txt`). The pre-commit hook passed on `db723d5`.

## Results by Acceptance Criterion

### F0064-S0001 — Declare the product manifest

| AC | Result | Observation | Evidence |
|---|---|---|---|
| AC1 | PASS | `version: 1`; instructions in order, the checklist limited to `[plan-review]`; one check `plan-readiness` with `plan-review`/`PR2`/`before_stage_complete`/`product`/`60` | `s0001-manifest-assertions.txt` |
| AC2 | PASS | argv `python3` + `{NEBULA_PRODUCT_ROOT}/scripts/validation/validate_plan_readiness.py` with `--product-root/--plan-scope/--target`; placeholder set is exactly `{NEBULA_PRODUCT_ROOT, PLAN_SCOPE, TARGET}`; no shell token or shell key | same |
| AC3 | PASS | With `NEBULA_PRODUCT_ROOT` unset: plan-review lists BLUEPRINT → agent-instructions → checklist, each with a 64-hex SHA-256; `--action plan` omits the checklist. Two runs per action are byte-identical (determinism NFE). `manifest_hash` is `dedbcb94…3e089` | `s0001-context-*-run{1,2}.json`, `s0001-ac3-summary.txt` |
| AC4 | PASS | `--list` exit 0. Single check `plan-readiness`, every placeholder expanded (`--plan-scope project --target project`) | `s0001-ac4-list.txt` |
| AC5 | PASS | All 12 patterns match tracked files. The 88 files the validator reads (BLUEPRINT, 2 docs, 8 governing sources, REGISTRY, feature README/STATUS/PRD/stories, the validator itself) are all covered. Archived folders fall under `planning-mds/features/**/*.md` | `s0001-manifest-assertions.txt` |
| Edge | PASS | A copy without `docs/agent-instructions.md` gives exit 2, `{"code": "path_missing", "error": "Required product path is missing: docs/agent-instructions.md"}`. The failure is visible, not a silent omission | `s0001-edge-missing-instruction.txt` |

### F0064-S0002 — Agent instructions and review checklist

| AC | Result | Observation | Evidence |
|---|---|---|---|
| AC1 | PASS | `docs/agent-instructions.md:3` gives the source order (BLUEPRINT → master blueprint + ADRs → feature folders); `:8` requires `--product-root` or `NEBULA_PRODUCT_ROOT`; `:15` says kg-source is authored and `compile.py` generates the rest | file at `db723d5` |
| AC2 | PASS | All three documented commands exit 0 under `.venv` (3.12.13) and under the literal `python3` (3.14.4). Under `.venv`, `semantic_rdf` reports a skip (rdflib not installed); CI runs it with `--require` | `s0002-ac2-cmd{1,2,3}-*.txt`, `s0002-ac2-system-python3.txt` |
| AC3 | PASS | Header columns exact; exactly the 8 rule IDs; owners in the allowed set; all 8 governing sources resolve | `s0002-checklist-assertions.txt` |
| AC4 | PASS | `docs/plan-review-checklist.md:3` ("a script pass does not mean approval or regulatory compliance"); `:5` ("If a rule does not apply, record the reason explicitly") | same |
| AC5 | PASS | `grep -rn "BRAIN-"` over the framework's `agents/`, root `*.md` and `docs/` finds nothing (exit 1). A whole-repo search for 7 distinctive Brain sentences, including "Nebula Insurance Brain", finds nothing, fixtures included | `s0002-ac5-framework-grep.txt` |

### F0064-S0003 — Validate plan-readiness structure

| AC | Result | Observation | Evidence |
|---|---|---|---|
| AC1 | PASS | Project scope prints `{"schema_version": 1, "check_id": "plan-readiness", "status": "pass", "findings": []}`, exit 0 | `s0003-real-tree.txt` |
| AC2 | PASS | Exit 2 + `BRAIN-INVOCATION` for project+F0001, feature+2 targets, duplicate feature-set, malformed `F01`. Exit 1 + `BRAIN-SECTIONS: Dependencies` for a copy with an emptied PRD section | `s0003-real-tree.txt`, `s0003-copy-cases.txt` |
| AC3 | PASS | `test_plan_readiness.py`: 11 passed. The named tests cover the future-runtime-path plan, 4 invalid mutations, feature-set/project scopes, a missing governing source, the examples rule, non-mutation, a deleted active PRD, and an unresolved story reference | `s0003-ac3-pytest.txt` |
| AC4 | PASS | A copy with F0009 (no PRD) flipped to Active: it is selected, giving a missing-artifact finding. A copy with archived F0001's PRD deleted still passes, so archived features are not selected. Selection on HEAD = `F0064`, `F0065` | `s0003-copy-cases.txt` |
| AC5 | PASS | `validate_plan_compliance.py` on F0064 PRD exits 0; on root `README.md` exits 2 | `s0003-real-tree.txt` |
| AC6 | PASS | `--plan-scope feature --target F0064` passes | same |
| AC7 | PASS | 3,865 tracked files byte-identical (symlink-aware hash) and `git status` unchanged across Steps 3.1–3.6. The validator writes nothing | `s0003-ac7-hash-{before,after}.txt` |
| NFE | PASS | Project-scope wall time 0.046 s, against the 60 s timeout | `s0003-real-tree.txt` |

### F0064-S0004 — Enforce checks in CI and document setup

| AC | Result | Observation | Evidence |
|---|---|---|---|
| AC1 | PASS | `ci-gates.yml` `framework-validators`: checkout at the pinned ref L304–308; fail-closed guard L322–328; context L329–331; executor with a generated run ID L332–341; `always()` evidence upload L342–348 | `s0004-ac1-ci-inspection.txt` |
| AC2 | PASS | `ci-gates.yml:307` and BLUEPRINT section 0 both name `d90bbb6fc70dffcfa6d70379d42015e895a49fa0` | `g1-preflight.txt` |
| AC3 | PASS | Shared executor on a copy lacking the BRAIN-EXAMPLES row: exit 1, result `fail`, finding `BRAIN-CHECKLIST: Required local review criterion missing: BRAIN-EXAMPLES`. Run folder copied back. Real tree unchanged (3,865 files), and no run folder leaked into it. `identity.manifest` equals the Step 1.2 `manifest_hash` (cross-story checkpoint) | `s0004-ac3-negative.txt`, `s0004-ac3-copy-run/` |
| AC4 | PASS | PR #49 at `db723d5`: all 7 checks pass (product-gates, framework-validators, experience, runtime-stack, runtime-suites, 2× reproducibility). In `framework-validators` (run 43649628389), steps 8–11 (fail-closed guard, context, executor, evidence upload) all succeed; the executor prints `{"ok": true, "checks": 1}` and uploads `project-check-evidence` (artifact 14136010300). The final closeout commit is re-checked at G8 | `s0004-ac4-ci-checks-run1.txt`, `s0004-ac4-ci-framework-validators.txt` |
| AC5 | PASS | All 17 paths named in CONTRIBUTING exist; the `test` extra exists in `pyproject.toml`. Every documented command runs: product checks, the three framework validators, `project_context.py`, and `run-gate.py --list`. Workspace folders `.` and `../nebula-agents` resolve from the workspace file | `s0004-ac5-paths.txt`, `s0004-contributing-*.txt` |
| AC6 | PASS | Both adoption docs state rollout complete, the current pin and the F0064 closeout. The 2026-09-07 publication record is kept. Hygiene is stated complete, verified (both clones on `main`, no `codex/*` branches). The plan body keeps dated history under an explicit historical-record note | `artifacts/diffs/doc-repairs.diff` |

## Defects and Repairs

| # | Finding | Class | Repair | Re-verification |
|---|---|---|---|---|
| D-1 | `docs/framework-adoption.md` said both pins name `c218bf1` and listed local hygiene as remaining | Stale statement (S0004 AC6) | Current pin, hygiene complete (verified), F0064 reference through the registry so it survives the archive move | Diff reviewed; links resolve; lifecycle gates green |
| D-2 | `planning-mds/framework-adoption-plan.md` header said lifecycle review and pin coordination were pending | Stale statement (S0004 AC6) | Delivered status and a dated historical-record note; body unchanged | Same |
| D-3 | `CONTRIBUTING.md:26` claimed existing failures in the KG lookup fixtures | Stale statement (assembly Step 4.6) | Replaced with the observed result (full pass) | `s0004-step4.6-kg-tests.txt`: 189 passed |

No defect was found in the manifest, the validator, the fixtures, the compliance entry point, the CI job or the framework at the pin. No framework change or pin advance is needed.

## Observations (non-blocking, no action required)

- My first S0004 AC3 evidence script hashed the real tree after `cd`'ing into the framework, which produced a false "changed" result. This was a test-harness bug, not a product defect. It was replaced by the root-anchored `tree-hash.py`, and both AC7 and AC3 were re-run.
- Six git-tracked symlinks in F0004's evidence (`runs/2026-10-17-8a6cc79f/artifacts/review/*current`) point to container paths (`/app/brain/...`) and dangle on the host. They predate F0064, are outside its scope, and do not affect any F0064 check; the hasher records them by link target.

## Result

PASS
