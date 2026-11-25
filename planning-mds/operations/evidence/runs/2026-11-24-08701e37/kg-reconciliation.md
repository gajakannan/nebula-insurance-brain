# Knowledge-Graph Reconciliation — F0009 run 2026-11-24-08701e37

Reviewer: Claude (Opus 5.5) / Architect
Date: 2026-11-25

Result: PASS

## G0 prediction vs as-built

G0 predicted that the existing planned capabilities `provenance-lineage`, `review-submission-attribution` and `learning-candidate-reservation` gain code bindings, plus migration 0016. That held. No other new capability or canonical semantic emerged during implementation.

## Binding Delta

Applied in `kg-source/bindings/f0009-planning.yaml`.

Bindings use code paths only, which are stable across the G8 archive move. Each schema is now bound only to the capability that owns it.

| Node | Added code/test bindings |
|---|---|
| capability:provenance-lineage | `brain_domain/provenance.py`, `engine/packages/brain-provenance/**`, `brain_persistence/provenance.py`, `brain_persistence/lineage_contracts.py`; domain, facade, fixture and integration tests |
| capability:learning-candidate-reservation | `provenance_models.py`, `repositories.py`, `brain_review/decisions.py`; review unit and correction integration tests |
| capability:review-submission-attribution | `provenance_models.py`, `repositories.py`, `decisions.py`, `routes/reviews.py`, `schemas/review.py`; correction and API compatibility tests |
| migration:f0009-provenance-hooks (new node) | `engine/migrations/versions/0016_f0009_provenance_hooks.py`; `test_f0009_migration.py` |

`brain_api/deps.py` stays with `capability:runtime-roots-and-toolchain` (the composition root), not F0009. The existing `evidence-review-round-trip` and `durable-authorization-decisions` bindings already cover `decisions.py`, `reviews.py` and `execution.py`, which I confirmed rather than duplicated.

## Canonical Nodes

- **New:** `nodes/migrations/f0009-provenance-hooks.yaml`.
- **Updated:** the notes of the three capability nodes now record the as-built run.
- **Unchanged:** no new entity, canonical vocabulary or rationale (`WHY`) entry. ADR-0080 is unchanged and stays Proposed.

## PR-L3 (plan review) — story mapping precision

Each F0009 story mapping in `kg-source/features/F0009.yaml` now names only its own schemas and ADRs. Examples:

- S0005: `learning-candidate-reservation-v1` with ADR-0080/0037/0044.
- S0003: `provenance-result-v1`, `fact-version-read-v1` and `fact-temporal-v1` with ADR-0080/0078/0077.

The feature shard's `affects` gains `migration:f0009-provenance-hooks`. PM owns feature status and path at G8.

## Validator Results

- `compile.py`: pass. It regenerated `canonical-nodes.yaml`, `feature-mappings.yaml`, `code-index.yaml`, `solution-ontology.yaml` and the tracker regions.
- `validate.py --regenerate-symbols --check-symbols --regenerate-decisions --check-decisions`: pass, with 0 unknown-symbol warnings.
- `validate.py --check-drift`: pass.
- `--write-coverage-report` was **not** run at this gate; it is deferred to G8, after the archive move.

## Tooling note (follow-up)

`scripts/kg/symbols.py` keys its per-file cache (`.kg-state/symbols-cache.json`) by content hash only. When a binding moves an unchanged file to another node, the cache keeps the old node. Here that produced 8 dangling-symbol warnings, which cleared after deleting the local cache. Follow-up owner: KG tooling (framework). Proposed fix: include the bound node id in the cache key.

## Handoff to Closeout

The semantic graph is final for G8. The PM verifies it and does not re-author it. Closeout owns:

- the feature shard's `path` and `status` for the archive move (logical `F0009/` refs resolve through the shard);
- regenerating `coverage-report.yaml` after the move;
- the closeout `--check-drift` and plain `validate.py` runs.

No binding names a feature-document path that the move relocates.
