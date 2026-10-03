# Feature Assembly Plan — F0003: PostgreSQL persistence

**Created:** 2026-10-02  
**Author:** Architect  
**Status:** Approved; G4/G5 validations passed; user supplied `approve-phase-b` on 2026-10-02  
**Planning run:** `2026-09-30-6632006b`

## Overview

F0003 establishes the shared PostgreSQL persistence contract and inventories every relation named by master-blueprint §78. It preserves the accepted F0001 PostgreSQL 18 and bitemporal proofs and the F0002 structural ownership contract. F0003 does not implement domain behavior or create future-phase tables ahead of their owning features. Each owner defines its table columns and migration in its own approved feature plan.

The §78 inventory below assigns one contract owner and delivery phase to each listed relation. “Introduced by” records existing migration provenance separately from the feature that owns the domain contract. Where an owner feature has not yet authored its PRD, §78 and the roadmap identify the inventory assignment; that owner must define the detailed schema before adding a migration.

## Governing contracts and reconciliation

- PostgreSQL is the sole authority for accepted relational state; graph and vector stores remain rebuildable projections (ADR-0002, ADR-0022, ADR-0023).
- Valid time and recorded time remain separate. PostgreSQL range and GiST constraints enforce non-overlap (ADR-0007, ADR-0008).
- Authoritative facts retain evidence or derivation lineage; correction and audit history remain append-only where specified (ADR-0010, ADR-0037).
- Tenant, workspace, and knowledge-base ownership follows F0002 and ADR-0030. F0003 does not change principals, grants, roles, permissions, or delegation policy.
- Original source bytes and immutable content bundles remain behind the provider-neutral artifact port (ADR-0003, ADR-0059).
- Existing F0001 migrations 0001–0004 and F0002 migrations 0005–0007 are the immutable starting history. New work is additive and chained from the accepted head; this plan reserves no revision number.

ADR-0064 through ADR-0069 remain Proposed. Their mentions in the inventory identify the feature expected to evaluate the storage contract; they do not accept those decisions or authorize behavior beyond the 2026-09-25 amendment's bounded v0.1 storage-field scope. ADR-0063 is accepted as direction; its v0.2B alignment execution remains owned by F0066.

There was no prior F0003 assembly plan to overwrite. The accepted F0002 design uses verified principals, current scoped grants, and policy configuration; current migrations do not create separate `role` or `permission` relations. §78 still inventories those names under F0002 for v0.1A. Their physical realization is an explicit owner reconciliation item: F0003 will not introduce those tables or alter F0002 policy as a shortcut. F0002's accepted contract and implementation remain authoritative until a separately approved architecture change resolves the representation.

## Persistence boundary

```text
Owning feature service
        │ authorized command / query
        ▼
engine application port and unit of work
        │ SQLAlchemy 2 repositories
        ▼
PostgreSQL 18 — authoritative rows, constraints, migrations
        │ transactional outbox
        └──► idempotent, rebuildable projections (AGE / pgvector / search)

ContentArtifactStore port ──► object-store adapter for immutable source bytes
```

- `engine/packages/brain-persistence/` owns SQLAlchemy mappings, sessions, repositories, and Alembic integration. Domain services own transaction intent and call persistence ports; model code does not absorb domain policy.
- Owner keys and parent keys travel together on persisted child and multi-parent rows. Composite foreign keys enforce the same tenant/workspace/knowledge-base boundary as F0002; a single-parent link may inherit ownership only when its parent FK makes that ownership unambiguous.
- Required canonical state, audit records, and outbox events commit in the owning operation's declared transaction. Projectors consume the outbox idempotently and never become authoritative.
- Bitemporal facts use PostgreSQL range types and the accepted two-range GiST exclusion rule. SQLite is not evidence for range, exclusion, or concurrency behavior.
- JSONB is reserved for contract-approved extension payloads. It does not replace relational identity, ownership, lineage, or temporal columns.
- Migrations use expand, explicit reconciliation/backfill, constraint enforcement, and documented forward repair when downgrade would lose data. Ambiguous owner/backfill rows stop for review; migrations do not infer owners, delete history, or widen access.
- No public API or new API/schema contract is introduced by F0003. API request/response contracts remain owned by the feature exposing the operation.

## Existing persistence baseline

