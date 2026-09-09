# Nebula Insurance Brain — Single Source of Truth Master Build Spec (Blueprint Prompt)

You are an AI development partner helping build Nebula Insurance Brain, a continuously evolving enterprise semantic system for commercial Property & Casualty insurance.
This document is the framework entry point and the ONLY source of truth for process, scope, and platform baselines. The full architecture baseline lives in [`architecture/master-blueprint.md`](architecture/master-blueprint.md) and is referenced by section number from here. Where the two disagree, this document wins for process and scope and the master blueprint wins for architectural intent until an ADR settles the difference.
If information is missing, ask questions or mark open decisions — do NOT invent business rules.

## 0) How we will work (Process + Roles)

We proceed in three explicit phases driven by the `nebula-agents` framework. Sessions are rooted in the sibling `nebula-agents/` checkout with `{PRODUCT_ROOT}` resolved to this repository. Stay within the current phase.

### Phase A — Product Manager Mode (PM/BA)
Goal: define product requirements per feature (personas, stories, acceptance criteria, screens) against the epic inventory in section 3.
Output: feature folders under `features/F####-{slug}/` with PRD, stories, STATUS, and GETTING-STARTED.

### Phase B — Architect/Tech Lead Mode (Dev/Arch)
Goal: confirm or refine the architecture baseline (section 4 and the master blueprint) per feature: assembly plan, ADR confirmations, API and schema contracts, kg-source bindings.
Output: `feature-assembly-plan.md`, ADRs under `architecture/decisions/`, contracts under `api/` and `schemas/`, kg-source shards.

### Phase C — Implementation Mode
Goal: implement vertical slices in `engine/`, `experience/`, and `neuron/` with tests, migrations, contracts, and evidence packages.
Output: production-quality code + tests + run instructions + a feature evidence package per run.

IMPORTANT RULES:

- Single source of truth for process and scope is THIS document; architectural intent is the master blueprint until superseded by an ADR.
- If a requirement is not written here or in an approved feature folder, do not implement it.
- If there is ambiguity, list questions and propose minimal default assumptions labeled clearly.
- No scope creep. Build only what is specified for the current phase and feature.
- Proposed decisions in the master blueprint (sections 106 to 122, ADR-0038 to ADR-0053) are not accepted until their stated tests, owners, and release gates are satisfied.

### Framework binding

- Framework: `nebula-agents` pinned at commit `c218bf1776f509a30f71967a1ee79879caa9a000` (2026-09-07). Advance the pin deliberately, in step with `.github/workflows/ci-gates.yml`, and record the new commit here.
- Session setup: export `NEBULA_PRODUCT_ROOT=<absolute path to this repo>` before running any framework script. The framework default points at the CRM repo, not this one.
- Layout convention: `engine/`, `experience/`, `neuron/` runtime roots (section 2.3). Path-class extensions for the additional roots are declared in section 2.4 and registered in `operations/evidence/README.md` at init.
- Local guidance: [agent instructions](../docs/agent-instructions.md) and [plan review checklist](../docs/plan-review-checklist.md), declared in `../.nebula-project.yaml`, supplement this blueprint without changing its authority.
- Extension rollout: complete. The pinned revision carries `agents/scripts/project_checks.py` and `agents/scripts/project_context.py`, so the checks declared in `../.nebula-project.yaml` execute at the framework's `plan-review` extension point; see [adoption status](../docs/framework-adoption.md).

### Tracker Governance (Mandatory)

Planning trackers must stay in sync at all times. Treat stale tracker state as a process defect.

- Governance contract: `features/TRACKER-GOVERNANCE.md`
- `features/REGISTRY.md`, `features/ROADMAP.md`, and the `knowledge-graph/` projections are compiled from `kg-source/**` shards by `scripts/kg/compile.py`; never hand-edit generated regions.
- Run the framework tracker and story validators against this repo before declaring any planning or feature gate complete.

---

## 1) Product Context

### 1.1 What we're building

Name: Nebula Insurance Brain

Domain: Commercial Property & Casualty insurance enterprise knowledge (policies, endorsements, loss runs, claims, submissions, broker and account relationships).

Purpose: Ingest enterprise information once at the content level, preserve evidence, represent what sources claim, resolve claims into a governed bitemporal canonical world model with versioned ontology and mandatory provenance, and expose that knowledge through 360 views, search, graph traversal, APIs, agents, and conversation while learning from every interaction under governance (master blueprint sections 0 to 2).

