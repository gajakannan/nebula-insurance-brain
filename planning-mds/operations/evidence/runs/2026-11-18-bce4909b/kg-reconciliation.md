# Knowledge-Graph Reconciliation — F0008-bitemporal-canonical-facts run 2026-11-18-bce4909b

- Role: Architect
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-19
- Result: PASS

## Scope

This pass reconciles the remediation change set against the graph from the prior run's G7. The bindings cover code paths only, and no generated file was hand-edited.

## Binding Delta

| Node | Delta | Shard |
|---|---|---|
| `migration:f0008-bitemporal-contract` | adds `engine/migrations/versions/0015_f0008_split_lineage_same_slot.py`, with notes on the same-slot guard | `bindings/f0008-planning.yaml`, `nodes/migrations/f0008-bitemporal-contract.yaml` |
| `feature:F0018` | notes record the F0008 handoffs (SEC-F8-02; refusal reason codes) | `kg-source/features/F0018.yaml` |

The other remediation files are already bound: the commit service, API schemas, domain facts, and tests.

## Canonical Nodes

No new node. `adr:0078` is affirmed and stays Proposed.

## Validator Results

| Command | Exit |
|---|---|
| `scripts/kg/compile.py` | 0 |
| `scripts/kg/validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | 0 |
| `scripts/kg/validate.py --check-drift` | 0 |

`--write-coverage-report` is deferred to G8.

## Handoff to Closeout

The PM verifies this graph at G8 and does not re-author it.
