# Working in Nebula Insurance Brain

Read `planning-mds/BLUEPRINT.md` for process, scope, technology, and phase status. Architectural intent comes from `planning-mds/architecture/master-blueprint.md` and its governing ADRs. Feature-specific accepted requirements live in their feature folders. Report conflicts between these sources; do not invent product rules.

## Repository boundaries

- Keep product requirements, insurance terminology, review criteria, and validation scripts here. Generic framework mechanisms belong in the sibling `nebula-agents` repository.
- Framework sessions start in that sibling repository. Always pass this repository's absolute path as `--product-root`, or set `NEBULA_PRODUCT_ROOT` explicitly. Do not rely on a default product or the shell's current directory.
- `BOUNDARY-POLICY.md` in the framework describes the separation of framework and product content. It is not an insurance regulatory policy.
- Runtime directories and proof harnesses named in a plan may not exist yet. Distinguish a proposed implementation path from a required existing planning artifact.

## Planning and knowledge graph

- Keep the blueprint, feature status, and trackers aligned under `planning-mds/features/TRACKER-GOVERNANCE.md`.
- Edit `planning-mds/kg-source/**` as the authored graph source. Generate projections and tracker tables with `scripts/kg/compile.py`; do not hand-edit generated regions.
- Use KG lookup for routing. Inspect the source planning artifacts before making readiness judgments.
- Honor `.agentignore` for broad searches. Read exact evidence references when a review requires them.
- Proposed ADRs stay proposed until their stated proof and acceptance conditions are met. Structural readiness checks do not settle them.

## Local validation

From this repository, run:

```bash
python3 scripts/validation/validate_plan_readiness.py --plan-scope feature --target F0001
python3 scripts/validation/validate_plan_readiness.py --plan-scope project --target project
python3 scripts/run-lifecycle-gates.py
```

The readiness validator emits JSON and exits 0 for a structurally valid plan, 1 for failed checks, and 2 for invalid invocation. Architectural adequacy remains a reviewer decision. During `plan-review`, also read `docs/plan-review-checklist.md` and cite actual planning evidence for findings.