What it is not: a document archive, a vector database, a chat-with-PDF system, or a static knowledge graph (section 2).

### 1.2 Target users

Baseline derived from the master blueprint surfaces (sections 64 to 75); Phase A refines these into personas per feature.

- Insurance knowledge workers (underwriters, account and claims analysts) using Entity 360, Document 360, search, and contextual chat (sections 70 to 72)
- Human reviewers adjudicating low-confidence or corrected extractions in the Nebula Review Panel (sections 75, 111, 125)
- Ontology, profile, and knowledge-governance stewards approving promotions and releases (sections 42, 112; the workbenches are v0.2)
- Agents and integrations consuming the semantic API and MCP under verified principals and bounded delegation (sections 64, 68, 69)
- Platform operators and security administrators managing tenancy, principals, policy releases, and retention (sections 65, 66, 110)

External users (brokers or MGAs) are not in v0.1 scope unless a feature explicitly states otherwise.

### 1.3 Core entities (baseline)

Semantic kernel (sections 12 to 18, 78):

- Tenant, Workspace, KnowledgeBase (structural tenancy)
- Principal, Membership, Role, Permission, ResourceScope
- SourceDocument, DocumentVersion, ContentArtifact, ContentBlock, ContentTable
- DocumentProfile, ExtractionProfile, SemanticInterpretationRun, InterpretationBasis
- Assertion, AssertionValue, AssertionRelationship, AssertionEvidence
- Entity, EntityType, EntityAlias
- FactSlot, FactSlotQualifier, CanonicalFactVersion, CanonicalRelationshipVersion, CanonicalFactChange
- Derivation, DerivationInput
- GuidelineRuleVersion, AssessmentRecord (F0065 bounded v0.1B assessment; proposed contract in its feature folder)
- ReviewItem, ReviewBatch, ReviewDecision, EvidenceLocator
- LearningCandidate, LearningEvidence, KnowledgeGap
- Conversation, ConversationTurn, ConversationContext, ConversationKnowledgeArtifact
- AuditEvent, OutboxEvent

Insurance core for the v0.1 GL slice (sections 23, 24, 86):

- Account, Insured, Policy, PolicyTerm, Endorsement
- Coverage (CGL), CoverageForm, CoverageTrigger, Limit (EachOccurrence, GeneralAggregate, ProductsCompletedOperationsAggregate), Deductible/Retention

### 1.4 Critical workflows (baseline)

Ingestion and interpretation: Source Document → Parse Once (Docling) → Content Artifact → Classify → Extraction Profile → Assertions → Confidence/Review Policy → Deterministic Entity Resolution → Canonical Commit → FactSlots + Bitemporal Facts → Entity 360 (section 86)
Guideline assessment (v0.1B, F0065): accepted qualified facts + selected reviewed rule release + explicit time/snapshot → deterministic comparison → immutable assessment with exact lineage → authorized Entity 360 explanation (master blueprint section 124).
Human review: Assertion → ReviewItem → Nebula Review Panel → reviewer decision → ReviewDecision → corrected assertion or canonical commit → Golden Corpus (sections 75, 85, 125)
Endorsement supersession: Original fact → Endorsement (valid-time effective, recorded-time received) → superseded canonical version with both timelines queryable (sections 14 to 16, 87)
Knowledge promotion (v0.2): Conversation or learning candidate → validate and score → retain, review, or promote (sections 30 to 44)

Non-negotiables:

- Every document version is physically parsed once; reinterpretation never re-parses (ADR-0003, ADR-0016).
- No authoritative fact without evidence or derivation lineage (ADR-0010); corrections append and never rewrite evidence (ADR-0037).
- Canonical facts are fully bitemporal with database-level overlap integrity (ADR-0007, ADR-0008).
- Authorization is enforced during retrieval, commit, evidence access, graph traversal, and MCP, never after (section 66).
- Every canonical commit, review decision, and authorization decision is audited (sections 66, 89).

---

## 2) Technology and Platform (baseline decisions)

Locked unless changed by an accepted ADR (master blueprint section 3).

### 2.1 Stack

