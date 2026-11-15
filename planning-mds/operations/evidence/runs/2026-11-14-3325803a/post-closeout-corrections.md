# Post-Closeout Corrections — F0064 run 2026-11-14-3325803a

Date: 2026-11-14. Author: Claude Opus 5.5, acting for the original lifecycle owners (PM, QE). Trigger: feature-review run `2026-11-14-7cba50ff` (verdict TRULY DONE; 4 Low findings). These corrections change no verdict, gate result or AC disposition.

`pm-closeout.md`, `signoff-ledger.md` and `kg-reconciliation.md` are hash-attested at the G8 `archive-move` checkpoint, so they stay byte-identical. Where they are wrong, this note is the correction. Non-attested reports were corrected in place, with each change listed below.

## PM-02 — final closeout CI provenance

- **What was wrong:** `pm-closeout.md` (Validator Results) says CI on the closeout commit is re-checked on PR #49. PR #49 (head `db723d5`, merged as `45117ba`) was squash-merged mid-run, so the closeout commit landed in **PR #50** instead (head `abe5045f785bf4aea4c6dfa09783cc145d2cf1b7`, merged as `6acd80560c0bc486bf9a7b28041631f907c2e901`).
- **Correction:** S0004 AC4 is satisfied at both heads. PR #49: `artifacts/test-results/s0004-ac4-ci-checks-run1.txt` and `s0004-ac4-ci-framework-validators.txt`. PR #50: `artifacts/test-results/s0004-ac4-ci-checks-pr50.txt`, where all 7 checks pass (CI Gates run 43652089357 and KG reproducibility run 43652089362). The review run's `artifacts/ci-pr50-jobs.json` records framework-validators job 132622580186, with project-extension steps 8–11 succeeding.
- **Also corrected:** the feature shard `kg-source/features/F0064.yaml` (closing note, `completion_state`) now names both PRs.

## QE-L1 — coverage label

- **What was wrong:** "88% branch coverage" was coverage.py's combined statement-and-branch `Cover` figure. From `artifacts/coverage/combined-coverage.json` the actual values are 115/127 statements (90.55%), 52/62 branches (**83.87%**) and 88.36% combined. All three exceed the 80% floor, so the G2 result is unchanged.
- **Corrected in place:** `coverage-report.md`, `code-review-report.md`, `g2-self-review.md`, `artifact-trace.md`, `feature-action-execution.md`, and the archived feature `STATUS.md` closeout summary. The historical G2 row in `gate-decisions.md` is left as recorded; its corrigendum is appended below that table.

## QE-L2 — failed-attempt gate diagnostics

- **What was lost:** the first G0 (twice), G1 and G5 `run-gate.py` attempts wrote to `artifacts/gates/g0.txt`, `g1.txt` and `g5.txt`. The passing rerun overwrote each file, so the failed attempts' driver output is gone. This cannot be recovered and is not reconstructed here.
- **What survives:** exit codes in `lifecycle-gates.log` and `commands.log`. The validator diagnoses were also captured by direct `validate-feature-evidence.py` reruns in this session, and are summarized in `README.md` (Validation Summary) and `feature-action-execution.md`: missing diff artifact; run-folder paths in the diff; missing G1 decision row; STATUS heading `Required Role Matrix`; unchanged-path mention in `code-review-report.md`. Those summaries are narrative, not preserved raw output.
- **Process fix:** later runs write each gate attempt to a distinct, attempt-numbered output file (as G8 already did: `g8-1.txt`, `g8-2.txt`, `g8-3.txt`).

## Stale G7/G8 rows in the G6 timeline

`feature-action-execution.md` was a G6 snapshot, and its G7/G8 rows still read "— (next)". They now record the actual outcomes, with pointers to `kg-reconciliation.md` and `pm-closeout.md`. This was not one of the review's findings; it was noticed while checking the review.

## Validation

After these edits: `validate-feature-evidence.py --stage closeout`, scoped `validate-trackers.py`, plain `validate.py` (after the coverage refresh), `--check-drift`, and `validate_plan_readiness.py --plan-scope feature --target F0064` all pass. Outputs: `artifacts/test-results/post-closeout-validation.txt`.
