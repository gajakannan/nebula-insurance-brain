# Knowledge-Graph Reconciliation — F0012 run 2026-11-26-54387a08

Reviewer: Claude (Opus 5.5) / Architect
Date: 2026-11-26

Result: PASS

## G0 prediction vs as-built

G0 predicted that the planned capabilities `foundation-ontology-release`, `release-backed-predicate-registry` and `ontology-release-compatibility` would gain code bindings, plus migration 0017 and `ontology/**`. That held.

Two canonical additions came with the policy rows at G2: the role node `role:ontology-steward` and four `policy_rule:ontology-release-{install,read,review,activate}` nodes. The product KG validator's role-slug map (`scripts/kg/validate.py`) gained `ontology-steward`, so the Casbin drift check covers the new rows. No other new capability or canonical semantic emerged.

## Binding Delta

| Node | Shard | Paths bound (code only, stable across the archive move) |
|---|---|---|
| `capability:foundation-ontology-release` | `kg-source/bindings/f0012.yaml` | `brain-ontology` authoring, compiler, rdf_export, service, runtime, cli, errors; `brain_domain/ontology.py`; `brain_persistence/ontology_releases.py`, `ontology_models.py`; `ontology/modules/foundation/**` and `ontology/releases/foundation/1/**`; `scripts/validation/build_foundation_examples.py`; tests |
| `capability:release-backed-predicate-registry` | `bindings/f0012.yaml` | `brain_factslots/predicates.py`; `test_temporal_kind_activation.py` |
| `capability:ontology-release-compatibility` | `bindings/ontology-planning.yaml` (merged into its existing planning binding, one shard per node) | `brain_ontology/impact.py`, `semantics.py`; `test_semantics_impact.py`, `test_ontology_activation.py` |
| `migration:f0012-ontology-releases` (new node `nodes/migrations/f0012-ontology-releases.yaml`) | `bindings/f0012.yaml` | `0017_f0012_ontology_releases.py`; `test_ontology_migration.py` |

The modified shared files keep their existing bindings: `brain_temporal/commit.py` and `ranges.py` under `bitemporal-canonical-commit`, `brain_factslots/resolution.py` and `answers.py` under `factslot-identity-resolution`, and `brain_domain/authx.py` and `brain_persistence/authx.py`/`tenancy.py` under `authorization-enforcement`. Planning paths are not bound here, so the G8 archive move cannot break them.

## Canonical Nodes

Updated through `kg-source/**` only; no generated `knowledge-graph/*.yaml` was edited by hand.

- `capability:foundation-ontology-release` and `capability:release-backed-predicate-registry`: notes changed from "Phase B design, not implemented" to implemented in this run (ADR-0081 still Proposed).
- `capability:ontology-release-compatibility`: notes now say the F0012 share is implemented; ADR-0045 stays Proposed and F0030/F0062 keep the extended tooling.
- New `migration:f0012-ontology-releases`; new `role:ontology-steward` and four policy rules (added at G2 with policy.csv).

The feature shard `kg-source/features/F0012.yaml` (status, notes) is updated by the PM at the G8 archive move.

## Validator Results

| Command | Result | Artifact |
|---|---|---|
| `scripts/kg/compile.py` | wrote canonical-nodes, feature-mappings, code-index, solution-ontology and the tracker regions | [g7-compile.txt](artifacts/kg/g7-compile.txt) |
| `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | PASS; 6307 symbols, all on bound nodes | [g7-validate-symbols.txt](artifacts/kg/g7-validate-symbols.txt) |
| `validate.py --check-drift` | PASS (Casbin rows and policy nodes agree) | [g7-drift.txt](artifacts/kg/g7-drift.txt) |

The first compile attempt failed with a duplicate code-index id: `ontology-release-compatibility` was bound in two shards. The fix was to merge it into the existing shard. New files were staged (`git add`) before validation because KG patterns resolve through the git index.

## Handoff to Closeout

The PM verifies this graph at the `archive-move` checkpoint, updates the F0012 feature shard and the trackers, moves the feature folder to `features/archive/`, and runs `--write-coverage-report` only after the move.