- Backend: Python 3.13+, FastAPI, Pydantic v2, SQLAlchemy 2, asyncpg, Alembic, uv; Temporal Python SDK from v0.3
- Data platform: PostgreSQL (authoritative) with JSONB, range and multirange types with btree_gist, full-text search, pgvector (retrieval projection), Apache AGE (graph projection); Qdrant optional and deferred (ADR-0033)
- Direct specialist dependencies: Docling (content extraction), Docling-Graph (semantic and graph extraction). Human evidence adjudication is native (ADR-0057, section 125); `pdf.js` and `fflate` are Review Panel rendering libraries in `experience/`, not specialist engines
- Frontend: React, TypeScript, Vite, React Router, TanStack Query, Zustand, React Hook Form, AJV with JSON Schema 2020-12, shadcn/ui, Tailwind CSS, TanStack Table, Cytoscape.js (v0.2), react-i18next
- AuthN: authentik OIDC. AuthZ: native Casbin adapter behind an AuthorizationService with typed resource scopes. Session transport: same-origin BFF with server-held tokens is the proposed direction (ADR-0051, open)
- Semantic interchange: JSON Schema 2020-12, JSON-LD, RDF and N-Triples, OWL, RDFS, SKOS, OKF, YAML, JSONL (authoring and interchange only, never runtime truth)
- Deploy: Docker + docker-compose for local development; the production host is an open decision (section 117.1). Clarification decisions recorded at F0001 G1 (2026-09-06): PostgreSQL 18 is the pinned major for the pgvector and Apache AGE build (fallback 17 only on build failure); the review surface is the native Nebula Review Panel (ADR-0057, 2026-09-08); the F0001 proofs use `microsoft/Phi-4-mini-instruct` served by vLLM as an OpenAI-compatible service on the host GPU (the local profile the CRM validated in nebula-insurance-crm ADR-035; 4,096-token context, bearer auth, no prompt persistence) and run in local Docker Compose
- Testing: pytest for `engine/` and `neuron/` (unit, integration, evaluation against the Golden Corpus). Frontend stack proposed as Vitest + Playwright + axe following the CRM baseline, to be confirmed in Phase B. Cross-cutting scans per the framework evidence contract (dependency, secrets, SAST, DAST)

### 2.2 Contract locations

- OpenAPI: `api/brain-api.yaml` (semantic API, section 68). MCP tool surface documented in `api/brain-mcp.yaml` (section 69)
- Design-time shared JSON Schemas: `schemas/` under this planning tree. Runtime canonical and generated schemas live in the repository root `schemas/` tree (ADR-0013)
- Python package prefix: `brain_` (for example `brain_domain`, `brain_extraction`). Distribution directories keep the hyphenated `brain-*` names from master blueprint section 77

### 2.3 Repository layout and role ownership

Three runtime roots follow the framework convention; master blueprint section 77 holds the full tree.

| Root | Contents | Owning role | Notes |
|------|----------|-------------|-------|
| `engine/` | FastAPI API, worker, and the semantic kernel packages: domain, persistence, content, schema, ontology, graph, temporal, process, provenance, resolution (deterministic), search, decisions, governance, review, security; Alembic migrations; backend tests | backend-developer | Business logic and canonical truth live here |
| `neuron/` | AI and semantic runtime packages: ingestion (Docling adapter), extraction (Docling-Graph, extraction profiles), interpretation, reasoning, conversation, learning, evolution, agent-tools (MCP); AI tests | ai-engineer | Proposes assertions and candidates; never writes canonical truth directly (ADR-0001, section 64) |
| `experience/` | React web app: 360 views, search, evidence, chat, graph explorer | frontend-developer | Semantic-first; chat is one modality (ADR-0036) |
| `ontology/`, `profiles/`, `schemas/`, `knowledge-packs/` | Authored ontology modules, document and extraction profiles, runtime JSON Schemas, OKF packs | architect (design), backend-developer (compiler and runtime loading) | Versioned, modular, compiled into normalized runtime structures (ADR-0011, ADR-0012) |
| `golden-corpus/` | Version-controlled regression fixtures exported from Nebula review decisions | quality-engineer | Section 96; frozen holdout rules in section 115.1 |
| `scripts/kg/` | Product-owned knowledge-graph toolchain | architect | Copied from the framework; `.mcp.json` exposes it over MCP |

Boundary rules:

- Shared semantics (entities, FactSlots, ontology, schemas, policies) change only through the architect and kg-source shards.
- `neuron/` writes assertions, candidates, and review items through engine commit services under the acting principal; it has no direct canonical SQL write path (sections 64, 69).
- Frontend consumes contracts from `api/` and `schemas/`; it never embeds business rules.

