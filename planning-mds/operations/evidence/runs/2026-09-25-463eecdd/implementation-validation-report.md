# Implementation Validation Report — validate run 2026-09-25-463eecdd

**Scope:** `all` (implementation lane, registry-wide). **Subject:** `docs/utopia-evolution` @ `d897b46`. **Rerun of:** `2026-09-25-9aa87cdf`.

## Commands Executed

`commands.log` holds 20 entries:

- **Entries 1–6:** the V1 spec operations via `run-gate.py` (journal: `gate-state.json`).
- **Entries 7–20:** direct runs with output captured into `artifacts/` and logged through `append-command-log.py`.

| Command | Exit | Artifact |
|---|---|---|
| validate-trackers.py (spec op; rerun with `--product-root`) | 0 | `artifacts/test-results/validate-trackers.txt` |
| validate-feature-evidence.py --json (spec op ii) | 0 | `artifacts/feature-evidence-validation.json` |
| generate-story-index.py (spec op) | 0 | No diff |
| kg validate --check-symbols / --check-drift (spec ops) | 0 / 0 | `kg-check-symbols.txt`, `kg-check-drift.txt` |
| validate_templates.py (spec op) | 0 | `validate-templates.txt` |
| validate-stories.py | 0 | `validate-stories.txt` |
| kg validate --check-reproducible / --check-orphans; dead-code --safe-only | 0 / 0 / 0 | `kg-check-reproducible.txt`, `kg-check-orphans.txt`, `kg-dead-code-safe-only.txt` |
| run-lifecycle-gates.py (product) | 0 (3 of 3 PASS) | `product-lifecycle-gates.txt` |
| validate_plan_readiness.py (project) | 0 (pass, no findings) | `plan-readiness-project.json` |
| validate_semantic_examples.py | 0 | `semantic-examples.txt` |
| pytest scripts/validation/tests | 0 (31 passed) | `validation-pytest.txt` |
| lint-vague-language.py over added markdown lines | 0 (no findings) | `vague-language-added-lines.txt` |

No validator returned exit code 2.

## Errors / Warnings / Info

Feature evidence: 1 feature validated, with 0 errors, 0 warnings, and 0 info. Trackers: 0 errors and 0 warnings. Stories: 0 failures and 10 pre-existing warnings. Knowledge graph: 0 errors.

## KG Drift Status

No drift. Projections and tracker regions equal compile(source). Coverage is 4 mapped, 62 excluded, 0 uncovered.

## Template Alignment

PASS.

## Findings (cross-referenced to §22 rule IDs)

No §22 rule fired. I-1 (cwd label normalization in appended log entries) still applies. I-2 does not recur: this run did not use `exec-and-log.py`, so no artifact was superseded.

## Result

**PASS.**
