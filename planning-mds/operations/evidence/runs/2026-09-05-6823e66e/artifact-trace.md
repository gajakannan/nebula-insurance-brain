# Artifact Trace — Init Run 2026-09-05-6823e66e

> Base run (§8). Everything under `{PRODUCT_ROOT}` listed as created or updated was written by this run or by the operator during the adoption steps that fed it; nothing in `nebula-agents` was modified.

## Artifacts Read

### Framework (context load order)
- `agents/agent-map.yaml`, `agents/docs/AGENT-USE.md`, `agents/actions/init.md`, `agents/actions/spec/init.yaml`, `agents/actions/spec/_contract.yaml`
- `agents/templates/prompts/evidence-contract/init-operator-friendly.md` (generated operator prompt for this policy version)
- `agents/product-manager/SKILL.md` (initialization mode), `agents/templates/*` (lifecycle, contributing, ci-gates, tracker-governance, solution-patterns, base-run templates)
- `agents/scripts/scaffold-map.yaml`, `scaffold-product.py`, `run-gate.py`, `gate_runtime.py`, `run-lifecycle-gates.py`, `append-command-log.py`
- `agents/product-manager/scripts/validate-trackers.py`, `validate-feature-evidence.py` (registry and path-class expectations)
- `CONSUMER-CONTRACT.md` §2, §6, §7

### Product (pre-existing)
- `planning-mds/BLUEPRINT.md` (Sections 0 to 6), `planning-mds/architecture/master-blueprint.md` sections 3, 65, 66, 75, 77, 78, 86, 95, 115
- `scripts/kg/tracker_gen.py`, `compile.py`, `validate.py`, `symbols.py` (behavior on an empty graph)

### Reference consumer (shapes only)
- `../nebula-insurance-crm/planning-mds/features/REGISTRY.md`, `ROADMAP.md`, `planning-mds/operations/evidence/README.md`, `planning-mds/domain/glossary.md`, `.github/workflows/kg-reproducibility.yml`, and one base-run package under `operations/evidence/runs/`

## Artifacts Created Or Updated

- `lifecycle-stage.yaml` — scaffolded from template, then rewritten to product-local gates (see gate-decisions post-init note)
- `CONTRIBUTING.md` — scaffolded
- `.github/workflows/ci-gates.yml` — scaffolded, then rewritten (product gates job + framework validators job); `.github/workflows/kg-reproducibility.yml` — created
- `scripts/run-lifecycle-gates.py` — created (product-local gate runner)
- `planning-mds/architecture/SOLUTION-PATTERNS.md` — scaffolded from template (to be filled in Phase B)
- `planning-mds/features/TRACKER-GOVERNANCE.md` — scaffolded
- `planning-mds/features/REGISTRY.md`, `ROADMAP.md` — created with generated regions; regions rendered by compile.py
- `planning-mds/features/STORY-INDEX.md` — generated (0 stories)
- `planning-mds/operations/evidence/README.md` — created (profiles, effective date, Path Class Extensions, lanes, runs table)
- `planning-mds/knowledge-graph/{canonical-nodes,feature-mappings,code-index,solution-ontology,symbol-index,decisions-index,coverage-report}.yaml` — generated
- `planning-mds/domain/glossary.md` — authored skeleton
- `planning-mds/examples/{features,personas,stories}/.gitkeep`, `planning-mds/features/archive/.gitkeep` — created
- `scripts/kg/tracker_gen.py` — patched (empty feature set)
- this run folder (six base files, `gate-state.json`, `artifacts/`)

## Generated Evidence

- `artifacts/i6-validate-trackers.txt`, `artifacts/i6-validate-feature-evidence.json`, `artifacts/i6-kg-check-symbols.txt`, `artifacts/i6-kg-check-drift.txt`, `artifacts/i6-validate-templates.txt` — captured I6 validator outputs (re-run after the gate, identical inputs)
- `artifacts/post-init-product-lifecycle-gates.txt` — `scripts/run-lifecycle-gates.py` for stage framework-bootstrap (PASS, 2 gates)

## External Or Global Evidence References

None. No global lanes exist yet.

## Omissions And Waivers

- No `evidence-manifest.json`: base-run-only scope; init does not create a feature evidence package.
- No personas, feature folders, or kg-source feature shards: out of init scope by contract; the seeding step and the plan action own them.
- `agents/ROUTER.md` was not loaded: no role reference corpus was needed for a scaffold-only run.
