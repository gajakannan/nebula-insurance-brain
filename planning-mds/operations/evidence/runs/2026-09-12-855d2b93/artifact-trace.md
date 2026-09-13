# Artifact Trace — F0001-repository-and-engineering-foundation run 2026-09-12-855d2b93

Required per §8. Captures what was read, written, generated, referenced externally, and explicitly omitted/waived.

## Artifacts Read

Bulleted list of files the action consulted (planning docs, prior evidence, role inputs).

- `planning-mds/features/archive/F0001-repository-and-engineering-foundation/PRD.md`
- `planning-mds/features/archive/F0001-repository-and-engineering-foundation/STATUS.md`
- `planning-mds/features/archive/F0001-repository-and-engineering-foundation/feature-assembly-plan.md`
- `planning-mds/BLUEPRINT.md`, `features/REGISTRY.md`, `features/ROADMAP.md`, `features/STORY-INDEX.md`
- prior run `2026-09-08-b5af1e54/evidence-manifest.json` and cited role reports
- Security and QE role instructions in `agents/actions/feature.md` and role SKILLs

## Artifacts Created Or Updated

- `evidence-manifest.json`, `README.md`, `action-context.md`, `gate-decisions.md`,
  `lifecycle-gates.log`, and `commands.log` — remediation run package
- `engine/apps/api/src/brain_api/deps.py` — structured credential-failure event
- `engine/tests/security/conftest.py` and `test_credential_verification.py` — bounded
  runtime preflight and logging/non-disclosure tests
- archived feature README, PRD, STATUS, seven story DoD sections, and `BLUEPRINT.md`
  — status reconciliation

## Generated Evidence

- `artifacts/security/*` — prior approved run's raw dependency, secret, SAST, and DAST
  outputs reused as the unchanged baseline; the changed security boundary is covered by
  the remediation tests in the run reports.
- `artifacts/diffs/changed-files.txt` — remediation changed-file lock.

## External Or Global Evidence References

References to global lanes (§20) or to other features' evidence that this run depends on. Each reference must resolve when validated.

- `planning-mds/operations/evidence/runs/2026-09-08-b5af1e54/` — prior approved evidence
  baseline, explicitly cited for unchanged proof and scan artifacts.

## Omissions And Waivers

No required artifact is omitted. The five live HTTP security cases are runtime-skipped
only because the managed sandbox cannot reach the published Postgres port; this is
recorded in the QE report and is not a feature waiver.

## Run Environment (conditional)

Required only when `commands.log` carries an absolute `cwd`. One bullet per justified absolute path:

- Absolute cwd: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/engine` —
  application runtime workspace.
