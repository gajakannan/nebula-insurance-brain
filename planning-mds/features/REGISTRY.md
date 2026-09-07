# Feature Registry

**Next Available Feature Number:** F0066

**Planning Views:**
- Roadmap sequencing (`Now / Next / Later`): `planning-mds/features/ROADMAP.md`
- Story rollup index: `planning-mds/features/STORY-INDEX.md`
- Governance contract: `planning-mds/features/TRACKER-GOVERNANCE.md`

The feature tables below are generated fenced regions compiled from `planning-mds/kg-source/features/**` by `scripts/kg/compile.py` (via `tracker_gen.py`). Edit the feature shards, never the tables. The epic inventory for this product is master blueprint sections 95 and 124 (original F0001 to F0063 plus F0065; F0064 tracks repository tooling); features enter this registry as their shards are seeded and planned.

## Active Features

<!-- generated:begin registry:active -->
| Feature ID | Name | Status | Phase | Folder |
|------------|------|--------|-------|--------|
| F0001 | Repository and engineering foundation | Active | Pre-build | `F0001-repository-and-engineering-foundation/` |
<!-- generated:end registry:active -->

## Retired Features

Per §19 of the feature-evidence package contract. Retired features are registry records that were not delivered as completed scope.

<!-- generated:begin registry:retired -->
| Feature ID | Name | Terminal Status | Superseded By | Retired Date | Folder | Reason |
|------------|------|-----------------|---------------|--------------|--------|--------|
<!-- generated:end registry:retired -->

## Planned (Reserved IDs)

