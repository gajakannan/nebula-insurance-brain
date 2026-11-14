# Test Plan — F0064 Repository instructions and planning-check adoption

Role: Quality Engineer (Claude Opus 5.5). Date: 2026-11-14.

## Scope

Re-verify the Brain-side project-extension adoption delivered 2026-09-07 against all 23 acceptance criteria, at framework pin `d90bbb6`. Follow assembly plan Steps 1–4. No runtime code, UI or AI scope, so there are no E2E browser tests. Every "test" is an executable command whose output is saved under `artifacts/test-results/`, `artifacts/coverage/`, or the CI run on the closeout PR.

## Method

- **Real tree, read-only.** Positive checks run on the working tree. S0003 AC7 brackets the real-tree validator invocations with a hash of every tracked file (`artifacts/test-results/tree-hash.py`, symlink-aware), plus `git status`.
- **Copies for negatives.** Every negative case runs on a fresh `git archive HEAD` copy in the session scratchpad. The working tree is never broken to stage a failure (S0001 assumption, GETTING-STARTED note).
- **Explicit root.** Framework commands pass `--product-root` explicitly. Step 1 runs with `NEBULA_PRODUCT_ROOT` unset (`env -u`).
- **Interpreters.** Product scripts run under the repository `.venv` (Python 3.12.13). S0002 AC2 also runs the literal `python3` (3.14.4). The framework runs under its `.venv` (3.14.4).
- **Defect rule (G1 decision 3).** Every defect is repaired and re-verified before closeout. Nothing is deferred.

## AC → Test Matrix

| Story | AC | Test (assembly step) | Evidence |
|---|---|---|---|
| S0001 | AC1 | YAML assertions on exact fields (1.1) | `s0001-manifest-assertions.{py,txt}` |
| S0001 | AC2 | argv/placeholder/no-shell assertions (1.1) | `s0001-manifest-assertions.txt` |
| S0001 | AC3 | `project_context.py --json` for plan-review and plan, ×2 each, diffed (1.2) | `s0001-context-*-run{1,2}.json`, `s0001-ac3-summary.txt` |
| S0001 | AC4 | `project_checks.py … --list` (1.3) | `s0001-ac4-list.txt` |
| S0001 | AC5 | patterns → tracked files; validator reads ⊆ patterns (1.4) | `s0001-manifest-assertions.txt` |
| S0001 | Edge | copy without `docs/agent-instructions.md` → context fails visibly (1.5) | `s0001-edge-missing-instruction.txt` |
| S0002 | AC1 | line references in `docs/agent-instructions.md` (2.1) | test-execution-report |
| S0002 | AC2 | three documented commands, `.venv` and `python3` (2.2) | `s0002-ac2-*.txt` |
| S0002 | AC3/AC4 | checklist structure assertions (2.3, 2.4) | `s0002-checklist-assertions.{py,txt}` |
| S0002 | AC5 | framework search for rule IDs and distinctive sentences (2.5) | `s0002-ac5-framework-grep.txt` |
| S0003 | AC1, AC2 (exit 2), AC5, AC6, AC7, NFE | real-tree script with hash bracketing (3.1, 3.2, 3.5–3.8) | `s0003-real-tree.{sh,txt}`, `s0003-ac7-*` |
| S0003 | AC2 (exit 1), AC4 | copy cases: emptied PRD section; Active row without PRD; archived PRD deleted (3.2, 3.4) | `s0003-copy-cases.{sh,txt}` |
| S0003 | AC3 | fixture suite, verbose (3.3) | `s0003-ac3-pytest.txt` |
| S0004 | AC1, AC2 | CI job inspection with line references; pin agreement (4.1, 4.2) | `s0004-ac1-ci-inspection.txt`, `g1-preflight.txt` |
| S0004 | AC3 | shared executor on a copy lacking BRAIN-EXAMPLES; run folder copied back; real tree hashed (4.3) | `s0004-ac3-negative.{sh,txt}`, `s0004-ac3-copy-run/` |
| S0004 | AC4 | CI on the closeout PR, all jobs (4.7) | CI run URL in test-execution-report |
| S0004 | AC5 | CONTRIBUTING paths exist; documented commands run; workspace paths resolve (4.4) | `s0004-ac5-paths.txt`, `s0004-contributing-*.txt` |
| S0004 | AC6 | doc repairs applied and reviewed (4.5) | `artifacts/diffs/`, code review |
| — | Step 4.6 | `pytest scripts/kg/tests` → repair the CONTRIBUTING line 26 claim | `s0004-step4.6-kg-tests.txt` |

## Integration Checkpoints

- After Step 3: validator (project scope), fixtures (11 tests) and `--list` all agree before any document edit.
- Cross-story: `manifest_hash` from Step 1.2 equals `identity.manifest` in the Step 4.3 executor result.

## Coverage Approach

No changed executable lines. For the delivered validator under verification, measure branch coverage of `scripts/validation/validate_plan_readiness.py` across the fixture suite plus the S0003 CLI invocations (`artifacts/coverage/combined-coverage.*`), against the contract floor.

## Exit Criteria

All 23 ACs PASS with saved evidence. Every defect repaired and re-verified. Lifecycle gates green after the documentation edits, with coverage refreshed after `git add`. CI green on the PR.
