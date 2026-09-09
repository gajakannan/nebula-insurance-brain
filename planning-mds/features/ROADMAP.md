# Feature Roadmap (Now / Next / Later)

**Last Reviewed:** 2026-09-07 (v0.1 bounded assessment scope amendment; implementation review pending)

This document is the working prioritization view for feature sequencing. The tables are generated fenced regions compiled from `planning-mds/kg-source/features/**` (`roadmap_section`, `roadmap_order`, `rationale`, `validation_gate`, `completion_state`); edit the shards, never the tables. The delivery sequence is master blueprint sections 115.3 and 124: canonical foundations and 360 base views → F0065 bounded assessment → F0024/F0025 integration → F0026 release qualification. Generalized reasoning remains later.

## Purpose

- Provide a current planning dashboard for sequencing decisions.
- Keep prioritization separate from feature metadata in `REGISTRY.md`.
- Avoid constant churn in `BLUEPRINT.md`, which stays baseline strategy.

## Update Rules

- Update whenever feature priority or sequence changes, by editing the feature shard and recompiling.
- Keep entries at feature level (not story-level unless explicitly needed).
- Every feature carries a rationale for its section.

## Now

<!-- generated:begin roadmap:now -->
| Feature | Status | Why Now | Validation Gate |
|---------|--------|---------|-----------------|
| [F0001 — Repository and engineering foundation](./F0001-repository-and-engineering-foundation/README.md) | Active | Plan approved 2026-09-06 (Phase A at G3, Phase B at G5, plan run 2026-09-06-cdb5d8cb): assembly plan, contracts, schemas, policy, ADR-0054 and ADR-0055 in place. Everything downstream needs the runtime roots, the pinned dependency stack, and the four section 115.4 proofs recorded before any contract is frozen. | Four section 115.4 proofs recorded with results in ADRs; product lifecycle gates green; PostgreSQL with pgvector and AGE and Docling start locally from docker-compose, and the proof-scope Review Panel resolves its anchors. |
<!-- generated:end roadmap:now -->

## Next

<!-- generated:begin roadmap:next -->
| Feature | Status | Why Next | Entry Criteria |
|---------|--------|----------|----------------|
| [F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts](./F0002-tenancy-aware-domain-kernel-and-principal-contracts/README.md) | Planned | Structural tenancy and verified principals must exist in the first schema because every authoritative row carries tenant and knowledge-base ids and authorization is enforced at retrieval (sections 65, 66). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0003 — PostgreSQL persistence](./F0003-postgresql-persistence/README.md) | Planned | PostgreSQL is the authoritative runtime store; the core tables, range types, and exclusion constraints underpin every later feature (section 78). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0004 — Content artifact model](./F0004-content-artifact-model/README.md) | Planned | The content artifact contract (native DoclingDocument plus normalized views, blocks, coordinates, manifest) is what parse-once preserves and what every interpretation reads (sections 5, 80, 81, 108). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0005 — One-time Docling ingestion](./F0005-one-time-docling-ingestion/README.md) | Planned | One-time Docling ingestion is the foundational rule; durable ingestion with idempotency keys and a transactional outbox is a P0 pre-build requirement (sections 5, 114.1). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0006 — Assertion plane + origin + interpretation basis](./F0006-assertion-plane-origin-and-interpretation-basis/README.md) | Planned | The assertion plane records what sources claim before anything becomes truth; origin and interpretation basis are first-class from the first extraction (section 11). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0007 — FactSlot model](./F0007-factslot-model/README.md) | Planned | FactSlot defines canonical semantic identity for every fact; the GL limits in the v0.1 acceptance question are distinct FactSlots (section 13). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0008 — Bitemporal canonical facts](./F0008-bitemporal-canonical-facts/README.md) | Planned | Full bitemporality with database-level overlap integrity is required before the endorsement slice can be proven (sections 14, 15, 109.2). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0009 — Provenance + human-correction lineage](./F0009-provenance-and-human-correction-lineage/README.md) | Planned | No authoritative fact exists without evidence, and human corrections append with lineage that feeds the Golden Corpus (sections 17, 75). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0010 — Change/retraction semantics](./F0010-change-and-retraction-semantics/README.md) | Planned | Explicit change semantics distinguish a legitimate endorsement from a bad extraction correction (section 16). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0011 — JSON Schema contract system](./F0011-json-schema-contract-system/README.md) | Planned | JSON Schema 2020-12 is the cross-language structural contract shared by Pydantic, AJV, and OpenAPI (sections 25 to 27). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0012 — Foundation ontology](./F0012-foundation-ontology/README.md) | Planned | The foundation ontology module is the versioned base that every insurance module composes on (sections 19 to 22). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0013 — Insurance Core GL ontology](./F0013-insurance-core-gl-ontology/README.md) | Planned | The General Liability module of the insurance core ontology supplies the coverage, limit, and trigger concepts the v0.1 slice extracts (sections 23, 24, 107). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0014 — Document Profile model](./F0014-document-profile-model/README.md) | Planned | Document profiles select which ontology modules and extraction profiles apply to a document type and business context (section 7). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0015 — Extraction Profile compiler](./F0015-extraction-profile-compiler/README.md) | Planned | Composable extraction profiles compile a shared base with line-of-business extensions; reinterpretation without reparse depends on them (section 8). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0016 — Semantic interpretation runs](./F0016-semantic-interpretation-runs/README.md) | Planned | Semantic interpretation runs version every extraction over persisted content and are the unit of incremental reinterpretation (sections 28, 29). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0017 — Deterministic entity resolution](./F0017-deterministic-entity-resolution/README.md) | Planned | Deterministic entity resolution with stable, scoped identifiers ships before probabilistic resolution (sections 53, 107.3). | F0001 accepted; plan action Phase A and Phase B approved for this feature. |
| [F0064 — Repository instructions and planning-check adoption](./F0064-repository-instructions-and-planning-check-adoption/README.md) | Planned | Adopt the generic project extension contract with Brain-local guidance, review criteria, and structural planning checks. User-requested repository tooling; does not alter F0001 or the master blueprint's runtime epic inventory. | Local fixtures and project-wide checks pass through the shared executor; framework release is published and blueprint/CI pins match; Git source-control tools select the child repository. |
<!-- generated:end roadmap:next -->

