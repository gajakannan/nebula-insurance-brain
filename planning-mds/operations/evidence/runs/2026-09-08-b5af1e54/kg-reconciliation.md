# Knowledge-Graph Reconciliation — F0001-repository-and-engineering-foundation run 2026-09-08-b5af1e54

## Scope

- Feature ID: F0001
- Run ID: 2026-09-08-b5af1e54
- Date: 2026-09-10
- Reconciled by: Architect (feature-action, G7)

## Binding Delta

Baseline: `feature-assembly-plan.md`'s "Knowledge-Graph Binding Plan" (authored at G0,
2026-09-06/08), which declared ten intended capability→path bindings. No bindings had
actually been authored as shards yet (`kg-source/bindings/` was empty apart from
`.gitkeep`) — this gate is where they land, against the as-built source.

| Capability / node | code-index binding (glob) | G0-declared? | Action |
|-------------------|---------------------------|--------------|--------|
| `capability:runtime-roots-and-toolchain` | `engine/apps/api/src/brain_api/{app,health,errors}.py`, `engine/pyproject.toml`, `neuron/pyproject.toml` | yes | added |
| `capability:local-dependency-stack` | `docker-compose.yml`, `docker/postgres/**`, `docker/DEPENDENCY-MATRIX.md` | yes | added |
| `capability:local-inference-service` | `docker/local-inference-runbook.md`, `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_adapter.py` | yes | added |
| `capability:parse-once-content-artifact` | `neuron/packages/brain-ingestion/src/**`, `engine/packages/brain-content/src/**` | yes | added |
| `capability:semantic-interpretation-run` | `neuron/packages/brain-extraction/src/**`, `neuron/packages/brain-interpretation/src/**` | yes | added |
| `capability:evidence-review-round-trip` | `engine/packages/brain-review/src/**`, `experience/src/review-panel/**` | yes | added |
| `capability:bitemporal-canonical-commit` | `engine/packages/brain-temporal/src/**`, `engine/migrations/versions/0003_fact_slots_and_commits.py` | yes | added |
| `capability:credential-verification-and-principal-resolution` | `engine/packages/brain-security/src/brain_security/{verification,principals}.py` | yes | added |
| `capability:authorization-enforcement` | `engine/packages/brain-security/src/brain_security/{authorization,casbin_adapter,audit}.py`, `planning-mds/security/policies/**` | yes | added |
| `capability:backup-and-restore` | `scripts/ops/**` | yes | added |

All ten bindings match the G0 declaration exactly — no as-built deviation from the
predicted binding surface. Authored as `planning-mds/kg-source/bindings/f0001.yaml` (one
bundle shard, ten `binding` records against `planning-mds/schemas/kg-source/binding.schema.json`'s
`paths: {category: [globs]}` shape), then compiled via `scripts/kg/compile.py` into
`code-index.yaml` (`node_bindings`, now 10 entries, up from 0).

One naming note recorded, not requiring a binding change: `capability:local-inference-service`'s
declared binding path (`docling_graph_adapter.py`) still points at the correct file — that
module now calls the OpenAI-compatible vLLM endpoint directly rather than the `docling-graph`
package (ADR-0040), but the file itself remains the right binding target for this capability;
the semantic decision is recorded in the ADR, not the binding shard.

## Canonical Nodes

**None introduced; reuses existing semantics.** The ten capabilities, twelve entities (ten
of F0001's own plus two carried by F0065's later ontology binding), four workflows (three
of which — `ingestion-interpretation`, `canonical-commit`, `human-review` — are F0001's),
`endpoints.yaml`, `roles.yaml`, and `policy_rules.yaml` were all already authored as node
shards at Phase B / G0 (plan run `2026-09-06-cdb5d8cb`). This reconciliation confirms they
match the as-built implementation and adds no new canonical nodes or `WHY` rationale beyond
what G0 already declared — the two ADR-level findings this run recorded (Docling-Graph
rejected, ADR-0058 amended) are captured in the ADR files themselves and in
`master-blueprint.md`'s §116.1 reconciliation table (rows 14, 47–49, 75, 80–81, 104), not
as new KG nodes, since they are decision-record content, not new solution-graph structure.

## Validator Results

| Check | Command | Result |
|-------|---------|--------|
| symbol regen + check | `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions` | PASS (exit 0) — 190 symbols, 190 on bound nodes (python); TypeScript extractor unavailable in this environment, 8 `experience/` files skipped (pre-existing tooling gap, not introduced by this run) |
| drift | `validate.py --check-drift` | PASS (exit 0) — 10 code bindings, 0 uncovered features, no drift errors |

`coverage-report.yaml` was **not** regenerated at this gate, per instruction — deferred to
G8, after the (not-yet-decided) archive move.

## Handoff to Closeout

Semantic graph is green and ready for PM closeout to verify. No binding gap found; no
route-back to a G7 delta pass needed.