### 2.4 Path-class extensions (register at init)

The framework defaults cover `engine/**` and `experience/**`. Register these additive extensions in `operations/evidence/README.md`:

| Path class (glob) | Forces |
|-------------------|--------|
| `neuron/**` excluding test-only subtrees | `runtime_bearing = true` |
| `neuron/**/migrations/**` | `runtime_bearing = true` and `deployment_config_changed = true` |
| `ontology/**`, `profiles/**`, `schemas/**`, `knowledge-packs/**` | `runtime_bearing = true` |
| `golden-corpus/**` | `runtime_bearing = true` |
| `**/brain_security/**`, `**/brain-security/**`, `**/auth/**`, `**/authz/**`, `**/identity/**`, `**/principals/**` | `security_sensitive_scope = true` (Python paths are lowercase; the framework defaults match capitalized names only) |

Architecture constraints:

- Clean architecture inside `engine/`: domain → application → infrastructure → api; application depends on repository interfaces.
- Canonical commit is transactional with audit and outbox in one boundary; projections (AGE, pgvector, FTS) are rebuildable and never authoritative (ADR-0002, ADR-0022, ADR-0023, proposed ADR-0041).
- Assertions, review decisions, audit events, and canonical fact versions are append-only.
- Tenant and knowledge-base identifiers are structural on every authoritative row (ADR-0030).
- API error contract must be consistent across all services (ProblemDetails pattern; confirm in Phase B).

---

## 3) Phase A — Product Manager Spec

Status: epic inventory established; personas, stories, and screens are authored per feature by the plan action.

### 3.1 Vision & Non-goals

Vision: master blueprint sections 0 and 103. Non-goals: section 2 and the v0.1 exclusions in section 89.

### 3.2 Personas

Derived per feature from section 1.2 of this document; persona files land in `examples/personas/` and feature PRDs.

Engineering personas established by F0001 Phase A (2026-09-06):

- Dana the Platform Engineer — `examples/personas/platform-engineer.md`
- Mateo the Document Intelligence Engineer — `examples/personas/document-intelligence-engineer.md`
- Ingrid the Persistence Engineer — `examples/personas/persistence-engineer.md`
- Rosa the Business Reviewer — `examples/personas/business-reviewer.md`

End-user personas established by F0065 Phase A (2026-09-07), ahead of F0021 to F0023, because F0065 was
planned first and its stories are written against them:

- Priya the GL Underwriter — `examples/personas/gl-underwriter.md`
- Sameer the Domain Steward — `examples/personas/domain-steward.md`

Remaining end-user personas (analysts, and any further steward or governance roles) are authored with the
first user-facing features, F0021 to F0023.

### 3.3 Epics & Features

The runtime epic inventory is the master blueprint section 95 roadmap (original F0001 to F0063, plus F0065), sequenced per sections 115.3 and 124. F0064 tracks repository tooling separately. The authoritative registry is `features/REGISTRY.md` and the sequencing view is `features/ROADMAP.md`, both generated from `kg-source/features/**`. The original 63 runtime features retain their identifiers and stages. F0065 adds a bounded neurosymbolic assessment in v0.1B under the user-authorized 2026-09-07 amendment; its draft architecture remains subject to proof and review. Story links are appended by the plan action as each feature is planned.

**Pre-build (Now)**

- [F0001 — Repository and engineering foundation](features/F0001-repository-and-engineering-foundation/README.md) - Plan approved 2026-09-06 (Phase A and B); ready for the feature action
  - [F0001-S0001](features/F0001-repository-and-engineering-foundation/F0001-S0001-runtime-roots-and-toolchain-skeleton.md) - Not Started
  - [F0001-S0002](features/F0001-repository-and-engineering-foundation/F0001-S0002-local-runtime-containers-and-dependency-matrix.md) - Not Started
  - [F0001-S0003](features/F0001-repository-and-engineering-foundation/F0001-S0003-proof-parse-once-reinterpret-evidence.md) - Not Started
  - [F0001-S0004](features/F0001-repository-and-engineering-foundation/F0001-S0004-proof-native-review-round-trip.md) - Not Started
  - [F0001-S0005](features/F0001-repository-and-engineering-foundation/F0001-S0005-proof-bitemporal-commit.md) - Not Started
  - [F0001-S0006](features/F0001-repository-and-engineering-foundation/F0001-S0006-proof-access-boundaries-extension-build-and-restore.md) - Not Started
  - [F0001-S0007](features/F0001-repository-and-engineering-foundation/F0001-S0007-record-proof-outcomes-and-settle-contracts.md) - Not Started

