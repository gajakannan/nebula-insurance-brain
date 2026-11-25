# Post-Closeout Corrections — F0011 run 2026-11-22-885e8734

Date: 2026-11-24. Author: Claude Opus 5.5, acting for the original lifecycle owners (PM, feature orchestrator, QE). Trigger: feature-review run `2026-11-24-96b7f791` (verdict TRULY DONE; 0C/0H/2M/1L). These corrections change no verdict, gate result, signoff or AC disposition. No code, test, requirement text or acceptance criterion changed.

`pm-closeout.md`, `signoff-ledger.md` and `kg-reconciliation.md` are hash-attested at the G8 `archive-move` checkpoint, so they stay byte-identical. None of them needed correcting. The other files were corrected in place, and each change is listed below.

## FR-PM-M1 — conflicting status prose in the archived feature

- **What was wrong:** after closeout, several archived feature documents still described the feature as unstarted or in progress, while `STATUS.md`, the signoff ledger and raw test evidence record it as Done.
- **Corrected current-status statements** under `planning-mds/features/archive/F0011-json-schema-contract-system/`:
  - `README.md`: roadmap line, planning line, overview evidence paragraph, approval-state paragraph and the story table (In Progress → Done).
  - `PRD.md`: status header, Related Stories table and total line (Not Started → Done).
  - `acceptance-criteria-checklist.md`: story state table (Not Started → Done) and the total line (0 → all 41 implemented and verified).
  - `GETTING-STARTED.md`: "Current implementation state" now says Done, and review, approval, signoff and closeout are complete.
  - All six story files: the context line (implementation "in progress") and the Review Provenance line (signoff "pending").
- **Labelled, not rewritten:** in the approved planning baselines (`feature-assembly-plan.md` status header and Exit and Approval State, `contract-design.md` status header), "Not Started" is now marked as the state at approval, with a pointer to `STATUS.md`.
- The review cited the checklist, PRD, S0001 and README. GETTING-STARTED, the README story table, the other five story files and the two plan documents had the same drift and were fixed in the same pass.

## FR-PM-M2 — changed-path inventory not finalized

- **What was wrong:** `evidence-manifest.json` `changed_paths` and its `scm.diff_artifact` (`artifacts/diffs/changed-files.txt`) held the same 426 paths from the G2-era working tree. The merged PR #64 range (`eac6b5a..a125d2c`, squash-merged as `15648cb`) contains 586 paths with rename detection off. Among the omitted paths was a real change, `engine/tests/integration/test_temporal_migration.py` (CI repair commit `bc0ab11`). Conversely, 91 listed paths were never committed.
- **Correction:**
  - New receipt `artifacts/diffs/changed-files-final.txt`: the exact 586-path `git diff --name-only --no-renames` of the PR range, with the range in its header.
  - `evidence-manifest.json`: `changed_paths` now equals those 586 committed paths, and `scm.diff_artifact` points to the new receipt.
  - The 91 removed entries are listed in `artifacts/diffs/changed-paths-uncommitted-evidence.txt`. All of them exist locally and are git-ignored (coverage binaries, source snapshots, superseded captures), so they were never delivered changes.
- `artifacts/diffs/changed-files.txt` is kept unchanged as the G2-era receipt, because `code-review-report.md` and `artifact-trace.md` cite it as that snapshot.
- `scm.base_ref` stays `bf78e111…`. Its tree is byte-identical to the PR base `eac6b5a…` (review `artifacts/pa-base-path-delta.txt`), so this is squash history, not drift.

## QE-L1 — stale coverage figure in the final test summary

- **What was wrong:** the post-G4 summary paragraph of `test-execution-report.md` said Python changed-statement coverage was 86.0%. Raw `artifacts/coverage/changed-line-coverage.json` records 1166/1350 = 86.37%, and `coverage-report.md` reports 86.4%.
- **Corrected in place:** that paragraph now says 86.4% (1166/1350).
- **Left as recorded:** `g2-self-review.md` ("Final G2 Refresh") and `feature-action-execution.md` (2026-11-23T20:10 entry) also say 86.0%. Both describe the pre-G4 measurement (`commands.log` 20:37). The post-G4 re-measurement (21:35) overwrote that output, so 86.0% can be neither confirmed nor refuted, and those historical rows are not rewritten. The G2 re-run row in `gate-decisions.md` already says 86.4%.

## Run README

`README.md` was a G0-era snapshot that still says G2–G8 are pending. A pointer to the final state and this note was added at the top, and the historical body was left as written.

## Validation

After these edits: `validate-feature-evidence.py --stage closeout` for F0011, `validate-trackers.py`, KG `validate.py` (`--check-symbols`, `--check-drift`) and the story-index currency check all pass. Output: `artifacts/test-results/post-closeout-validation.txt`.
