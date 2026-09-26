# Artifact Trace — validate run 2026-09-25-9aa87cdf

## Artifacts Read

- `planning-mds/BLUEPRINT.md`, `planning-mds/README.md`, `docs/agent-instructions.md` (via `project_context.py --action validate`)
- `planning-mds/features/REGISTRY.md`, `ROADMAP.md`, `STORY-INDEX.md`, `TRACKER-GOVERNANCE.md`
- `planning-mds/knowledge-graph/{solution-ontology,canonical-nodes,feature-mappings,code-index,coverage-report}.yaml`
- `planning-mds/kg-source/nodes/adrs/adrs.yaml`; `planning-mds/kg-source/features/F0066.yaml` and the 28 amended feature shards
- `planning-mds/architecture/decisions/ADR-0063` to `ADR-0069`; ADR-0008, ADR-0039, ADR-0042, ADR-0053, ADR-0060, ADR-0061 (consistency checks)
- `planning-mds/architecture/master-blueprint.md` (changed sections 3, 11, 14, 17, 29, 53, 56, 62, 64, 75, 76, 78, 95, 99; and §28, §107.4 for consistency)
- `planning-mds/architecture/data-model.md`, `planning-mds/testing/evaluation-strategy.md`, `planning-mds/domain/glossary.md`
- `planning-mds/examples/README.md`, `planning-mds/examples/statements-time-and-governance.md`, `planning-mds/examples/neurosymbolic-gl/{README.md,cases.md,records.json}`
- `planning-mds/features/F0005-one-time-docling-ingestion/F0005-S0003-reinterpret-saved-json-and-map-evidence.md`; `planning-mds/features/F0065-grounded-gl-guideline-assessment/assessment-contract.md`
- `planning-mds/schemas/interpretation-result.schema.json`
- Framework (pinned `c218bf1`): `agents/actions/validate.md`, `agents/actions/spec/validate.yaml`, `agents/actions/spec/_contract.yaml`, `agents/templates/prompts/evidence-contract/validate-operator-friendly.md`, the gate-decisions and artifact-trace templates

## Artifacts Created Or Updated

All files are in this run folder. Nothing outside it changed; `git status` shows only this folder as new.

- `README.md`, `action-context.md`, `artifact-trace.md`, `gate-decisions.md`, `commands.log`, `lifecycle-gates.log` — the six base run files
- `gate-state.json` — the `run-gate.py` journal (V0–V3)
- `pm-validation-report.md` (product-manager), `architect-validation-report.md` (architect), `implementation-validation-report.md` (product-manager, tool lane)

## Generated Evidence

- `artifacts/feature-evidence-validation.json` — captured stdout of V1 command ii
- `artifacts/test-results/*.txt|json` — captured validator outputs (see the implementation report table)
- `artifacts/diffs/changed-files.txt` — `git diff --name-status main...HEAD` (79 paths)
- `artifacts/diffs/added-markdown-lines.md` — added markdown lines (excluding generated knowledge-graph files), the input to the vague-language lint

## External Or Global Evidence References

- Subject commit: `docs/utopia-evolution` @ `b1f4357`; base `main` @ `93cc8c1`
- Framework: `gajakannan/nebula-agents` @ `c218bf1776f509a30f71967a1ee79879caa9a000` (matches `.github/workflows/ci-gates.yml`)

## Omissions And Waivers

- **No `evidence-manifest.json`.** `validate` is base-run-only and `validate.md` §8/§14 excludes the manifest profile. The generated prompt's session-setup sentence conflicts with this (architect A-8).
- **`init-run.py` not used.** It requires `--feature`, and this run has no feature. The skeleton was created as `notes.session_setup` specifies.
- **Superseded `commands.log` entries 7–19.** Their artifact files first held only the `exec-and-log.py` wrapper banner. They were replaced by the captured output of the rerun (entries 20–32). Exit codes agree.
- **No application-runtime execution.** No runtime code changed.
- **Dead-code candidates** (52, all in existing F0001 code) were not triaged. This change touches no code, and the triage belongs to the next runtime release-readiness review.
