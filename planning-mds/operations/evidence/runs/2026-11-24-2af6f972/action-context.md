# Action Context

> Seeded by init-run.py. Fill the judgment sections before the first gate.

## Run Identity

- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **action:** plan-review
- **contract_effective_date:** 2026-07-11
- **contract_version:** 2026-07-11
- **feature_id:** F0009
- **feature_index_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/features/F0009-provenance-and-human-correction-lineage
- **feature_slug:** provenance-and-human-correction-lineage
- **mode:** clean
- **product_root:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain
- **run_folder:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-24-2af6f972
- **run_id:** 2026-11-24-2af6f972

## Inputs

- **PLAN_SCOPE:** feature (selected by the operator 2026-11-24)
- **TARGET:** F0009 (selected by the operator 2026-11-24)
- **DIFF_RANGE:** not supplied. The F0009 plan package is uncommitted in the product working tree (HEAD `2613b0b`, branch `fix/F0011-feature-review-findings`); the review reads the working tree as it stands.
- **NEBULA_PRODUCT_ROOT:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain (source: environment; normalized by `_product_root.py`, passed as `--product-root` explicitly to every script)
- **FEATURE_SLUG:** provenance-and-human-correction-lineage (REGISTRY.md line 33)
- **FEATURE_PATH:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/features/F0009-provenance-and-human-correction-lineage
- **PLAN_REVIEW_RUN_FOLDER:** /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain/planning-mds/operations/evidence/runs/2026-11-24-2af6f972
- **Reviewed plan run:** 2026-11-24-bfdbbf04 (action plan, PHASE=A+B, manifest status `approved`)

## Assumptions

- lookup.py (`scripts/kg/lookup.py F0009 --fields ids`) returned one unambiguous match, `feature:F0009` at `planning-mds/features/F0009-provenance-and-human-correction-lineage`. It is first-pass routing only; readiness judgments come from the raw artifacts.
- This is a fresh session, separate from the one that produced plan run 2026-11-24-bfdbbf04 (reviewer independence contract).
- Runtime paths the plan names as future deliverables (engine/neuron modules, migration files, proof harnesses) may be absent. Their absence is not a finding unless the plan claims they already exist.

## Scope Boundaries

- In scope: every file under FEATURE_PATH; ADR-0080 plus the ADRs F0009 is governed by (0010, 0037, 0044, 0058, 0062, 0075, 0077, 0078, 0079); `planning-mds/kg-source/features/F0009.yaml` and the generated KG projections; the uncommitted planning edits to BLUEPRINT.md, ROADMAP.md, STORY-INDEX.md, data-model.md, glossary.md, examples/README.md, architecture/feature-assembly-plan.md; the API, schema, and authorization artifacts F0009 binds; shipped code in dependency features (F0002/F0004/F0006/F0007/F0008/F0011) only where the plan makes claims about it.
- Out of scope: repairing any artifact (read-only review); other features' readiness, except to record discovered impact; feature evidence packages.
- Writes are limited to this run folder.

## Lifecycle Stage

- plan-review run initialized
