# F0012 — Getting Started

Implementation guide. Feature run `2026-11-26-54387a08` built the runtime; the Phase B planning notes below are kept for history.

## Planning resume

Canonical `NEBULA_PRODUCT_ROOT`: `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain` (environment selection normalized at setup).
Run `2026-11-25-120320e9`, action plan, phase A+B, feature mode new. Keep this run ID across sessions.

From `/home/gajap/uSandbox/repos/nebula/nebula-agents`:

```bash
python3 agents/scripts/resume-brief.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --run-id 2026-11-25-120320e9
python3 agents/scripts/project_context.py --product-root /home/gajap/uSandbox/repos/nebula/nebula-insurance-brain --action plan
```

Read the [PRD](PRD.md), [STATUS](STATUS.md), the seven stories, the [assembly plan](feature-assembly-plan.md), proposed [ADR-0081](../../../architecture/decisions/ADR-0081-foundation-ontology-authoring-and-release-runtime.md), the [foundation module design](foundation-module-design.yaml), [migration design](migration-design.sql), [contract inventory](contract-inventory.yaml) and the run's [gate decisions](../../../operations/evidence/runs/2026-11-25-120320e9/gate-decisions.md). Run the independent plan-review action before implementation.

## Carry-ins and gotchas

- The predicate key grammar and `_RELEASE_REF` grammar are ADR-0077 D2 as shipped; `ontrel:sha256-<64 hex>` fits the 128-character limit.
- `brain_temporal.commit` hard-codes `TemporalKind.STATE` today; the D10 CHECK `ck_cfv_v1_kind_shape` already accepts EVENT/ETERNAL shapes, so no DDL is needed.
- The registry port is synchronous; call `prepare(scope, release_refs)` in the same unit of work before resolving any non-`sys` key.
- Casbin `policy_rule` KG nodes and `policy.csv` rows must land together, or the KG drift check fails.
- KG wildcard bindings resolve only git-tracked files; bind new `ontology/**` and `brain-ontology` files with literal paths until committed.
- `coverage-report.yaml` source sets count only tracked files: `git add` new planning files, then rerun `validate.py --write-coverage-report`.
- Never run GPU-using tests during live lanes (not expected here: no parse or model call).

## Runtime setup / verification (as built, feature run 2026-11-26-54387a08)

From the repository root, in the engine environment (`uv sync --project engine --locked`):

```bash
# Offline: files only, exit 0 valid / 1 invalid / 2 usage.
python -m brain_ontology.cli validate ontology/modules/foundation/module.yaml
python -m brain_ontology.cli compile --check ontology/releases/foundation/1/release.yaml
python -m brain_ontology.cli compile ontology/releases/<name>/<n>/release.yaml   # writes the five lock files

# Runtime: authenticated principal (token file), existing API environment variables.
python -m brain_ontology.cli install --tenant <id> --kb <id> --token-file <path> ontology/releases/foundation/1
python -m brain_ontology.cli report  --tenant <id> --kb <id> --token-file <path> --candidate <ontrel:sha256-…>
python -m brain_ontology.cli review  --tenant <id> --kb <id> --token-file <path> --report <uuid> --decision approve --rationale "…"
python -m brain_ontology.cli activate --tenant <id> --kb <id> --token-file <path> --release <ontrel:…> --review <uuid>
python -m brain_ontology.cli rollback --tenant <id> --kb <id> --token-file <path> --release <ontrel:…>
python -m brain_ontology.cli history --tenant <id> --kb <id> --token-file <path>
```

- **Grants** (policy.csv): `ServicePrincipal` holds `install`/`read`; `OntologySteward` holds `review` (which also runs `report`), `activate` (which also covers `rollback`) and `read`; `TenantMember` holds `read` (`history`).
- **Prerequisite per KB:** a trusted `resource_access` row for `ResourceKey(ontology_release, <kb_id>)` with explicit classifications, created with `brain_persistence.tenancy.provision_resource_access`. Without it every command is denied (`missing_attributes`).
- **Release references:** the foundation@1 lock is `ontrel:sha256-3602b71f…` (see `ontology/releases/foundation/1/manifest.json`). Slots pin it in `predicate_release_ref`.
- **Commit shapes:** an ETERNAL predicate (for example `fnd:accountOrganization@v1`) takes `{"contract": "fact-temporal/v1", "valid_to_state": "OPEN"}` with no bounds. An EVENT predicate takes exactly one granularity period. STATE is unchanged.
- **Tests:** `engine/packages/brain-ontology/tests` (offline). `engine/tests/integration/test_ontology_*.py` and `test_temporal_kind_activation.py` need `BRAIN_MIGRATION_ADMIN_URL`.
- **Examples:** `python scripts/validation/build_foundation_examples.py --check` and `python scripts/validation/validate_semantic_rdf.py --require`, both with the `semantic-rdf` extra.

## Migration and concurrency gotchas

- 0017 follows 0016 (confirmed at G0). It also widens `resource_access.ck_resource_access_type`.
- Install serializes per tenant/KB with a transaction advisory lock; selection appends lock the current head row.
- Downgrade refuses once any `ontology_release` row exists; forward-repair instead.