## Later

<!-- generated:begin roadmap:later -->
| Feature | Status | Notes |
|---------|--------|-------|
| [F0018 — Canonical commit service + action authorization and policy-version audit](./F0018-canonical-commit-service-and-action-authorization/README.md) | Planned | The canonical commit service is the only write path to truth, with action authorization, policy-version audit, transactional outbox, and projection delivery (sections 66, 109). |
| [F0019 — Basic endorsement supersession](./F0019-basic-endorsement-supersession/README.md) | Planned | Basic endorsement supersession exercises change semantics and bitemporal versions on a real policy change (section 87). |
| [F0020 — Minimal graph/temporal query API](./F0020-minimal-graph-and-temporal-query-api/README.md) | Planned | A minimal graph and temporal query API answers the v0.1 acceptance questions as of valid time and recorded time (sections 20, 68, 87). |
| [F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior](./F0021-native-react-semantic-shell-and-oidc-session/README.md) | Planned | The native React semantic shell with the OIDC session contract and safe re-auth behavior is the first user-facing surface (section 3, 120.5). |
| [F0022 — Document 360 + native evidence review panel + parent/classification and reviewer authority](./F0022-document-360-and-native-evidence-review/README.md) | Planned | Document 360 with the Nebula Review Panel is the v0.1 human-correction loop, including the renderer set, the evidence anchoring contract, parent and classification checks, and reviewer authority (sections 71, 75, 111, 125). |
| [F0023 — Minimal Entity 360](./F0023-minimal-entity-360/README.md) | Planned | Minimal Entity 360 exposes current and historical facts with evidence pointers for the acceptance question (section 70). |
| [F0065 — Grounded GL guideline assessment](./F0065-grounded-gl-guideline-assessment/README.md) | Planned | Bounded neurosymbolic GL assessment: profile-guided model interpretation, governed canonical facts, and a versioned exact-decimal guideline comparison with snapshot/evidence lineage. After F0018–F0023; before F0024/F0025 integration and F0026 qualification. Draft planning package; runtime not started. |
| [F0024 — GL vertical slice](./F0024-gl-vertical-slice/README.md) | Planned | The GL vertical slice proves actual model interpretation through evidence review and canonical acceptance to the bounded F0065 guideline assessment, with exact rule/fact/evidence lineage and explicit time context (sections 86, 124). |
| [F0025 — Endorsement bitemporal slice](./F0025-endorsement-bitemporal-slice/README.md) | Planned | The endorsement slice proves both fact and F0065 assessment answers at distinct valid/recorded coordinates after retroactive endorsement, preserving historical results and current access checks (sections 87, 124). |
| [F0026 — v0.1 hardening + Golden Corpus workflow + AuthX negative tests and policy parity](./F0026-v0-1-hardening-golden-corpus-and-authx-tests/README.md) | Planned | v0.1 hardening closes Golden Corpus, AuthX, recovery, revocation, and independent frozen evaluation gates, including F0065 assessment correctness, lineage, temporal freshness, and complete derived-result access (sections 96, 115, 121, 124). |
| [F0033 — pgvector retrieval](./F0033-pgvector-retrieval/README.md) | Planned | pgvector adds exact and approximate vector retrieval as a tenant-scoped projection; vectors locate evidence and never define truth (section 50). |
| [F0034 — AGE graph projection](./F0034-age-graph-projection/README.md) | Planned | Apache AGE provides openCypher traversal over canonical entities and relationships as a rebuildable projection with commit-consistent delivery (sections 47 to 49, 109.3). |
| [F0035 — Hybrid search + consistent authorized rows/counts/facets/graph scope](./F0035-hybrid-search-and-authorized-scope/README.md) | Planned | Search fusion across full-text, vector, graph, ontology, temporal, and metadata signals with authorization applied before rows, counts, facets, and graph paths (sections 51, 120.3). |
| [F0036 — Evidence-aware retrieval / grounded generation](./F0036-evidence-aware-retrieval-and-grounded-generation/README.md) | Planned | Grounded answers carry scope, time basis, evidence references, and abstention, and counts or financial analysis run through typed authorized query plans rather than retrieved passages (sections 44, 113). |
| [F0037 — Native Semantic Conversation Engine + Onyx-inspired Chat mechanics](./F0037-native-semantic-conversation-engine/README.md) | Planned | The native conversation engine implements turn trees, streaming, citations, branching, attachments, and feedback studied from Onyx while keeping Nebula's semantic model and scoping (sections 37, 72). |
| [F0038 — Chat with Document](./F0038-chat-with-document/README.md) | Planned | Chat rooted on a document distinguishes what the document says from what the Brain currently accepts and cites content blocks as evidence (sections 38, 113.1). |
| [F0039 — Chat with Entity](./F0039-chat-with-entity/README.md) | Planned | Chat rooted on an account, policy, or claim expands context only through permitted relationships and answers as of valid time and recorded time (sections 39, 113.1). |
| [F0040 — Conversation Graph](./F0040-conversation-graph/README.md) | Planned | A temporary conversation graph holds hypotheses and discovered relationships outside canonical truth until explicit promotion (sections 40, 41, 43). |
| [F0044 — Expanded Entity 360](./F0044-expanded-entity-360/README.md) | Planned | Entity 360 grows to relationships, conflicts, decisions, learned insights, and conversation with valid-as-of and known-as-of controls (section 70). |
| [F0045 — Cytoscape Graph Explorer](./F0045-cytoscape-graph-explorer/README.md) | Planned | The graph explorer visualizes the AGE projection with time-aware traversal inside the native semantic UX (section 73). |
| [F0046 — Semantic API](./F0046-semantic-api/README.md) | Planned | The semantic API expands the read surface over entities, facts, relationships, evidence, history, ontology, search, and graph with permission-safe retrieval on every path (sections 68, 120.3). |
| [F0047 — Read-only MCP + verified principal, bounded delegation, and evidence access](./F0047-read-only-mcp-and-bounded-delegation/README.md) | Planned | Read-only MCP tools use the same verified principal, resource scope, and evidence restrictions as the API; agents receive bounded delegation and no canonical write path (sections 69, 120.4). |
| [F0027 — Probabilistic entity resolution](./F0027-probabilistic-entity-resolution/README.md) | Planned | Fuzzy, embedding, and model-assisted entity resolution with reversible merges follows the deterministic v0.1 resolver; every merge stays inspectable through merge history (sections 53, 90). |
| [F0028 — Conflict and supersession](./F0028-conflict-and-supersession/README.md) | Planned | Generalized conflict handling resolves disagreeing assertions into accepted state while preserving both claims and their lineage (sections 54, 90). |
| [F0029 — Ontology discovery](./F0029-ontology-discovery/README.md) | Planned | Discovery proposes concepts, relationships, and abstractions from persisted content and conversations as learning candidates rather than editing the ontology directly (sections 33, 34, 90). |
| [F0030 — Ontology Workbench](./F0030-ontology-workbench/README.md) | Planned | Ontology authoring and release management with immutable module releases, dependency locks, change classification, dry-run impact analysis, and rollback (sections 21, 112). |
| [F0031 — Document/Extraction Profile Workbench](./F0031-document-and-extraction-profile-workbench/README.md) | Planned | Profile authoring with release hashes pinned to interpretation runs so changing a profile never silently reinterprets history (sections 7, 8, 112). |
| [F0032 — Knowledge Evolution Engine](./F0032-knowledge-evolution-engine/README.md) | Planned | When an ontology or profile release changes meaning, the engine determines affected profiles, content, derived facts, and candidates and schedules targeted reinterpretation (sections 30, 112). |
| [F0041 — Learning Plane](./F0041-learning-plane/README.md) | Planned | The learning plane holds candidates, evidence, gaps, and reasoning-pattern candidates with independent-support rules so repetition never becomes proof (sections 31 to 35, 110.5). |
| [F0042 — Knowledge promotion/governance](./F0042-knowledge-promotion-and-governance/README.md) | Planned | Governed promotion moves conversation artifacts and learning candidates into canonical knowledge or the ontology through review and provenance checks (sections 32, 42). |
| [F0043 — Generalized review queues / governance](./F0043-generalized-review-queues-and-governance/README.md) | Planned | Review queues generalize beyond extraction correction to conflicts, merges, candidates, and promotions, with the Review Panel kept for evidence-oriented adjudication and business approval kept separate (sections 75, 111.2, 125). |
| [F0048 — Process domain model](./F0048-process-domain-model/README.md) | Planned | Process semantics separate canonical, observed, and execution state so workflow state never masquerades as enterprise truth (sections 59, 60). |
| [F0049 — Canonical Transition Service](./F0049-canonical-transition-service/README.md) | Planned | Every process state change is a canonical commit through the transition service with evidence and authorization (section 61). |
| [F0050 — Temporal.io](./F0050-temporal-io/README.md) | Planned | Temporal owns durable execution and proposes state changes only through canonical commit services (section 62). |
| [F0051 — Process Workbench](./F0051-process-workbench/README.md) | Planned | Process definitions and instances become authorable and inspectable once transition semantics are canonical (sections 59, 91). |
| [F0052 — Normative constraints](./F0052-normative-constraints/README.md) | Planned | Obligations such as issue-within-24-hours are modeled separately from fact modes and evaluated against canonical and execution state (section 57). |
| [F0053 — Hypothetical scenarios](./F0053-hypothetical-scenarios/README.md) | Planned | Scenarios assume facts without asserting them and stay apart from canonical truth through an explicit knowledge mode (sections 58, 113.1). |
| [F0054 — Process reconciliation](./F0054-process-reconciliation/README.md) | Planned | The reconciliation view shows canonical, observed, execution, and normative state side by side and flags disagreement (section 74). |
| [F0055 — Native reasoning](./F0055-native-reasoning/README.md) | Planned | Generalized native ontology inference and broader business-rule composition extend the bounded F0065 v0.1 evaluator, preserving exact inputs, rule versions, evidence, and explicit rejection of unsupported constructs (sections 45, 92, 112, 124). |
| [F0056 — Derived dependency invalidation](./F0056-derived-dependency-invalidation/README.md) | Planned | Automatic propagation across persisted derived canonical facts invalidates and recomputes dependencies after input changes; it extends the lineage introduced by F0065 without being a prerequisite for its on-demand v0.1 assessments (sections 55, 56, 124). |
| [F0057 — Decision ledger](./F0057-decision-ledger/README.md) | Planned | Decisions record the exact fact versions, recorded-time snapshot, rule, ontology, and model versions used (section 63). |
| [F0058 — Historical decision replay](./F0058-historical-decision-replay/README.md) | Planned | Replay reconstructs what was known at decision time from the ledger and recorded-time state without reinstating revoked access (sections 63, 110). |
| [F0059 — Execution gate](./F0059-execution-gate/README.md) | Planned | Agent-proposed actions pass authorization, ontology constraints, business rules, process and temporal state, evidence requirements, and unresolved conflicts before ALLOW, DENY, or REVIEW (section 64). |
| [F0060 — Reasoning-pattern governance](./F0060-reasoning-pattern-governance/README.md) | Planned | Repeated analytical patterns become governed reasoning-pattern candidates promoted into skills, rule sets, or workflows with provenance (sections 35, 45). |
| [F0061 — Advanced retrieval](./F0061-advanced-retrieval/README.md) | Planned | Dense plus sparse retrieval, multivectors, reranking, and optional Qdrant arrive only when vector retrieval becomes an independent scaling problem (sections 52, 93). |
| [F0062 — Advanced reasoners](./F0062-advanced-reasoners/README.md) | Planned | Additional reasoner providers such as OWL-DL, Datalog, and advanced scenario simulation plug in around the semantic core without owning meaning (sections 92 to 94). |
| [F0063 — Future DSL](./F0063-future-dsl/README.md) | Planned | A PULSE-like executable process DSL compiles to canonical process semantics and never becomes a second truth store (section 94). |
<!-- generated:end roadmap:later -->

## Abandoned

<!-- generated:begin roadmap:abandoned -->
| Feature | Superseded By | Rationale |
|---------|---------------|-----------|
<!-- generated:end roadmap:abandoned -->

## Completed

<!-- generated:begin roadmap:completed -->
| Feature | Completed Date | Evidence |
|---------|----------------|----------|
<!-- generated:end roadmap:completed -->
