# Artifact Trace — validate run 2026-09-25-463eecdd

## Artifacts Read

- Everything read by run `2026-09-25-9aa87cdf` (see its `artifact-trace.md`), re-read at head `d897b46`.
- The fix delta `b1f4357..d897b46`: ADR-0065, ADR-0066, and ADR-0067; `knowledge-graph/coverage-report.yaml`; and the prior run's evidence folder.

## Artifacts Created Or Updated

All files are in this run folder only: the six base run files, `gate-state.json`, and the three lane reports.

## Generated Evidence

- `artifacts/feature-evidence-validation.json`
- `artifacts/test-results/*`
- `artifacts/diffs/changed-files.txt` (`git diff --name-status main...HEAD`, 105 paths, including the prior run's evidence folder)
- `artifacts/diffs/added-markdown-lines.md` (the lint input; excludes generated knowledge-graph files and evidence runs)

## External Or Global Evidence References

- Prior run: `planning-mds/operations/evidence/runs/2026-09-25-9aa87cdf/` (V3 approved with follow-ups)
- Framework: `nebula-agents` @ `c218bf1`

## Omissions And Waivers

- No `evidence-manifest.json` and no `init-run.py`, for the same reasons as the prior run (A-8).
- The V3 journal attestation is blocked by A-9. `gate-decisions.md` is the authoritative V3 record.
