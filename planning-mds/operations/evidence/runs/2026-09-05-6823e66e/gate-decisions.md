# Gate Decisions — Init Run 2026-09-05-6823e66e

> Init gates I0–I6 (base run contract). Timestamps are the `commands.log` entries that closed each gate; the durable journal is `gate-state.json`.

## Gate Decisions

| Gate | Decision | Decider | Timestamp | Rationale | Blocking | Follow-up |
|------|----------|---------|-----------|-----------|----------|-----------|
| I0 | PASS | Product Manager (init mode) | 2026-09-05T23:31:47-04:00 | PROJECT_NAME, DOMAIN_DESCRIPTION, TARGET_USERS, CORE_ENTITIES recorded in `action-context.md`; Lifecycle Stage = Init; Scope Boundaries = Bootstrap only. | No | - |
| I1 | PASS | Product Manager | 2026-09-05T23:31:47-04:00 | Non-empty `{PRODUCT_ROOT}` confirmed by the operator before scaffolding; `scaffold-product.py` created 8 directories and 5 framework files, preserved all existing files (`preserved: []` because none of the five existed; the planning tree was untouched). | No | - |
| I2 | PASS | Product Manager | 2026-09-05T23:31:47-04:00 | `planning-mds/BLUEPRINT.md` pre-existed (Sections 0 to 6, authored 2026-09-05 from the master blueprint) and passes `validate-architecture.py`; the template was not re-applied (idempotent init). | No | - |
| I3 | PASS | Product Manager | 2026-09-05T23:32:47-04:00 | `REGISTRY.md` (Active, Retired, Planned, Archived) and `ROADMAP.md` (Now, Next, Later, Abandoned, Completed) created with EMPTY generated regions; Next Available Feature Number F0001; Archived and Retired not pre-populated. `tracker_gen.py` patched so compile.py tolerates zero features. | No | Upstream the `max(default=0)` fix to nebula-agents `scripts/kg/tracker_gen.py`. |
| I4 | PASS | Product Manager | 2026-09-05T23:33:10-04:00 | `operations/evidence/README.md` created with Base Run Profile (§8), Feature Evidence Profile (§9, §10), Effective-Date Boundary (§6, framework default 2026-05-19), Path Class Extensions (§7, 14 additive rows because the layout adds `neuron/`, asset trees, `golden-corpus/`, and lowercase security packages), Global Lanes (§20). `path_class_extension_conflict_fails` not triggered. | No | - |
| I5 | PASS | Product Manager | 2026-09-05T23:34:48-04:00 | `knowledge-graph/` produced by `compile.py` from the empty shard set (trio + ontology mirror + tracker regions), then `validate.py --regenerate-symbols --regenerate-decisions` and `--write-coverage-report`; `STORY-INDEX.md` generated. The spec's "empty YAML files" instruction is superseded by the compiled-projection toolchain the product adopted. | No | Upstream: `init.yaml` I5 should invoke compile.py; scaffold-map should carry the shard schemas, ontology seed, and toolchain. |
| I6 | PASS | Product Manager | 2026-09-05T23:34:49-04:00 | All five validators exit 0 via `run-gate.py`: `validate-trackers.py` (PASS, 0 warnings), `validate-feature-evidence.py` (0 validated, 0 skipped, 0 errors), `validate.py --check-symbols`, `validate.py --check-drift` (policy.csv absent → Casbin drift check skipped with a warning), `validate_templates.py`. | No | - |

Decisions: `PASS`, `PASS WITH RECOMMENDATIONS`, `FAIL`, `SKIP`. Blocking values: `Yes` / `No`.

## Post-init adaptations (same session, outside the gate list)

| Change | Rationale | Evidence |
|--------|-----------|----------|
| `lifecycle-stage.yaml` rewritten to product-local gates (`knowledge_graph_sync`, `kg_reproducibility`, plus the template's symbol, decision, orphan, and coverage-gap gates) | The template's gates are framework-relative and use `{PRODUCT_ROOT}`; `agents/scripts/run-lifecycle-gates.py` runs commands from the framework root and does not expand the placeholder, so the template cannot execute product gates. CONSUMER-CONTRACT §6 expects product-local gates. | `artifacts/post-init-product-lifecycle-gates.txt` (PASS) |
| `scripts/run-lifecycle-gates.py` added; `.github/workflows/ci-gates.yml` rewritten; `kg-reproducibility.yml` added | Product CI carries product-local equivalents (§6, §7); framework validators run in a second job with the framework checked out at the pinned commit. | workflow files |
| `planning-mds/domain/glossary.md` authored | init.md lists the glossary skeleton as a scaffolded output; `validate-architecture.py` and `validate-genericness.py --glossary` consume it. | `validate-architecture.py` PASS with warnings |
