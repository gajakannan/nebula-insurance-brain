# Knowledge-Graph Reconciliation — F0008-bitemporal-canonical-facts run 2026-11-17-1a4ae2f0

- Role: Architect
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-18
- Result: PASS

## Scope

This pass reconciles the as-built F0008 source against the G0 "Knowledge-Graph Binding Plan" in the assembly plan. Only code and test paths are bound. These stay stable across the G8 archive move, and the feature-folder documents are covered by the feature shard's `path`. No generated `knowledge-graph/*.yaml` was hand-edited; `compile.py` regenerated them.

## Binding Delta

| Node | Planned at G0 | As built (bound now) | Shard |
|---|---|---|---|
| `capability:temporal-fact-resolution` (new at Phase B) | ADR-0078, `fact-temporal-v1` schema | + `brain_temporal/reader.py`, `brain_api/routes/facts.py`, `brain_api/schemas/facts.py`; tests `test_temporal_reads.py` | `bindings/f0008-planning.yaml` |
| `capability:bitemporal-canonical-commit` | existing F0001 record | + `brain_domain/temporal.py`, `brain_temporal/bounds.py`, `attestation.py`, `commit.py`; tests `test_bounds.py`, `test_temporal_service.py`, `test_contract_examples.py`, `fixtures/temporal/harness.py`, `test_temporal_v1_commit.py`, `test_temporal_concurrency.py`. The `brain-temporal/src/**` wildcard resolves only tracked files, so new files are bound literally. Binding IDs are unique, so these paths join the existing record instead of a second one. | `bindings/f0001.yaml` |
| `entity:canonical-fact-version` | notes only | + `brain_persistence/models.py`; tests `test_temporal_immutability.py` | `bindings/f0008-planning.yaml` |
| `migration:f0008-bitemporal-contract` (new) | not predicted; G0 named migration 0014 but planned no node | `engine/migrations/versions/0014_f0008_bitemporal_contract.py`; tests `test_temporal_migration.py` | `bindings/f0008-planning.yaml`, `nodes/migrations/f0008-bitemporal-contract.yaml` |

Unplanned delta: the migration node. It follows the F0007 precedent (`migration:f0007-*`). The feature shard's `affects` now lists it.

## Canonical Nodes

- **New:** `migration:f0008-bitemporal-contract`. Its notes cover the columns, CHECKs, triggers, preflight and downgrade guard, and it states no table, role, grant, RLS or `SECURITY DEFINER`.
- **Updated as-built notes:**
  - `capability:temporal-fact-resolution` (reader and disclosure rule);
  - `capability:bitemporal-canonical-commit` (v1 and legacy paths);
  - `entity:canonical-fact-version` (migration 0014, `ending_refs`).
- **Affirmed:** `adr:0078` (stays Proposed; acceptance is an operator decision, and the proof gates are met per `architect-implementation-review.md`), `schema:fact-temporal-v1`, `endpoint:fact-commit`, `endpoint:fact-get`.
- **No new `WHY`/rationale entries.** ADR-0078 carries the rationale, plus the G0 D8 note.

## Validator Results

| Command | Exit |
|---|---|
| `python3 scripts/kg/compile.py` | 0. The first attempt failed with a duplicate binding ID `capability:bitemporal-canonical-commit`; that was fixed by merging into `bindings/f0001.yaml`. The remaining `binding-overlap` warnings are pre-existing F0006 schema paths. |
| `python3 scripts/kg/validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | 0 |
| `python3 scripts/kg/validate.py --check-drift` | 0 |

`--write-coverage-report` was not run here. It is path-sensitive and deferred to G8, after the archive move.

## Handoff to Closeout

- The PM verifies this graph at the G8 `archive-move` checkpoint and does not re-author it.
- At G8 the PM sets the feature shard status, archive path and trackers. It then runs `compile.py`, `validate.py --write-coverage-report`, `--check-drift` and the plain `validate.py` last.
- The manifest stays `in-progress`, and `gate_results.kg_reconciliation` is recorded.
