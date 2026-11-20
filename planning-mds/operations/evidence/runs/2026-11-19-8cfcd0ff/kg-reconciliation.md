# Knowledge-Graph Reconciliation — F0008-bitemporal-canonical-facts run 2026-11-19-8cfcd0ff

- Role: Architect
- Reviewer: Claude (Opus 5.5) / Architect
- Date: 2026-11-19
- Result: PASS

## Scope

This pass reconciles the second-remediation change set. The bindings cover code paths only, and no generated file was hand-edited.

## Binding Delta

| Node | Delta | Shard |
|---|---|---|
| `capability:temporal-fact-resolution` | adds test `engine/apps/api/tests/test_facts_temporal_helpers.py` | `bindings/f0008-planning.yaml` |

The changed production files (`routes/facts.py`, `repositories.py`, `commit.py`) and the integration and unit test files are already bound.

## Canonical Nodes

No new node. `adr:0078` is affirmed and stays Proposed; its D4 text now covers the commit response.

## Validator Results

| Command | Exit |
|---|---|
| `scripts/kg/compile.py` | 0 |
| `scripts/kg/validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | 0 |
| `scripts/kg/validate.py --check-drift` | 0 |

`--write-coverage-report` is deferred to G8.

## Handoff to Closeout

The PM verifies this graph at G8 and does not re-author it.
