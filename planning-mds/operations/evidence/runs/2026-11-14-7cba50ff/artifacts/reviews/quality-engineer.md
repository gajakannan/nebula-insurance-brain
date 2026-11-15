# Test Evidence and Coverage — Quality Engineer

Reviewer: Codex, independent QE lane. Date: 2026-11-14. Scope: F0064, closeout-audit, PRs 48/49/50. NEBULA_PRODUCT_ROOT: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`.

Canonical feature-run-relative citations in this report resolve against `planning-mds/operations/evidence/runs/2026-11-14-3325803a/`. Review-run artifacts resolve against `planning-mds/operations/evidence/runs/2026-11-14-7cba50ff/`. The canonical package was read only.

## Decision

PASS with two Low evidence-quality findings; no Critical, High or Medium QE finding. All 23 acceptance criteria have concrete evidence. The final closeout PR #50 has current successful CI evidence in this review run. Statement, branch and combined coverage each exceed 80%. The historical coverage label overstates branch coverage, but does not change the floor result.

## Findings By Severity

### QE-L1 — Low — Combined coverage is labeled branch coverage

`coverage-report.md:12` calls the validator measurement **88% branch coverage**. Raw `artifacts/coverage/combined-coverage.json:1` reports 115 covered statements of 127, and 52 covered branches of 62. The precise values are 90.55% statement coverage, 83.87% branch coverage, and 88.36% combined coverage. The text output at `artifacts/coverage/combined-coverage.txt:14` uses coverage.py's combined `Cover` column. This is evidence-label drift. All three values clear 80%, so no coverage waiver or behavioral repair is needed. Owner: Quality Engineer. Follow-up: in targeted evidence rework, label the combined number accurately and preserve the separate statement/branch denominators.

### QE-L2 — Low — Earlier failed gate diagnostics are not retained at their cited output paths

Canonical `commands.log:3`, `commands.log:8` and `commands.log:52` record failed G0/G1/G5 gate-driver attempts and cite `artifacts/gates/g0.txt`, `artifacts/gates/g1.txt` and `artifacts/gates/g5.txt`. Each cited file now contains only the final `status: pass` driver result. `lifecycle-gates.log:2`, `lifecycle-gates.log:26` and `lifecycle-gates.log:66` retain the failure exit codes, with `Output References: -`; the second G0 failure is also preserved at `lifecycle-gates.log:10`. Thus attempt history survives, while those original detailed diagnostics cannot be verified from the cited files. The classifications described in `feature-action-execution.md` are narrative context, not preserved raw diagnostic proof. This is an evidence-retention limitation; it does not establish an unresolved product failure. Owner: Quality Engineer with the lifecycle coordinator. Follow-up: retain attempt-specific diagnostic artifacts and cite their immutable names in future/reworked evidence.

## Completion Checks

The archived story files explicitly define 5 + 5 + 7 + 6 = 23 ACs. Each was compared with raw output or the actual delivered source; the reported PASS count was not accepted on summary alone.

| Story / AC | Result | Concrete evidence checked |
|---|---|---|
| S0001 AC1 | PASS | `.nebula-project.yaml:1`; `artifacts/test-results/s0001-manifest-assertions.txt:1` records version, instruction order/filter, exact check stage/event/cwd/timeout. |
| S0001 AC2 | PASS | `.nebula-project.yaml:11`; `artifacts/test-results/s0001-manifest-assertions.txt:12` verifies argv, placeholders and no shell evaluation. |
| S0001 AC3 | PASS | `artifacts/test-results/s0001-context-plan-review-run1.json`, `s0001-context-plan-review-run2.json`, `s0001-context-plan-run1.json`, `s0001-context-plan-run2.json`; parsed each and independently compared paired bytes and instruction ordering. |
| S0001 AC4 | PASS | `artifacts/test-results/s0001-ac4-list.txt`: parsed exactly one resolved `plan-readiness` check. |
| S0001 AC5 | PASS | `.nebula-project.yaml:22`; `artifacts/test-results/s0001-manifest-assertions.txt:21` verifies nonempty tracked matches and all 88 validator-read files covered by the declared patterns. |
| S0002 AC1 | PASS | Actual delivered `docs/agent-instructions.md:3`, `:8`, `:15` states source authority, explicit root and authored/generated KG separation. |
| S0002 AC2 | PASS | `artifacts/test-results/s0002-ac2-cmd1-feature-F0001.txt:1`, `s0002-ac2-cmd2-project.txt:1`, `s0002-ac2-cmd3-lifecycle-gates.txt:1`, and `s0002-ac2-system-python3.txt:1` retain successful documented commands under both interpreter paths. |
| S0002 AC3 | PASS | Actual `docs/plan-review-checklist.md:7`; `artifacts/test-results/s0002-checklist-assertions.txt:1` verifies eight rule IDs, owners and governing-source existence. |
| S0002 AC4 | PASS | Actual `docs/plan-review-checklist.md:3` and `:5`; `artifacts/test-results/s0002-checklist-assertions.txt:27`. |
| S0002 AC5 | PASS | `artifacts/test-results/s0002-ac5-framework-grep.txt:1` contains no Brain rule/text hit in the declared framework search. |
| S0003 AC1 | PASS | `artifacts/test-results/s0003-real-tree.txt:1` retains exact pass JSON and exit 0. |
| S0003 AC2 | PASS | `artifacts/test-results/s0003-real-tree.txt:13` retains four invalid invocations, each exit 2 plus BRAIN-INVOCATION; `s0003-copy-cases.txt:1` retains exit 1 plus BRAIN-SECTIONS for a broken planning copy. |
| S0003 AC3 | PASS | Actual `scripts/validation/tests/test_plan_readiness.py:77` onward; `artifacts/test-results/s0003-ac3-pytest.txt:8` lists all 11 executed cases and ends with 11 passed. Fixtures exercise meaningful outcomes, references, scope and non-mutation. |
| S0003 AC4 | PASS | Actual `scripts/validation/validate_plan_readiness.py:85`; `artifacts/test-results/s0003-copy-cases.txt:16` proves Active-without-PRD selection; `:62` proves archived exclusion. |
| S0003 AC5 | PASS | `artifacts/test-results/s0003-real-tree.txt:74` retains accepted feature-plan path exit 0 and outside-tree path exit 2. |
| S0003 AC6 | PASS | Original `artifacts/test-results/s0003-real-tree.txt:88`; independently re-executed against the archived current F0064 package with explicit root, exit 0. Current raw output is review-run `artifacts/reviews/qe-current-feature-readiness.txt:1`. |
| S0003 AC7 | PASS | Independently compared `artifacts/test-results/s0003-ac7-hash-before.txt` and `s0003-ac7-hash-after.txt`, plus the two `s0003-ac7-status-*.txt` files; all pairs are byte-identical. Hash list includes 3,865 tracked files plus its total line. |
| S0004 AC1 | PASS | Actual `.github/workflows/ci-gates.yml:304` onward; recorded `artifacts/test-results/s0004-ac1-ci-inspection.txt:1`; final PR #50 framework-validators steps 8–11 all success in review-run `artifacts/ci-pr50-jobs.json`. |
| S0004 AC2 | PASS | `artifacts/test-results/g1-preflight.txt:3` shows framework HEAD, CI ref and BLUEPRINT pin at d90bbb6fc70dffcfa6d70379d42015e895a49fa0. Actual workflow still names the same full SHA. |
| S0004 AC3 | PASS | `artifacts/test-results/s0004-ac3-negative.txt:1`; parsed nested `s0004-ac3-copy-run/artifacts/project-checks/PR2-plan-readiness-b5192693076344109f8f450bb7297608.result.json`: exit 1, BRAIN-CHECKLIST, missing BRAIN-EXAMPLES. Independent hash comparison proves real-tree non-mutation; executor and context manifest hashes match. |
| S0004 AC4 | PASS | Historical PR #49 raw output `artifacts/test-results/s0004-ac4-ci-checks-run1.txt` ends with every job pass and exit 0. Current closeout PR #50 head abe5045f785bf4aea4c6dfa09783cc145d2cf1b7: review-run `artifacts/ci-pr50-jobs.json` shows all five CI Gates jobs in run 43652089357 successful, including framework extension steps, plus successful reproducibility run 43652089362. Canonical reports' PR #49 provenance is handled by PM. |
| S0004 AC5 | PASS | `artifacts/test-results/s0004-ac5-paths.txt:1` resolves all 17 named paths and both workspace folders; `s0004-contributing-validation-tests.txt:186` records 63 passed; `s0004-contributing-framework-cmds.txt` records documented framework commands exit 0. |
| S0004 AC6 | PASS | Read actual repairs in `artifacts/diffs/doc-repairs.diff:1`: adoption status/pin/hygiene updated, dated publication history retained, stale KG-test claim corrected. `artifacts/test-results/s0004-step4.6-kg-tests.txt:4` records 189 passed. |

Additional required paths checked: S0001's missing-instruction edge case produces visible `path_missing` and exit 2 (`artifacts/test-results/s0001-edge-missing-instruction.txt:1`). Context output is deterministic, independently byte-checked. S0003's project-scope NFE is 0.046 seconds (`artifacts/test-results/s0003-real-tree.txt:11`), below the 60-second manifest timeout. Future-runtime-path and unresolved-story-reference edge cases are present in the executed fixture suite.

## Coverage and Runtime Evidence

No executable product code changed in the locked PR set. The measured denominator is the existing validator deliberately re-verified by S0003: 127 statements and 62 branches. The independent raw audit confirms 115 covered statements and 52 covered branches. The supplied measurement script `artifacts/coverage/combined-coverage.sh:1` combines the 11 fixtures with real CLI exit-code/scope cases and isolated broken copies. The fixture-only report was not substituted for combined coverage.

Toolchain preflight at `artifacts/test-results/g1-preflight.txt:1` precedes testing and records framework SHA, interpreter versions and clean scoped product tree. F0064 has no application service, database or frontend/AI runtime; a Python tooling preflight is appropriate. The raw 11-fixture result names actual cases; the wider 63 validation and 189 KG suites have retained outputs. No fresh broad suites were run during this audit because the current source is unchanged and the preserved raw evidence is sufficient. The one targeted current invocation resolves the material post-archive question.

Failure/retry history distinguishes expected negative cases from gate metadata/freshness fixes: missing instruction exit 2 and broken plan/checklist exit 1 are intended negative tests. `artifacts/test-results/post-edit-lifecycle-gates.txt:32` records the post-edit KG-freshness failure, and `pre-commit-1-validate.txt:14` / `:28` and its final reproducibility result retain passing rechecks. No service/network failure is represented as a code defect. Original diagnostics for earlier G0/G1/G5 failures have the retention limit in QE-L2.

## Skipped Layers and Rationale

- Browser E2E, accessibility, visual regression, product API/database integration and AI evaluation: no UI, API, database, runtime or model change exists in F0064. Repository tooling integration and CI execution supply the applicable end-to-end proof. No deferred layer is needed.
- New application-container preflight: no application runtime exists in this feature's scope; the retained toolchain preflight is the relevant runtime evidence.
- Local semantic-RDF execution: explicitly reported skipped in `artifacts/test-results/s0002-ac2-cmd3-lifecycle-gates.txt`, because rdflib was optional/missing at that invocation; it is not counted here as executed proof. The later 63-test output includes semantic examples/RDF tests and final CI product-gates succeeds. This does not leave an F0064 AC uncovered.
- Security scanners: manifest has explicit not-applicable waivers for this documentation-only changed set; security judgment remains the Security lane's responsibility.
- Framework internals, native host adapters, new extension points and semantic adequacy: explicit feature non-goals, not missing QE coverage.

## Validation Evidence and FR3 Self-Review

Independent audit output: review-run `artifacts/reviews/qe-raw-artifact-audit.json:1` records all eleven raw-artifact checks passing, including context pair hashes, instruction/check resolution, both tracked-file hash pairs, status comparison, cross-story manifest identity, negative-executor result and recomputed coverage. The first scratch parser attempt rejected the context files' prepended product-root diagnostic; the parser was corrected to read their JSON payload, then the complete raw audit passed. This was an audit-helper correction, not a product mutation or defect.

FR3: Findings cite exact raw diagnostics, raw counters, or retained output paths. No hidden acceptance from report summaries remains. All 23 dispositions point to actual source/output, with closeout CI checked at the exact PR #50 head. Skipped items are explicit and justified. No original feature evidence, code, tests, feature documents, trackers or KG artifacts were edited. FR2 required validators and the aggregate FR4 policy computation remain the orchestrator's responsibility.