The source migration audit found these §78 relations already present:

| Revision | Existing §78 relations |
|---|---|
| `0001_content_and_interpretation.py` | `source_document`, `document_version`, `content_artifact`, `semantic_interpretation_run`, `assertion`, `assertion_evidence` |
| `0002_principals_audit_and_review.py` | `audit_event`, `principal`, `membership`, `review_batch`, `review_item`, `review_decision` |
| `0003_fact_slots_and_commits.py` | `fact_slot`, `outbox_event`, `canonical_fact_version`, `canonical_fact_change` |
| `0005_tenancy_authx_expand.py` | `tenant`, `workspace`, `knowledge_base` |

Migration `0004` adds ingestion job state outside the §78 list. Revisions `0006` and `0007` tighten structural ownership and immutability for the F0002 substrate. The inventory retains this origin information; no existing table is represented as newly created by F0003.

## §78 ownership and delivery inventory

“Existing + additive” means preserve the cited migration and add only the owning feature's approved compatible revision. “Owner revision” means the named feature defines and adds the relation in its own approved release; F0003 does not create it. Every inventory entry is governed by §78 plus the named feature's PRD/approved story before migration.

| §78 relation(s) | Contract owner | Delivery phase | Source contract | Migration boundary |
|---|---|---|---|---|
| `tenant`, `workspace`, `knowledge_base`, `principal`, `membership`, `role`, `permission` | F0002 — Tenancy-aware domain kernel | v0.1A | F0002 approved PRD/assembly plan; ADR-0030, ADR-0061, ADR-0062 | Existing F0002 tables retain 0002/0005–0007 provenance. `role` and `permission` remain the explicit representation reconciliation above; no F0003 migration. |
| `source_document`, `document_version`, `content_artifact`, `content_block`, `content_table`, `content_table_cell` | F0004 — Content artifact model | v0.1A | §78; F0004 feature plan; ADR-0003, ADR-0004, ADR-0059 | Preserve the F0001 0001 source/document/artifact rows; F0004 owns compatible additive content-block/table relations and artifact metadata evolution. Bytes remain outside PostgreSQL. |
| `document_profile`, `document_classification_assertion` | F0014 — Document Profile model | v0.1A | §78; F0014 feature plan; ADR-0014 | Owner revision after F0014 defines versioning and classification lineage; no F0003 table creation. |
| `ontology`, `ontology_version`, `ontology_module`, `ontology_concept`, `ontology_property`, `ontology_relation`, `ontology_axiom`, `ontology_label`, `ontology_alias` | F0012 — Foundation ontology | v0.1A | §78; F0012 feature plan; ADR-0011, ADR-0012 | Owner revision after F0012 defines normalized runtime representation; F0013 contributes GL content through its own contract without taking schema ownership. |
| `extraction_profile`, `extraction_profile_module` | F0015 — Extraction Profile compiler | v0.1A | §78; F0015 feature plan; ADR-0015 | Owner revision after F0015 defines compiled-release persistence; authoring and workbench state remain with later owners. |
| `semantic_interpretation_run`, `time_mention`, `document_time_context`, `interpretation_drop` | F0016 — Semantic interpretation runs | v0.1A | F0001-S0003 for the existing run row; §78 and F0016 plan; ADR-0035; ADR-0064/0065 Proposed | Preserve `semantic_interpretation_run` from 0001; F0016 adds only storage fields authorized by the bounded amendment and its approved contract. |
| `assertion`, `assertion_value`, `assertion_relationship`, `assertion_evidence`, `assertion_qualifier` | F0006 — Assertion plane, origin, and interpretation basis | v0.1A | F0001-S0003/S0004 for existing assertion/evidence rows; §78 and F0006 plan; ADR-0010, ADR-0063 accepted as direction; ADR-0065 Proposed | Preserve 0001 assertion/evidence identity and lineage; F0006 owns only its approved v0.1 assertion and storage contract. |
| `typed_assertion_source`, `kind_word_binding`, `signature_binding`, `implication_rule`, `implication_rule_version`, `phrase_reading` | F0066 — Open-statement extraction and signature alignment | v0.2B | §78; F0066 plan; ADR-0063 accepted as direction; ADR-0068 Proposed | Owner revision only after F0066's Phase A/B contracts and proof gates; explicitly deferred from v0.1. |
| `entity`, `entity_type`, `entity_alias` | F0017 — Deterministic entity resolution | v0.1A | §78; F0017 plan; ADR-0025; ADR-0066 Proposed | Owner revision; F0002's `entity_identity` and `entity_knowledge_base` remain distinct existing tables and are not renamed to these §78 relations. |
| `fact_slot`, `fact_slot_qualifier` | F0007 — FactSlot model | v0.1A | F0001-S0005 for existing `fact_slot`; §78 and F0007 plan; ADR-0006 | Preserve `fact_slot` from 0003; owner adds only accepted qualifier shape. |
| `canonical_fact_version`, `canonical_relationship_version` | F0008 — Bitemporal canonical facts | v0.1A | F0001-S0005 and ADR-0007/0008 for existing fact versions; §78 and F0008 plan | Preserve `canonical_fact_version` from 0003 and its two-range constraint; relationship version rows are additive under F0008. |
| `canonical_fact_evidence`, `derivation`, `derivation_input` | F0009 — Provenance and human-correction lineage | v0.1A | §78; F0009 plan; ADR-0010, ADR-0037 | Owner revision; lineage references are required before any authoritative fact can be accepted. |
| `canonical_fact_change` | F0010 — Change and retraction semantics | v0.1A | F0001-S0005 for existing change rows; §78 and F0010 plan; ADR-0009, ADR-0037 | Preserve `canonical_fact_change` from 0003; F0010 owns compatible change/retraction extensions. |
| `learning_candidate`, `learning_evidence`, `knowledge_gap` | F0041 — Learning Plane | v0.2B | §78; F0041 plan; ADR-0020, ADR-0021 | Owner revision in v0.2B; no learning state is materialized in F0003. |
| `reasoning_pattern_candidate` | F0060 — Reasoning-pattern governance | v0.4+ | §78; F0060 plan; ADR-0027 and applicable accepted future decisions | Owner revision in v0.4+; candidate state is not v0.1 canonical truth. |
| `conversation`, `conversation_turn`, `conversation_feedback`, `conversation_context` | F0037 — Semantic Conversation Engine | v0.2A | §78; F0037 plan; ADR-0018, ADR-0019 | Owner revision in v0.2A; no conversation persistence in F0003. |
| `conversation_turn_citation`, `conversation_attachment` | F0038 — Chat with Document | v0.2A | §78; F0038 plan; ADR-0010, ADR-0018 | Owner revision in v0.2A; citations preserve existing evidence authority and document scope. |
| `conversation_knowledge_artifact`, `conversation_hypothesis`, `conversation_derivation` | F0042 — Knowledge promotion and governance | v0.2B | §78; F0042 plan; ADR-0019, ADR-0020, ADR-0021 | Owner revision after promotion states and lineage are defined; conversation artifacts do not become canonical facts by default. |
| `entity_merge`, `entity_merge_history` | F0027 — Probabilistic entity resolution | v0.2B | §78; F0027 plan; ADR-0025 | Owner revision in v0.2B; deterministic F0017 identity remains the v0.1 baseline. |
| `conflict` | F0028 — Conflict and supersession | v0.2B | §78; F0028 plan; ADR-0009 | Owner revision in v0.2B; v0.1 endorsement supersession remains with F0019/F0025. |
| `review_item`, `review_batch`, `review_decision`, `review_decision_evidence` | F0022 — Document 360 and native evidence review | v0.1B | F0001-S0004 for existing review rows; §78 and F0022 plan; ADR-0037, ADR-0057, ADR-0058 | Preserve review rows from 0002; F0022 owns evidence-panel and review-specific additive schema. |
| `process_type`, `process_instance`, `process_state_definition`, `process_transition_definition`, `process_event`, `process_constraint` | F0048 — Process domain model | v0.3 | §78; F0048 plan; ADR-0028, ADR-0029 | Owner revision in v0.3; process DSL and execution remain deferred. |
| `normative_constraint` | F0052 — Normative constraints | v0.3 | §78; F0052 plan; ADR-0027 | Owner revision in v0.3; no evaluation state is added by F0003. |
| `hypothetical_scenario` | F0053 — Hypothetical scenarios | v0.3 | §78; F0053 plan; ADR-0027 | Owner revision in v0.3; scenario state remains separate from canonical facts. |
| `decision`, `decision_input` | F0057 — Decision ledger | v0.4+ | §78; F0057 plan; ADR-0032 | Owner revision in v0.4+; replay and decision history remain deferred. |
| `automated_decision`, `automation_fuse` | F0043 — Generalized review queues and governance | v0.2B | §78; F0043 plan; ADR-0067 Proposed | Owner revision only after human-precedent and impact-gating requirements are accepted; no automated decision is activated in F0003. |
| `action_definition`, `action_attempt` | F0059 — Execution gate | v0.4+ | §78; F0059 plan; ADR-0069 Proposed | Owner revision in v0.4+ after action identity, dispatch, uncertain outcome, and recovery contracts are approved. |
| `embedding` | F0033 — pgvector retrieval | v0.2A | §78; F0033 plan; ADR-0023 | Owner revision in v0.2A; vectors remain a rebuildable retrieval projection. |
| `outbox_event` | F0001 — Repository and engineering foundation | Pre-build | F0001-S0005 accepted bitemporal proof; ADR-0002, ADR-0008, ADR-0009 | Preserve `outbox_event` from 0003 and its parent ownership; F0003 applies the shared transactional contract without taking over projection behavior. |