**v0.1A (Next)**

- [F0002 — Tenancy-aware domain kernel + verified stable principal and scope contracts](features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/README.md) - Planned
- [F0003 — PostgreSQL persistence](features/F0003-postgresql-persistence/README.md) - Planned
- [F0004 — Content artifact model](features/F0004-content-artifact-model/README.md) - Planned
- [F0005 — One-time Docling ingestion](features/F0005-one-time-docling-ingestion/README.md) - Planned
- [F0006 — Assertion plane + origin + interpretation basis](features/F0006-assertion-plane-origin-and-interpretation-basis/README.md) - Planned
- [F0007 — FactSlot model](features/F0007-factslot-model/README.md) - Planned
- [F0008 — Bitemporal canonical facts](features/F0008-bitemporal-canonical-facts/README.md) - Planned
- [F0009 — Provenance + human-correction lineage](features/F0009-provenance-and-human-correction-lineage/README.md) - Planned
- [F0010 — Change/retraction semantics](features/F0010-change-and-retraction-semantics/README.md) - Planned
- [F0011 — JSON Schema contract system](features/F0011-json-schema-contract-system/README.md) - Planned
- [F0012 — Foundation ontology](features/F0012-foundation-ontology/README.md) - Planned
- [F0013 — Insurance Core GL ontology](features/F0013-insurance-core-gl-ontology/README.md) - Planned
- [F0014 — Document Profile model](features/F0014-document-profile-model/README.md) - Planned
- [F0015 — Extraction Profile compiler](features/F0015-extraction-profile-compiler/README.md) - Planned
- [F0016 — Semantic interpretation runs](features/F0016-semantic-interpretation-runs/README.md) - Planned
- [F0017 — Deterministic entity resolution](features/F0017-deterministic-entity-resolution/README.md) - Planned

**v0.1B (Later)**

- [F0018 — Canonical commit service + action authorization and policy-version audit](features/F0018-canonical-commit-service-and-action-authorization/README.md) - Planned
- [F0019 — Basic endorsement supersession](features/F0019-basic-endorsement-supersession/README.md) - Planned
- [F0020 — Minimal graph/temporal query API](features/F0020-minimal-graph-and-temporal-query-api/README.md) - Planned
- [F0021 — Native React semantic shell + OIDC/session contract and safe re-auth behavior](features/F0021-native-react-semantic-shell-and-oidc-session/README.md) - Planned
- [F0022 — Document 360 + native evidence review panel + parent/classification and reviewer authority](features/F0022-document-360-and-native-evidence-review/README.md) - Planned
- [F0023 — Minimal Entity 360](features/F0023-minimal-entity-360/README.md) - Planned
- [F0065 — Grounded GL guideline assessment](features/F0065-grounded-gl-guideline-assessment/README.md) - Planned (six stories and draft contracts authored; review and implementation pending)
  - [F0065-S0001](features/F0065-grounded-gl-guideline-assessment/F0065-S0001-versioned-guideline-rule.md) - Not Started
  - [F0065-S0002](features/F0065-grounded-gl-guideline-assessment/F0065-S0002-evaluate-accepted-facts.md) - Not Started
  - [F0065-S0003](features/F0065-grounded-gl-guideline-assessment/F0065-S0003-preserve-assessment-lineage.md) - Not Started
  - [F0065-S0004](features/F0065-grounded-gl-guideline-assessment/F0065-S0004-temporal-reassessment.md) - Not Started
  - [F0065-S0005](features/F0065-grounded-gl-guideline-assessment/F0065-S0005-explain-assessment-in-entity-360.md) - Not Started
  - [F0065-S0006](features/F0065-grounded-gl-guideline-assessment/F0065-S0006-reproducible-worked-examples.md) - Not Started
- [F0024 — GL vertical slice](features/F0024-gl-vertical-slice/README.md) - Planned
- [F0025 — Endorsement bitemporal slice](features/F0025-endorsement-bitemporal-slice/README.md) - Planned

**v0.1C (Later)**

- [F0026 — v0.1 hardening + Golden Corpus workflow + AuthX negative tests and policy parity](features/F0026-v0-1-hardening-golden-corpus-and-authx-tests/README.md) - Planned

