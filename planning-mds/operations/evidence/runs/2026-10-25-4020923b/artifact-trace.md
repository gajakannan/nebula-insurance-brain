# Artifact Trace — F####-{slug} run {run-id}

> Required per §8. Captures what was read, written, generated, referenced externally, and explicitly omitted/waived.

## Artifacts Read

Bulleted list of files the action consulted (planning docs, prior evidence, role inputs).

- `planning-mds/BLUEPRINT.md` and `docs/agent-instructions.md` (loaded through project_context)
- `.agentignore`
- `planning-mds/features/F0005-one-time-docling-ingestion/PRD.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/F0005-S0001-pin-and-process-source-documents.md` through `F0005-S0005-qualify-text-origin-and-enable-v2-publication.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/feature-assembly-plan.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/STATUS.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/README.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/acceptance-criteria-checklist.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/compatibility-evidence.md`
- `planning-mds/features/F0005-one-time-docling-ingestion/GETTING-STARTED.md`
- F0005 tier 1 KG lookup; its mappings were treated as routing context only
- Framework action, evidence-contract and architect-role guidance in `nebula-agents/agents/**`
- Framework DevOps role guidance and the F0005 section of `docker/local-inference-runbook.md`
- No prior `latest-run.json` was recorded (`run_id_prior: null`); no prior run evidence was consumed.

## Artifacts Created Or Updated

- `evidence-manifest.json` — initialized with contract version 2026-07-11; G0 scope booleans and role requirements set
- `artifacts/diffs/changed-files.txt` — initial durable product diff list; refresh after implementation changes
- `g1-runtime-preflight.md` — DevOps runtime availability results; unable to restore required host services
- `README.md`, `action-context.md`, `artifact-trace.md`, `gate-decisions.md` — initialized for this run
- `commands.log` — initialized and populated with setup and discovery commands
- `planning-mds/features/F0005-one-time-docling-ingestion/STATUS.md` — required role matrix and live story progress matrix initialized
- `g0-assembly-plan-validation.md` — G0 architect validation

## Generated Evidence

No runtime-generated artifacts or tests. G0 and G1 reports are at the run root; later runtime outputs would be cited under `artifacts/`.

## External Or Global Evidence References

References to global lanes (§20) or to other features' evidence that this run depends on. Each reference must resolve when validated.

- None at G0.

## Omissions And Waivers

No omissions or waivers at G0. Mirror any later manifest entries here; required evidence cannot be waived.

## Run Environment (conditional)

Not applicable: command log cwd values use the stable `product` and `nebula-agents` labels.