## Build and migration sequence

| Step | Story | Work and boundary | Exit evidence |
|---|---|---|---|
| 1 | F0003-S0001 | Reconcile the inventory above against §78, feature roadmap, F0001/F0002 migration history, and actual model declarations. Record any owner/representation question before proposing DDL. | Every §78 name appears exactly once with owner, phase, contract source, and migration boundary; F0002 `role`/`permission` representation is carried as an explicit reconciliation. |
| 2 | F0003-S0002 | Audit tenant/workspace/KB keys and child references across existing models. Preserve F0002's immutable-owner and composite-FK decisions. Add DDL only for a proved gap in F0003's shared boundary; domain-specific references wait for their owner. | PostgreSQL tests prove valid references persist, cross-owner references fail, and the failure leaves no partial dependent state. |
| 3 | F0003-S0003 | Verify range types, the same-slot two-range GiST exclusion, transaction boundaries for fact/audit/outbox, and idempotent outbox identity against the F0001 baseline. Keep service and projection semantics with F0008/F0018 and projection owners. | PostgreSQL 18 integration and concurrency evidence; rollback/failure injection; restart read and outbox idempotency evidence. |
| 4 | F0003-S0004 | Define compatible Alembic conventions and audit any F0003-owned schema evolution. Existing revisions remain immutable; backfills are explicit, digest/reconciliation bound where ownership changes, and failures stop without guessed data. | Clean-install and accepted-head upgrade converge; existing IDs/history survive; invalid backfill fails with actionable reconciliation. |
| 5 | All | Map each implementation acceptance criterion to test IDs and measured evidence. Update the inventory only through the owning approved feature contract and this trace. | Feature action validates PostgreSQL 18 and changed-code coverage ≥80%; QE, code, security, DevOps, and Architect signoffs are recorded. |

## Implementation files and contracts

Expected implementation touchpoints, subject to the feature action's source inspection:

- `engine/packages/brain-persistence/src/brain_persistence/models.py`, repositories, and session/unit-of-work helpers for shared persistence behavior.
- `engine/migrations/versions/` for additive revisions only; no revision is pre-numbered here.
- `engine/tests/integration/`, `engine/tests/security/`, and package tests for PostgreSQL-specific ownership, temporal, concurrency, atomicity, and migration cases.
- No public endpoint, OpenAPI change, runtime JSON Schema, or new ADR is needed by this plan. Existing accepted contracts already govern the required invariants; no Proposed ADR is accepted by this plan.

## Signoffs and implementation gate

Required signoffs are Quality Engineer, Code Reviewer, Security Reviewer, DevOps, and Architect. Security independently reviews tenant isolation and data boundaries; DevOps reviews migration deployment and restore behavior; QE owns PostgreSQL-specific proof. These are implementation signoffs, not Phase B approval. No runtime readiness or acceptance of future ADRs is implied.

The plan is eligible for `approve-phase-b` only after G4 compilation/drift succeeds and every ordered G5 exit command exits 0. User approval is recorded in the base run's `gate-decisions.md`.