<!-- generated:begin registry:planned -->
| Feature ID | Name | Status | Phase | Folder |
|------------|------|--------|-------|--------|
| F0002 | Tenancy-aware domain kernel + verified stable principal and scope contracts | Planned | v0.1A | `F0002-tenancy-aware-domain-kernel-and-principal-contracts/` |
| F0003 | PostgreSQL persistence | Planned | v0.1A | `F0003-postgresql-persistence/` |
| F0004 | Content artifact model | Planned | v0.1A | `F0004-content-artifact-model/` |
| F0005 | One-time Docling ingestion | Planned | v0.1A | `F0005-one-time-docling-ingestion/` |
| F0006 | Assertion plane + origin + interpretation basis | Planned | v0.1A | `F0006-assertion-plane-origin-and-interpretation-basis/` |
| F0007 | FactSlot model | Planned | v0.1A | `F0007-factslot-model/` |
| F0008 | Bitemporal canonical facts | Planned | v0.1A | `F0008-bitemporal-canonical-facts/` |
| F0009 | Provenance + human-correction lineage | Planned | v0.1A | `F0009-provenance-and-human-correction-lineage/` |
| F0010 | Change/retraction semantics | Planned | v0.1A | `F0010-change-and-retraction-semantics/` |
| F0011 | JSON Schema contract system | Planned | v0.1A | `F0011-json-schema-contract-system/` |
| F0012 | Foundation ontology | Planned | v0.1A | `F0012-foundation-ontology/` |
| F0013 | Insurance Core GL ontology | Planned | v0.1A | `F0013-insurance-core-gl-ontology/` |
| F0014 | Document Profile model | Planned | v0.1A | `F0014-document-profile-model/` |
| F0015 | Extraction Profile compiler | Planned | v0.1A | `F0015-extraction-profile-compiler/` |
| F0016 | Semantic interpretation runs | Planned | v0.1A | `F0016-semantic-interpretation-runs/` |
| F0017 | Deterministic entity resolution | Planned | v0.1A | `F0017-deterministic-entity-resolution/` |
| F0018 | Canonical commit service + action authorization and policy-version audit | Planned | v0.1B | `F0018-canonical-commit-service-and-action-authorization/` |
| F0019 | Basic endorsement supersession | Planned | v0.1B | `F0019-basic-endorsement-supersession/` |
| F0020 | Minimal graph/temporal query API | Planned | v0.1B | `F0020-minimal-graph-and-temporal-query-api/` |
| F0021 | Native React semantic shell + OIDC/session contract and safe re-auth behavior | Planned | v0.1B | `F0021-native-react-semantic-shell-and-oidc-session/` |
| F0022 | Document 360 + Label Studio evidence review integration + parent/classification and reviewer authority | Planned | v0.1B | `F0022-document-360-and-label-studio-evidence-review/` |
| F0023 | Minimal Entity 360 | Planned | v0.1B | `F0023-minimal-entity-360/` |
| F0024 | GL vertical slice | Planned | v0.1B | `F0024-gl-vertical-slice/` |
| F0025 | Endorsement bitemporal slice | Planned | v0.1B | `F0025-endorsement-bitemporal-slice/` |
| F0026 | v0.1 hardening + Label Studio Golden Corpus workflow + AuthX negative tests and policy parity | Planned | v0.1C | `F0026-v0-1-hardening-golden-corpus-and-authx-tests/` |
| F0027 | Probabilistic entity resolution | Planned | v0.2B | `F0027-probabilistic-entity-resolution/` |
| F0028 | Conflict and supersession | Planned | v0.2B | `F0028-conflict-and-supersession/` |
| F0029 | Ontology discovery | Planned | v0.2B | `F0029-ontology-discovery/` |
| F0030 | Ontology Workbench | Planned | v0.2B | `F0030-ontology-workbench/` |
| F0031 | Document/Extraction Profile Workbench | Planned | v0.2B | `F0031-document-and-extraction-profile-workbench/` |
| F0032 | Knowledge Evolution Engine | Planned | v0.2B | `F0032-knowledge-evolution-engine/` |
| F0033 | pgvector retrieval | Planned | v0.2A | `F0033-pgvector-retrieval/` |
| F0034 | AGE graph projection | Planned | v0.2A | `F0034-age-graph-projection/` |
| F0035 | Hybrid search + consistent authorized rows/counts/facets/graph scope | Planned | v0.2A | `F0035-hybrid-search-and-authorized-scope/` |
| F0036 | Evidence-aware retrieval / grounded generation | Planned | v0.2A | `F0036-evidence-aware-retrieval-and-grounded-generation/` |
| F0037 | Native Semantic Conversation Engine + Onyx-inspired Chat mechanics | Planned | v0.2A | `F0037-native-semantic-conversation-engine/` |
| F0038 | Chat with Document | Planned | v0.2A | `F0038-chat-with-document/` |
| F0039 | Chat with Entity | Planned | v0.2A | `F0039-chat-with-entity/` |
| F0040 | Conversation Graph | Planned | v0.2A | `F0040-conversation-graph/` |
| F0041 | Learning Plane | Planned | v0.2B | `F0041-learning-plane/` |
| F0042 | Knowledge promotion/governance | Planned | v0.2B | `F0042-knowledge-promotion-and-governance/` |
| F0043 | Generalized review queues / governance | Planned | v0.2B | `F0043-generalized-review-queues-and-governance/` |
| F0044 | Expanded Entity 360 | Planned | v0.2A | `F0044-expanded-entity-360/` |
| F0045 | Cytoscape Graph Explorer | Planned | v0.2A | `F0045-cytoscape-graph-explorer/` |
| F0046 | Semantic API | Planned | v0.2A | `F0046-semantic-api/` |
| F0047 | Read-only MCP + verified principal, bounded delegation, and evidence access | Planned | v0.2A | `F0047-read-only-mcp-and-bounded-delegation/` |
| F0048 | Process domain model | Planned | v0.3 | `F0048-process-domain-model/` |
| F0049 | Canonical Transition Service | Planned | v0.3 | `F0049-canonical-transition-service/` |
| F0050 | Temporal.io | Planned | v0.3 | `F0050-temporal-io/` |
| F0051 | Process Workbench | Planned | v0.3 | `F0051-process-workbench/` |
| F0052 | Normative constraints | Planned | v0.3 | `F0052-normative-constraints/` |
| F0053 | Hypothetical scenarios | Planned | v0.3 | `F0053-hypothetical-scenarios/` |
| F0054 | Process reconciliation | Planned | v0.3 | `F0054-process-reconciliation/` |
| F0055 | Native reasoning | Planned | v0.4+ | `F0055-native-reasoning/` |
| F0056 | Derived dependency invalidation | Planned | v0.4+ | `F0056-derived-dependency-invalidation/` |
| F0057 | Decision ledger | Planned | v0.4+ | `F0057-decision-ledger/` |
| F0058 | Historical decision replay | Planned | v0.4+ | `F0058-historical-decision-replay/` |
| F0059 | Execution gate | Planned | v0.4+ | `F0059-execution-gate/` |
| F0060 | Reasoning-pattern governance | Planned | v0.4+ | `F0060-reasoning-pattern-governance/` |
| F0061 | Advanced retrieval | Planned | v0.4+ | `F0061-advanced-retrieval/` |
| F0062 | Advanced reasoners | Planned | v0.4+ | `F0062-advanced-reasoners/` |
| F0063 | Future DSL | Planned | v0.4+ | `F0063-future-dsl/` |
| F0064 | Repository instructions and planning-check adoption | Planned | Repository Tooling | `F0064-repository-instructions-and-planning-check-adoption/` |
| F0065 | Grounded GL guideline assessment | Planned | v0.1B | `F0065-grounded-gl-guideline-assessment/` |
<!-- generated:end registry:planned -->

## Archived Features

<!-- generated:begin registry:archived -->
| Feature ID | Name | Archived Date | Evidence Reentry Date | Folder |
|------------|------|---------------|-----------------------|--------|
<!-- generated:end registry:archived -->

## Numbering Rules

- Feature IDs use a 4-digit zero-padded format: `F0001`, `F0002`, ..., `F9999`
- Numbers are assigned sequentially and never reused; the master blueprint section 95 identifiers F0001 to F0063 are reserved in that order
- Story IDs within a feature follow `F{NNNN}-S{NNNN}` (for example `F0001-S0001`)
- **Next Available Feature Number** is recomputed by the tracker generator from the feature shards
