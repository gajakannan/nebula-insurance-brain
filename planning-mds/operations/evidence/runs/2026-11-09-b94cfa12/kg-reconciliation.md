# Knowledge-Graph Reconciliation — F0007-factslot-model run 2026-11-09-b94cfa12

- Role: Architect (role switch; `agents/architect/SKILL.md` read)
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-09

## Scope

This reconciliation binds the as-built F0007 source into the semantic graph and compares it with the G0 Knowledge-Graph Binding Plan in `feature-assembly-plan.md`.

- Authored shards: `planning-mds/kg-source/bindings/f0007-planning.yaml` and `planning-mds/kg-source/nodes/**`. Generated YAML is never hand-edited.
- Binding style: new files are bound by literal path, because wildcard bindings resolve only against git-tracked files and these files are not committed yet. Every binding id lives in its owning F0007 shard, so no id is duplicated.
- Coverage: `coverage-report.yaml` was **not** regenerated at G7. That happens at G8, after the archive move.

## Binding Delta

| Capability / node | code-index binding | G0-declared? | Action |
|-------------------|--------------------|--------------|--------|
| capability:factslot-identity-resolution | `brain_domain/fact_slots.py`; `brain-factslots/` `pyproject.toml`, `__init__`, `ports`, `predicates`, `resolution`, `names`, `service`; `brain_persistence/fact_slots.py`; `brain_testing/factslots.py`; tests (unit, harness, resolution, names, ownership) | yes (domain and `brain_factslots/**`) | updated (backend and tests added to the existing planning binding) |
| capability:typed-fact-answer | `brain_domain/fact_values.py`, `fact_answers.py`, `data/iso4217-2026-01.txt`; `brain_factslots/answers.py`; domain and answers tests | yes | updated |
| entity:fact-slot-qualifier | `brain_persistence/fact_slot_models.py` | yes (persistence) | updated |
| migration:f0007-factslot-identity (new node) | `engine/migrations/versions/0012_f0007_factslot_identity.py`; migration test; pilot seed and snapshot | yes (persistence row names 0012) | added (node and binding) |
| capability:bitemporal-canonical-commit | `engine/packages/brain-temporal/src/**` (existing glob) covers `commit.py` | yes ("existing globs") | confirmed existing coverage |
| capability:durable-authorization-decisions | existing binding covers `brain_api/routes/facts.py` | yes | confirmed existing coverage |
| capability:runtime-roots-and-toolchain | existing binding covers `errors.py`, `deps.py`, `engine/pyproject.toml` | — | confirmed existing coverage |
| capability:backup-and-restore | `scripts/ops/**` (existing glob) covers `verify_content.py` | — (carry-in repair) | confirmed existing coverage |

All five new-file checks resolve through `hint.py` to the expected node (`artifacts/test-results/g7-binding-coverage.txt`).

## Canonical Nodes

- **New:** `migration:f0007-factslot-identity` (`nodes/migrations/f0007-factslot-identity.yaml`).
- **Affirmed and refreshed** (notes moved from "Planned" to implemented in this run; ADR-0077 rationale now records the evidenced proof gates with formal acceptance pending):
  - `capability:factslot-identity-resolution`
  - `capability:typed-fact-answer`
  - `entity:fact-slot`
  - `entity:fact-slot-qualifier`
  - the ADR-0077 rationale on the F0007 schema and endpoint nodes
- **No new `WHY` or ADR node.** ADR-0077 status stays Proposed.
- **Planned semantic nodes from G0:** all present. That covers both capabilities, both entities, the three schema nodes and `adr:0077`, plus the migration node above.

## Validator Results

| Check | Command | Result |
|-------|---------|--------|
| compile | `scripts/kg/compile.py` | PASS (exit 0). Six binding-overlap warnings, all pre-existing shared planning documents. |
| symbol and decision regen + check | `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | PASS (exit 0). `symbol-index.yaml`: 324 symbols added, 0 removed, mostly F0007; 19 come from the already-tracked `neuron/.../test_conversion_limits.py`, which earlier PRs never indexed. |
| drift | `validate.py --check-drift` | PASS (exit 0) |

Executed through `run-gate.py --stage G7`; see `gate-state.json` and `commands.log`.

## G7 Delta Before the Archive Move

Before G8, the Architect removed three literal feature-folder document paths from `bindings/f0007-planning.yaml`: the assembly plan, `worked-examples.md` and `contract-examples.json`, all under `planning-mds/features/F0007-factslot-model/`. They were plan-time bindings that would break when the folder moves to `features/archive/`. The feature shard's `path:` already covers feature documents, which is how F0006 is bound. ADR, schema, data-model and code bindings are unchanged. G7 was re-run with `--force`, and compile, symbols, decisions and drift all exit 0.

## Handoff to Closeout

The PM verifies this graph at G8 and does not re-author shards. After the archive move and the feature-shard `path:`/`status:` edit, G8 runs compile, `--write-coverage-report`, `--check-drift` and the plain `validate.py`. Logical `F0007/` doc refs resolve through the shard `path:`, so the move needs no repointing.

## Result

PASS