**v0.2A (Later)**

- [F0033 — pgvector retrieval](features/F0033-pgvector-retrieval/README.md) - Planned
- [F0034 — AGE graph projection](features/F0034-age-graph-projection/README.md) - Planned
- [F0035 — Hybrid search + consistent authorized rows/counts/facets/graph scope](features/F0035-hybrid-search-and-authorized-scope/README.md) - Planned
- [F0036 — Evidence-aware retrieval / grounded generation](features/F0036-evidence-aware-retrieval-and-grounded-generation/README.md) - Planned
- [F0037 — Native Semantic Conversation Engine + Onyx-inspired Chat mechanics](features/F0037-native-semantic-conversation-engine/README.md) - Planned
- [F0038 — Chat with Document](features/F0038-chat-with-document/README.md) - Planned
- [F0039 — Chat with Entity](features/F0039-chat-with-entity/README.md) - Planned
- [F0040 — Conversation Graph](features/F0040-conversation-graph/README.md) - Planned
- [F0044 — Expanded Entity 360](features/F0044-expanded-entity-360/README.md) - Planned
- [F0045 — Cytoscape Graph Explorer](features/F0045-cytoscape-graph-explorer/README.md) - Planned
- [F0046 — Semantic API](features/F0046-semantic-api/README.md) - Planned
- [F0047 — Read-only MCP + verified principal, bounded delegation, and evidence access](features/F0047-read-only-mcp-and-bounded-delegation/README.md) - Planned

**v0.2B (Later)**

- [F0027 — Probabilistic entity resolution](features/F0027-probabilistic-entity-resolution/README.md) - Planned
- [F0028 — Conflict and supersession](features/F0028-conflict-and-supersession/README.md) - Planned
- [F0029 — Ontology discovery](features/F0029-ontology-discovery/README.md) - Planned
- [F0030 — Ontology Workbench](features/F0030-ontology-workbench/README.md) - Planned
- [F0031 — Document/Extraction Profile Workbench](features/F0031-document-and-extraction-profile-workbench/README.md) - Planned
- [F0032 — Knowledge Evolution Engine](features/F0032-knowledge-evolution-engine/README.md) - Planned
- [F0041 — Learning Plane](features/F0041-learning-plane/README.md) - Planned
- [F0042 — Knowledge promotion/governance](features/F0042-knowledge-promotion-and-governance/README.md) - Planned
- [F0043 — Generalized review queues / governance](features/F0043-generalized-review-queues-and-governance/README.md) - Planned

**v0.3 (Later)**

- [F0048 — Process domain model](features/F0048-process-domain-model/README.md) - Planned
- [F0049 — Canonical Transition Service](features/F0049-canonical-transition-service/README.md) - Planned
- [F0050 — Temporal.io](features/F0050-temporal-io/README.md) - Planned
- [F0051 — Process Workbench](features/F0051-process-workbench/README.md) - Planned
- [F0052 — Normative constraints](features/F0052-normative-constraints/README.md) - Planned
- [F0053 — Hypothetical scenarios](features/F0053-hypothetical-scenarios/README.md) - Planned
- [F0054 — Process reconciliation](features/F0054-process-reconciliation/README.md) - Planned

**v0.4+ (Later)**

- [F0055 — Native reasoning](features/F0055-native-reasoning/README.md) - Planned
- [F0056 — Derived dependency invalidation](features/F0056-derived-dependency-invalidation/README.md) - Planned
- [F0057 — Decision ledger](features/F0057-decision-ledger/README.md) - Planned
- [F0058 — Historical decision replay](features/F0058-historical-decision-replay/README.md) - Planned
- [F0059 — Execution gate](features/F0059-execution-gate/README.md) - Planned
- [F0060 — Reasoning-pattern governance](features/F0060-reasoning-pattern-governance/README.md) - Planned
- [F0061 — Advanced retrieval](features/F0061-advanced-retrieval/README.md) - Planned
- [F0062 — Advanced reasoners](features/F0062-advanced-reasoners/README.md) - Planned
- [F0063 — Future DSL](features/F0063-future-dsl/README.md) - Planned

### 3.4 MVP User Stories

