# Knowledge-Graph Reconciliation — F0003-postgresql-persistence run 2026-10-03-57d14a51

## Architect Review

The path hint for `engine/tests/integration/test_persistence_contract.py` returned an empty scope with low confidence. I opened the raw F0003 assembly plan, test source, feature graph shard, existing binding examples, and PostgreSQL persistence capability node before making a graph change.

The test directly inserts overlapping valid and recorded ranges through SQLAlchemy and verifies PostgreSQL rejects the transaction with exclusion SQLSTATE `23P01`, with no failed commit row left behind. The approved plan assigns this database integrity boundary to F0003-S0003 and the `postgresql-persistence-contract` capability.

## Binding Delta

- Added `planning-mds/kg-source/bindings/f0003.yaml`, binding the stable code path `engine/tests/integration/test_persistence_contract.py` to `capability:postgresql-persistence-contract` under the backend code index.
- Kept F0003 lifecycle state and feature mappings unchanged for G8 PM tracker reconciliation. The binding contains only a code path, so it remains valid after the feature folder is archived.

## Canonical Nodes

- Updated `planning-mds/kg-source/nodes/capabilities/postgresql-persistence-contract.yaml` with a source-evidence note describing the test's database-level rejection and rollback assertion. Capability semantics, contracts, and relationships were not changed.

## Validator Results

- `python3 scripts/kg/compile.py` completed successfully and regenerated the graph projections and tracker regions from `kg-source/**`.
- `python3 scripts/kg/validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` passed. It reported 489 symbols and zero decision markers; warnings list the existing unused `validated_by` and `supersedes` edge types.
- `python3 scripts/kg/validate.py --check-drift` passed with no drift. The validator also reports the existing unused-edge warnings.
- The compiler emitted name-similarity warnings for existing canonical-commit/guideline states and review-decision schema/entity names; integrity validation passed.
- `--write-coverage-report` was not run. Coverage report generation remains deferred until after the G8 archive move because the evidence paths are path-sensitive.

## Generated Projections

The compiler regenerated `planning-mds/knowledge-graph/canonical-nodes.yaml`, `feature-mappings.yaml`, `code-index.yaml`, `solution-ontology.yaml`, symbol and decisions indexes, and the generated tracker regions in `REGISTRY.md` and `ROADMAP.md`. No projection YAML was hand-edited.

## Handoff to Closeout

PASS. The as-built test source is bound to the approved F0003 persistence capability, generated projections validate, and drift checks pass. The evidence manifest remains `in-progress`; PM closeout and archival remain for G8.
