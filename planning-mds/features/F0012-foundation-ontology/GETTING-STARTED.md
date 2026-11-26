# F0012 — Getting Started

Phase B design guide. No F0012 runtime implementation exists yet.

## Planning resume

Canonical `NEBULA_PRODUCT_ROOT`: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (environment selection normalized at setup).
Run `2026-11-25-120320e9`, action plan, phase A+B, feature mode new. Keep this run ID across sessions.

From `/home/gajap/uSandbox/repos/nebula/nebula-agents`:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-25-120320e9
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action plan
```

Read the [PRD](PRD.md), [STATUS](STATUS.md), the seven stories, the [assembly plan](feature-assembly-plan.md), proposed [ADR-0081](../../architecture/decisions/ADR-0081-foundation-ontology-authoring-and-release-runtime.md), the [foundation module design](foundation-module-design.yaml), [migration design](migration-design.sql), [contract inventory](contract-inventory.yaml) and the run's [gate decisions](../../operations/evidence/runs/2026-11-25-120320e9/gate-decisions.md). Run the independent plan-review action before implementation.

## Carry-ins and gotchas

- The predicate key grammar and `_RELEASE_REF` grammar are ADR-0077 D2 as shipped; `ontrel:sha256-<64 hex>` fits the 128-character limit.
- `brain_temporal.commit` hard-codes `TemporalKind.STATE` today; the D10 CHECK `ck_cfv_v1_kind_shape` already accepts EVENT/ETERNAL shapes, so no DDL is needed.
- The registry port is synchronous; call `prepare(scope, release_refs)` in the same unit of work before resolving any non-`sys` key.
- Casbin `policy_rule` KG nodes and `policy.csv` rows must land together, or the KG drift check fails.
- KG wildcard bindings resolve only git-tracked files; bind new `ontology/**` and `brain-ontology` files with literal paths until committed.
- `coverage-report.yaml` source sets count only tracked files: `git add` new planning files, then rerun `validate.py --write-coverage-report`.
- Never run GPU-using tests during live lanes (not expected here: no parse or model call).

## Runtime setup / verification

Use the existing integration PostgreSQL 18 fixture and the engine `.venv`. Install the `semantic-rdf` extra (`uv pip install --python engine/.venv/bin/python -e '.[semantic-rdf]'` or the repo's documented command) so `semantic_rdf` runs with `--require`. Proposed commands (validated at feature G1):

```bash
python -m brain_ontology.cli validate ontology/modules/foundation/module.yaml
python -m brain_ontology.cli compile ontology/releases/foundation/1/release.yaml --check
python -m brain_ontology.cli install --release ontology/releases/foundation/1 --tenant <id> --kb <id> --token-file <path>
python -m brain_ontology.cli report --candidate <ontrel:sha256-…> --tenant <id> --kb <id> --token-file <path>
python -m brain_ontology.cli review --report <id> --decision approve --rationale "…" --token-file <path>
python -m brain_ontology.cli activate --release <ontrel:…> --review <id> --token-file <path>
python -m brain_ontology.cli history --tenant <id> --kb <id> --token-file <path>
```

## Migration and concurrency gotchas

- Proposed 0017 follows the current 0016 head; rebase at G0 if F0010/F0021 land a migration first.
- Install serializes per tenant/KB with a transaction advisory lock; selection appends lock the current head row.
- Downgrade refuses once any `ontology_release` row exists; forward-repair instead.