Authored per feature in `features/F####-{slug}/F####-S####-{slug}.md`. The v0.1 acceptance questions in sections 86 and 87 are the minimum story set for F0024 and F0025. F0001 carries seven stories: toolchain skeleton, local containers and dependency matrix, the four section 115.4 proofs, and contract settlement (see section 3.3).

### 3.4.1 Examples as acceptance artifacts

Every new or changed semantic concept needs a definition, worked example, boundary case, and owning feature/story/contract links. Start with [EX-GL-001](examples/neurosymbolic-gl/README.md) and the [coverage map](examples/README.md). Structured examples validate against declared local schemas; runtime stories must later reproduce observed outcomes. Synthetic examples, observed proof evidence, and independent frozen evaluation data remain explicitly distinguished. F0065 carries six unstarted stories; its drafted examples do not constitute runtime delivery.

### 3.5 Screen Specifications

Minimal Entity 360 and Document 360 (sections 70, 71) and the constrained chat surface (section 72) are the v0.1 screens; specs land in `screens/` during Phase A of their features. F0065 S0005 extends Entity 360 with the bounded guideline assessment panel specified in its PRD; it introduces no standalone workbench.

---

## 4) Phase B — Architect Spec

Status: the architecture baseline exists in the master blueprint; each subsection below summarizes it and points to the authoritative sections. Per-feature Phase B produces assembly plans, contract files, and ADR confirmations.

### 4.1 Service Boundaries

Eight architectural planes (section 4) implemented as a modular monolith across `engine/` (semantic kernel, commit services, governance, review, search, security), `neuron/` (interpretation, conversation, learning, agent tools), and `experience/` (native semantic UX, including the Review Panel), with Docling, Docling-Graph, PostgreSQL extensions, and Temporal as engines around the semantic core (ADR-0001 as amended by ADR-0057, sections 100 and 125). The deployable topology and dependency matrix are a P0 pre-build requirement (section 106.2).

### 4.2 Data Model

PostgreSQL is authoritative (ADR-0002). Kernel entities: Tenant, Workspace, KnowledgeBase, Principal, SourceDocument, DocumentVersion, ContentArtifact, ContentBlock, DocumentProfile, ExtractionProfile, SemanticInterpretationRun, Assertion, Entity, FactSlot, CanonicalFactVersion, CanonicalRelationshipVersion, Derivation, ReviewItem, ReviewDecision, LearningCandidate, Conversation, AuditEvent, OutboxEvent (definitions in `domain/glossary.md`). Core tables are listed in section 78 and mirrored in `architecture/data-model.md`; AGE labels in section 79; content artifact layout in sections 80 and 81. Every authoritative row carries `tenant_id`, `knowledge_base_id`, and audit fields (`created_at`, `recorded_at`, actor). FactSlot identity (section 13), bitemporal fact versions (section 14), and change semantics (section 16) define canonical truth.

### 4.3 Workflow Rules

Ingestion and interpretation (section 86), the human review round trip (section 75), endorsement supersession (section 87), and knowledge promotion (section 42) are the baseline workflows; every state transition is an append-only canonical commit or review decision. Process semantics and Temporal execution are v0.3 (sections 59 to 62, ADR-0028).

### 4.4 Authorization Model

Verified `(issuer, subject)` mapped to a stable internal principal; typed resource and action policies evaluated through a native Casbin adapter; tenant and knowledge-base membership resolved separately from resource scope; enforcement at API, commit, search, vector, graph, evidence, ontology, conversation context, MCP, and execution gate; user, service, and agent principals distinct with bounded delegation; every authorization decision audited with policy version (sections 66, 118 to 120; proposed ADR-0049 to ADR-0053).

### 4.5 API Contracts

Semantic REST API surface in section 68 (`GET` and `POST` over `/entities`, `/assertions`, `/facts`, `/relationships`, `/documents`, `/content`, `/ontology`, `/search`, `/graph`, `/evidence`, `/history`, `/conversations`, `/learning`, `/reviews`), and read-first MCP tools in section 69. OpenAPI lives in `api/brain-api.yaml` and is authored per feature.

### 4.6 Non-Functional Requirements

Performance, availability, scalability, and security targets are proposed gates in sections 114.2 and 115.2 and require baseline measurement and named owners before acceptance: extraction reuse with zero re-parse, evidence fidelity for every citation, temporal integrity under concurrent commits, zero unauthorized content in the isolation suite, ingestion recovery without duplicate effects, timed restore drills, and measured field precision and recall, latency, and cost on the frozen slice. Latency budgets are expressed in milliseconds per surface once measured.

