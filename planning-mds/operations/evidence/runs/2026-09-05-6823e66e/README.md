# Init Run 2026-09-05-6823e66e

**Action:** `agents/actions/init.md` — bootstrap the product planning tree (base-run-only, policy 2026-07-11)
**Product:** Nebula Insurance Brain (`{PRODUCT_ROOT}` = `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`)
**Framework:** nebula-agents @ `4eaf7b3abef84687f6fda622c61a95d378a50888`
**Date:** 2026-09-05
**Outcome:** **PASS** — gates I0 to I6 completed; all five I6 validators exit 0; registry-wide evidence scan reports 0 governed and 0 retired features.

## What this run produced

- Scaffold (I1): `lifecycle-stage.yaml`, `CONTRIBUTING.md`, `.github/workflows/ci-gates.yml`, `planning-mds/features/TRACKER-GOVERNANCE.md`, `planning-mds/architecture/SOLUTION-PATTERNS.md`, and the planning directory skeleton. Pre-existing planning content (BLUEPRINT, master blueprint, 53 ADRs, KG toolchain, shard schemas, ontology seed) was preserved.
- Trackers (I3): `planning-mds/features/REGISTRY.md` and `ROADMAP.md` with empty generated regions; Next Available Feature Number F0001.
- Evidence infrastructure (I4): `planning-mds/operations/evidence/README.md` with the Path Class Extensions for the `engine/experience/neuron` layout plus asset trees.
- Knowledge graph (I5): `planning-mds/knowledge-graph/` compiled from the empty shard set (canonical-nodes, feature-mappings, code-index, solution-ontology mirror), plus regenerated symbol-index, decisions-index, coverage-report; `STORY-INDEX.md` generated (0 stories).
- Judgment files authored alongside the gates: `planning-mds/domain/glossary.md` skeleton (33 entities, 8 terms, blocked-terms list), product-local `lifecycle-stage.yaml` gates with `scripts/run-lifecycle-gates.py`, and two CI workflows.

## Deviations from the init spec (recorded, not silent)

1. **I5 superseded by the compiler.** The spec says to create empty knowledge-graph YAML files; this product uses the compiled-projection toolchain, so `scripts/kg/compile.py` produced them from `kg-source/**` instead. Upstream candidate: `agents/actions/spec/init.yaml` I5 should invoke compile.py.
2. **tracker_gen.py patched** in the product copy to tolerate zero feature shards (`max(..., default=0)`); without it compile.py cannot run on a fresh product. Upstream candidate.
3. **Scaffold gaps filled before init** (step 3 of the adoption plan): the KG toolchain, shard JSON schemas, ontology seed, kg-source README, and projections-meta are required by I5/I6 but are not in `scaffold-map.yaml`. Upstream candidate.
4. **Lifecycle file adapted after scaffold.** The template's gates run from the framework root and reference `{PRODUCT_ROOT}`, which the framework runner does not expand; the product file now declares product-relative gates run by `scripts/run-lifecycle-gates.py` (CONSUMER-CONTRACT §6). The scaffolded `ci-gates.yml` was rewritten accordingly and `kg-reproducibility.yml` added.

## Evidence Index

- `action-context.md` — inputs, run identity, non-empty-root confirmation, scope boundaries
- `gate-decisions.md` — I0 to I6 decisions with timestamps
- `artifact-trace.md` — read, created, generated, omitted
- `commands.log` — JSONL command telemetry (scaffold, tracker authoring, compile, regenerate, story index, I6 validators)
- `lifecycle-gates.log` — I6 validator invocations recorded by `run-gate.py`
- `gate-state.json` — durable gate journal (all seven stages completed)
- `artifacts/i6-*.txt|json` — captured validator outputs; `artifacts/post-init-product-lifecycle-gates.txt` — product gate run

## Next Action

Seed `planning-mds/kg-source/features/F0001.yaml` to `F0026.yaml` (planned, from master blueprint section 95) and ADR node shards from `planning-mds/architecture/decisions/`, recompile, then run the `plan` action for F0001.
