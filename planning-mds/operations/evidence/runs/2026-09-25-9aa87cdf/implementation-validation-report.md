# Implementation Validation Report — validate run 2026-09-25-9aa87cdf

**Scope:** `all` (implementation lane, registry-wide form; `FEATURE_ID` unset). **Subject:** branch `docs/utopia-evolution` at `b1f4357`.
**Role:** Product Manager (tool lane). **Framework:** `nebula-agents` at the pinned commit `c218bf1`, as a detached worktree.

The branch changes no runtime code (`engine/`, `experience/`, `neuron/` untouched; see `artifacts/diffs/changed-files.txt`), so this lane runs the framework and product validators as tools.

## Commands Executed

`commands.log` holds 33 JSONL entries:

- **Entries 1–6:** the V1 spec operations, driven by `run-gate.py --action validate --stage V1`, recorded in `gate-state.json`.
- **Entries 7–19:** the same validators plus the architecture-hygiene and product checks, run through `exec-and-log.py`. That wrapper does not pass the child's output through, so these entries' artifact files held only a wrapper banner.
- **Entries 20–32:** a rerun of entries 7–19 with output captured directly into the artifact files and logged through `append-command-log.py`. **These artifact files are the authoritative outputs.**
- **Entry 33:** the vague-language lint.

| # | Command (V1 op or extension) | Exit | Artifact |
|---|---|---|---|
| i | `validate-trackers.py` (v1-validate-trackers; rerun with `--product-root`) | 0 | `artifacts/test-results/validate-trackers.txt` |
| ii | `validate-feature-evidence.py --product-root … --json` (v1-validate-feature-evidence-registry) | 0 | `artifacts/feature-evidence-validation.json` |
| iii | `generate-story-index.py …/features/` (v1-story-index) | 0 | No diff to `STORY-INDEX.md` |
| iv | `scripts/kg/validate.py --check-symbols` (v1-kg-check-symbols) | 0 | `artifacts/test-results/kg-check-symbols.txt` |
| v | `scripts/kg/validate.py --check-drift` (v1-kg-check-drift) | 0 | `artifacts/test-results/kg-check-drift.txt` |
| vi | `validate_templates.py` (v1-validate-templates) | 0 | `artifacts/test-results/validate-templates.txt` |
| + | `validate-stories.py --product-root …` | 0 | `artifacts/test-results/validate-stories.txt` |
| + | `scripts/kg/validate.py --check-reproducible` | 0 | `artifacts/test-results/kg-check-reproducible.txt` |
| + | `scripts/kg/validate.py --check-orphans` (architect hygiene) | 0 | `artifacts/test-results/kg-check-orphans.txt` |
| + | `scripts/kg/dead-code.py --safe-only` (architect hygiene) | 0 | `artifacts/test-results/kg-dead-code-safe-only.txt` |
| + | `scripts/run-lifecycle-gates.py` (product gates) | 0 | `artifacts/test-results/product-lifecycle-gates.txt` |
| + | `validate_plan_readiness.py --plan-scope project --target project` | 0 | `artifacts/test-results/plan-readiness-project.json` |
| + | `validate_semantic_examples.py` | 0 | `artifacts/test-results/semantic-examples.txt` |
| + | `pytest scripts/validation/tests` (via `uv run --no-project`) | 0 | `artifacts/test-results/validation-pytest.txt` (31 passed) |
| + | `lint-vague-language.py artifacts/diffs/added-markdown-lines.md` | 1 | `artifacts/test-results/vague-language-added-lines.txt` (2 hits; see PM P-4) |

No validator returned exit code 2, so no validator invocation error needed escalating.

## Errors / Warnings / Info

- **Feature evidence (registry-wide, closeout, effective date 2026-05-19):** 1 feature validated (F0001); 0 errors, 0 warnings, 0 info.
- **Trackers:** 0 errors, 0 warnings.
- **Stories:** 23 stories, 0 failures. There are 10 warnings, all on stories this branch did not change: archived F0001, F0002-S0003/S0006, and F0065-S0001.
- **Knowledge graph:** 0 errors. Two pre-existing warnings: unused edge types `validated_by` and `supersedes`.
- **Product lifecycle gates:** 3 of 3 PASS (`knowledge_graph_sync`, `kg_reproducibility`, `semantic_examples`). On `main` at `93cc8c1` the `knowledge_graph_sync` gate fails because its coverage report is stale; this branch refreshes the report.
- **Plan readiness (project):** `pass`, no findings.

## KG Drift Status

- **Drift:** none (`--check-drift` exit 0).
- **Reproducibility:** committed projections and tracker regions equal compile(source) (`--check-reproducible` exit 0).
- **Symbols:** 260 symbols on bound nodes.
- **Coverage:** 4 mapped, 62 excluded, 0 uncovered.

## Template Alignment

`validate_templates.py`: prompt templates align with the action contracts (PASS).

## Findings (cross-referenced to §22 rule IDs)

No §22 feature-evidence rule fired: `artifacts/feature-evidence-validation.json` has empty `errors`, `warnings`, and `info`. The findings below are process observations about this run.

| ID | Severity | Finding |
|---|---|---|
| I-1 | Info | The `commands.log` entries appended through `append-command-log.py` with `--cwd framework` / `--cwd product` were normalized to `{PRODUCT_ROOT}/framework` and `{PRODUCT_ROOT}/product`. The commands actually ran in the pinned framework worktree and the product root respectively. |
| I-2 | Info | Entries 7–19 reference artifact files that were later overwritten with captured output by the rerun (entries 20–32). The overwritten files are the rerun's outputs. The exit codes of both runs agree (all 0). |
| I-3 | Info | The framework gaps are recorded as architect finding A-8: `init-run.py` requires `--feature`; the prompt's manifest wording conflicts with the spec; `exec-and-log.py` does not capture output. |

## Result

**PASS.** Every required validator ran; exit codes are recorded; no errors are hidden. The lint's exit code 1 is reported as PM finding P-4 and not suppressed.