### 4.7 Architecture Artifacts

- `architecture/master-blueprint.md` — full baseline
- `architecture/decisions/` — ADR-0001 to ADR-0056 (Accepted baseline and Proposed; ADR-0056 records the bounded v0.1 assessment)
- `architecture/data-model.md` — tables, graph labels, artifact layout
- `architecture/SOLUTION-PATTERNS.md` — project conventions (seeded at F0001 Phase B)
- `architecture/c4-context.md`, `architecture/c4-container.md` — C4 L1 and L2 (Mermaid; ASCII companion in ADR-0054)
- `api/brain-api.yaml` — OpenAPI 3.1 (F0001 scope: health, protected reads, webhook, commit)
- `schemas/*.schema.json` — shared JSON Schemas (manifest, interpretation result, review decision, commit request and response, problem details); `semantic-example.schema.json` is explicitly an educational fixture contract, not a runtime DTO
- `security/policies/` — Casbin model and policy; `security/` — AuthX contract and pending security artifacts
- `testing/evaluation-strategy.md` — Golden Corpus, metrics, regression suites, release gates

### 4.8 Open decisions

Section 117.1 lists the decisions the implementation team still owes: source-authority owner, tenant and knowledge-base identity scope, host and extension build, Docling-Graph pin, licensed corpus and reviewers, acceptance thresholds and budgets, retention and deletion behavior. F0001 G1 (2026-09-06) answered the extension build (PostgreSQL 18) and the proof model policy (self-hosted), and ADR-0057 (2026-09-08) settled the review surface; the production host, the Docling-Graph pin, and the corpus source remain open.

### 4.9 F0001 Phase B (2026-09-06)

Assembly plan: `features/F0001-repository-and-engineering-foundation/feature-assembly-plan.md` (eight steps). New decisions: ADR-0054 (runtime roots and local topology) and ADR-0055 (Phi-4-mini-instruct on vLLM). Contracts authored: `api/brain-api.yaml`, six schemas, Casbin model and policy for the proof roles TenantMember, Reviewer, ServicePrincipal. Knowledge graph: ten capabilities, ten entities, three workflows, six endpoints, three roles, five policy rules bound to F0001; code bindings follow at feature G7.

---

## 5) Phase C — Implementation Plan (locked order)

Sequence per master blueprint sections 115.3 and 124; original identifiers F0001 to F0063 are preserved. F0065 is the bounded v0.1 assessment addition; F0064 is repository tooling.

1. Pre-build contract proofs as stories of F0001: parse, reinterpret, and evidence; native review round trip and evidence anchoring; bitemporal commit; access and hosting (section 115.4)
2. v0.1A — F0002 to F0017: typed domain contracts, durable ingestion, immutable evidence, assertion extraction
3. v0.1B — F0018 to F0023 establish authorized commits, temporal reads, evidence review, and minimal 360 views; F0065 adds bounded on-demand GL guideline assessment; F0024/F0025 prove real interpretation-to-assessment and temporal reassessment end to end
4. v0.1C — F0026 plus narrow acceptance coverage from F0036 to F0039: recovery, deletion and revocation minimum, audit, independent frozen evaluation, constrained policy question, and F0065 assessment/lineage/freshness/access challenge cases
5. v0.2A — F0033 to F0040 and F0044 to F0047; v0.2B — F0027 to F0032 and F0041 to F0043
6. v0.3 and later — F0048 to F0063: full process, generalized reasoning, automatic derivation propagation, decision replay, and advanced semantics; F0065 is already in v0.1B

Baseline authenticated writes, approval checks, source restrictions, and audit are v0.1 obligations even though the full Execution Gate and Decision Ledger come later (section 89).

---

## 6) Next Step Guidance

Init completed on 2026-09-05 (run `2026-09-05-6823e66e`, gates I0 to I6 green; evidence under `operations/evidence/runs/`).

1. Seed `kg-source/features/F0001.yaml` to `F0026.yaml` as planned from section 95 and ADR node shards from `architecture/decisions/`, then run `python3 scripts/kg/compile.py` and `python3 scripts/run-lifecycle-gates.py`.
2. Run the `plan` action for F0001 (the four section 115.4 pre-build proofs as its stories), then the `feature` action for F0001.
3. Activate the local KG hook once per clone: `git config core.hooksPath .githooks`.
