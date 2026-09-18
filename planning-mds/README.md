# planning-mds (Solution-Specific)

All solution-specific planning for Nebula Insurance Brain lives here. Generic roles, actions, and templates are consumed in place from the sibling `nebula-agents` repo and are never copied into this tree.

## Entry points

- `BLUEPRINT.md` — framework entry point: process, product context, platform baseline, phase status
- `architecture/master-blueprint.md` — the full architecture baseline (through section 126); referenced by section number everywhere else
- `features/REGISTRY.md` and `features/ROADMAP.md` — generated from `kg-source/features/**` (created by init, populated when the feature shards are seeded)

## Where the master blueprint sections landed

| Master blueprint sections | Planning artifact |
|---|---|
| 0 to 2 thesis, concerns, non-goals; 3 technology; 77 layout | `BLUEPRINT.md` sections 1 and 2 |
| 76 ADR-0001 to ADR-0037; 116 ADR-0038 to ADR-0048; 122 ADR-0049 to ADR-0053 | `architecture/decisions/ADR-####-*.md` |
| 12 to 18, 78 to 81 | `architecture/data-model.md` |
| 66, 110, 118 to 123 | `security/README.md`, `security/authorization-review.md` |
| 96 to 98, 115, 121.2 | `testing/evaluation-strategy.md` |
| 95 roadmap, 115.3 sequencing | `BLUEPRINT.md` section 5; `kg-source/features/**` (seeded after init) |
| 85 to 89 v0.1 slices | Story sources for F0001, F0024, F0025 |
| 126 document pipeline orchestration | ADR-0060; F0004/F0005/F0015/F0016 and dependent feature scope amendments |
| 106 to 117 pre-build requirements and open decisions | `BLUEPRINT.md` section 4.8; ADR-0038 to ADR-0048 |

Everything else in the master blueprint remains authoritative in place until a feature's Phase B extracts it into a contract, schema, or ADR.

## Conventions

- Feature folders: `features/F####-{slug}/` with one story per file, `F####-S####-{slug}.md`.
- Knowledge graph: author shards under `kg-source/**`; `knowledge-graph/*.yaml` and the tracker tables are compiled by `scripts/kg/compile.py` and never hand-edited.
- Evidence: `operations/evidence/` per the framework Feature Evidence Contract (created by init).
- Runtime roots: `engine/`, `experience/`, `neuron/` (see `BLUEPRINT.md` section 2.3).

## Rule of thumb

If it is project-specific, it belongs here. Agents never embed it directly.

## Learn the semantic model

Start with the [worked GL example](examples/neurosymbolic-gl/README.md), then follow the [concept coverage map](examples/README.md) and [glossary](domain/glossary.md). Master blueprint section 124 and F0065 define the bounded v0.1 neurosymbolic assessment; illustrative records are distinguished from future observed runtime evidence.
