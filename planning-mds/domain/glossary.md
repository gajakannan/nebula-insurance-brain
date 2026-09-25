# Nebula Insurance Brain — Domain Glossary

Essential terminology for Nebula Insurance Brain product specifications. Definitions are sourced from `../architecture/master-blueprint.md` (section numbers in parentheses) and are refined per feature during Phase A and Phase B.

## Purpose

This glossary keeps the semantic kernel vocabulary and the insurance vocabulary consistent across requirements, architecture, code, and the knowledge graph, and lets agents understand domain concepts without inventing definitions.

**Rule:** If a term is not in this glossary and its meaning is unclear, ASK rather than assume.

---

## Semantic Kernel Entities

### Tenant
**Type:** Entity
**Definition:** The top of the structural tenancy hierarchy (Tenant → Workspace → KnowledgeBase); every authoritative semantic row carries `tenant_id` (65, ADR-0030)
**In the Brain:** Resolved from verified identity and trusted grants, never from request filters

### Workspace
**Type:** Entity
**Definition:** A tenant-scoped grouping of knowledge bases (65)

### Knowledge Base
**Type:** Entity
**Definition:** The unit of knowledge ownership under a workspace; every authoritative row carries `knowledge_base_id` and retrieval, graph traversal, and commits are scoped to it (65, 66)

### Principal
**Type:** Entity
**Definition:** A verified identity acting on the Brain: UserPrincipal, ServicePrincipal, or AgentPrincipal, mapped from `(issuer, subject)` to a stable internal id (66, ADR-0049)
**In the Brain:** Agents acting for a user carry both identities and a bounded, expiring delegation

### Source Document
**Type:** Entity
**Definition:** An original file or system record received by the Brain; versioned, immutable, preserved as evidence (5, 6, 18)

### Document Version
**Type:** Entity
**Definition:** One received version of a source document; the identity that content extraction happens against exactly once (6, ADR-0003, ADR-0004)

### Content Artifact
**Type:** Entity
**Definition:** The immutable parse-once output for a document version, produced by Docling underneath the planned Docling-Graph pipeline (ADR-0060): normalized text, blocks, tables, coordinates, and a manifest with parser identity and hashes (5, 80, 81)
**In the Brain:** Reinterpretation always reads the persisted artifact and never re-parses the source

### Content Block
**Type:** Entity
**Definition:** An addressable unit of a content artifact (paragraph, table cell, heading) with page coordinates, bounding box, and character offsets; the target of evidence locators (5, 18)

### Document Profile
**Type:** Entity
**Definition:** Declares a document's type plus business context and selects which ontology modules and extraction profiles apply (7, ADR-0014)

### Extraction Profile
**Type:** Entity
**Definition:** A composable specification of what to extract for a document profile, built from a shared base plus line-of-business or product extensions (8, ADR-0015)

### Semantic Interpretation Run
**Type:** Entity
**Definition:** A versioned execution of interpretation over persisted content that produces assertions; many runs may target one content artifact (28, 29, ADR-0016)

### Interpretation Basis
**Type:** Entity
**Definition:** How directly evidence supports an interpretation: `EXPLICIT`, `INFERRED`, or `AMBIGUOUS`; independent of fact mode (ADR-0035)

### Assertion
**Type:** Entity
**Definition:** What a source, system, model, or person claims, with its evidence; never truth by itself (11, ADR-0005)

### Entity
**Type:** Entity
**Definition:** A canonical resolved thing in the world model such as an account, policy, coverage, location, or claim (12, 53)

### FactSlot
**Type:** Entity
**Definition:** The canonical semantic identity of one fact about an entity, for example the EachOccurrence limit of a coverage; the unit that fact versions attach to (13, ADR-0006)

### Canonical Fact Version
**Type:** Entity
**Definition:** An accepted value for a FactSlot carrying both a valid-time period and a recorded-time period, with change semantics when it ends (14, 16, ADR-0007, ADR-0009)

### Canonical Relationship Version
**Type:** Entity
**Definition:** A bitemporal accepted relationship between two entities (14, 15)

### Derivation
**Type:** Entity
**Definition:** The lineage of a derived fact to the exact input fact versions it depends on, enabling invalidation when inputs change (55, 56, ADR-0026)

### Review Item
**Type:** Entity
**Definition:** A Nebula-owned unit of human adjudication (low-confidence assertion, extraction, provenance, entity, or relationship correction) routed to the Nebula Review Panel (75, 125, ADR-0057)

### Review Batch
**Type:** Entity
**Definition:** The set of review items a reviewer is shown together, typically the fields of one submission package across its artifacts; submitted in one transaction (125, ADR-0057)

### Review Panel
**Type:** Term
**Definition:** Nebula's native evidence review surface: renders the immutable content artifact per content type, anchors each assertion in its source region at a declared precision, and submits governed decisions (111, 125, ADR-0057)

### Review Decision
**Type:** Entity
**Definition:** The governed outcome of human review (`ACCEPT`, `CORRECT`, `REJECT`) with correction lineage; corrections append and never rewrite evidence. `BLOCKED` records that evidence could not be anchored and is not an adjudication (75, 125, ADR-0037, ADR-0058)

### Evidence Locator
**Type:** Entity
**Definition:** The stored target that binds an assertion to its source region: W3C Web Annotation selectors per content type plus the declared precision, with `unresolved` a valid value (108.2, 125, ADR-0058)

### Evidence Precision
**Type:** Term
**Definition:** How exactly an assertion is grounded — `exact-span`, `table-cell`, `block`, `page`, `document`, or `unresolved` — declared rather than inferred, and rendered as claimed (108.2, 125, ADR-0058)

### Learning Candidate
**Type:** Entity
**Definition:** A proposed concept, pattern, relationship, rule, or gap discovered by the Brain or a conversation, held outside canonical truth until governed promotion (31 to 35, ADR-0020, ADR-0021)

### Conversation
**Type:** Entity
**Definition:** A scoped chat rooted on an explicit object (document, entity, account, policy, claim) whose turns may produce candidates but never canonical facts by default (36 to 44, ADR-0018, ADR-0019)

### Audit Event
**Type:** Entity
**Definition:** Append-only record of canonical commits, review decisions, and authorization decisions, including policy version and actor (66, 78)

### Outbox Event
**Type:** Entity
**Definition:** Transactional outbox record emitted with a canonical commit so projections (AGE, pgvector, FTS) rebuild consistently (78, proposed ADR-0041)

## Insurance Core Entities (v0.1 General Liability slice)

### Account
**Type:** Entity
**Definition:** The business entity seeking or holding insurance coverage; the root of Entity 360 (70, 86)

### Insured
**Type:** Entity
**Definition:** The named party covered by a policy; distinct from the account when a package covers several named insureds (86)

### Policy
**Type:** Entity
**Definition:** An insurance contract identified by a scoped policy number with one or more policy terms (86, 107.3)

### Policy Term
**Type:** Entity
**Definition:** The valid-time period of a policy; endorsements change facts within a term effective from a date that may precede their receipt (86, 87)

### Endorsement
**Type:** Entity
**Definition:** A document that changes policy facts with a valid-time effective date; the canonical example of bitemporal supersession (87, ADR-0007)

### Coverage
**Type:** Entity
**Definition:** A coverage part of a policy, for example Commercial General Liability, with its form, trigger, limits, and deductible or retention as FactSlots (24, 86)

### Coverage Form
**Type:** Entity
**Definition:** The standard or manuscript form that defines a coverage's terms (24, 86)

### Limit
**Type:** Entity
**Definition:** A typed monetary value with a limit basis, for example EachOccurrence, GeneralAggregate, or ProductsCompletedOperationsAggregate (24, 86, 107.3)

### Deductible
**Type:** Entity
**Definition:** The retained amount per claim or occurrence, recorded with its basis where present in the policy (86, 107.3)

## Terms

### Valid Time
**Type:** Term
**Definition:** When a fact is true in the world (14)

### Recorded Time
**Type:** Term
**Definition:** When the Brain accepted a fact as known; distinct from receipt and assertion timestamps (14, 116.1)

### Fact Mode
**Type:** Term
**Definition:** `ASSERTED`, `OBSERVED`, or `DERIVED`; what kind of knowledge a fact represents (ADR-0027, ADR-0035)

### Parse Once
**Type:** Term
**Definition:** Each document version is physically parsed exactly once; all later semantic work operates on the persisted content artifact (5, ADR-0003)

### Projection
**Type:** Term
**Definition:** A rebuildable read model (Apache AGE graph, pgvector embeddings, full-text search) that never defines truth (46 to 52, ADR-0022, ADR-0023)

### Promotion
**Type:** Term
**Definition:** The governed step by which a learning candidate or conversation artifact becomes canonical knowledge (42, ADR-0019, ADR-0020)

### Golden Corpus
**Type:** Term
**Definition:** Version-controlled labeled documents and expected results exported from Nebula review decisions, used for evaluation and regression (96, 115.1, ADR-0057)

### Loss Run
**Type:** Term
**Definition:** A carrier report of claims history for an insured; property and casualty loss runs share a base extraction profile and diverge by line of business (9, ADR-0015)

---

## Genericness-Blocked Terms

The following terms are specific to the Nebula Insurance Brain domain and must not appear in the external agent framework (generic, reusable content). The framework's genericness validator can read this denylist with `--glossary`. Generic words the framework legitimately uses (policy, coverage, limit, retention, claim) are deliberately excluded from this list even though they are insurance terms here.

- Insurance
- Insured
- Policyholder
- Endorsement
- Loss run
- Underwriter
- Underwriting
- Broker
- MGA
- Premium
- Deductible
- ACORD
- General Liability
- Casualty
- Reinsurance
- FactSlot
- Docling
- Docling-Graph
- Insurance Brain

## Neurosymbolic assessment vocabulary (F0065)

These definitions accompany the [worked example](../examples/neurosymbolic-gl/README.md) and [assessment contract](../features/F0065-grounded-gl-guideline-assessment/assessment-contract.md). They describe planned v0.1 behavior; later concepts carry their release phase in the [coverage map](../examples/README.md).

| Term | Meaning in the Brain | Concrete example / boundary | Owning feature |
|---|---|---|---|
| Neurosymbolic processing | Neural interpretation and explicit symbolic representations/rules participate in one governed workflow | EX-GL-001: model extracts the limit; accepted typed facts feed a deterministic rule | F0015/F0016/F0018/F0065 |
| Concept | A versioned definition of a kind of thing, distinct from an instance | insurance.coverage defines the kind; EX-COV-001 identifies one coverage | F0012/F0013 |
| Guideline rule version | Immutable, reviewed operation with scoped inputs, authority, and effective/release context | EX-RULE-001-v1 compares a USD each-occurrence amount to a fictional minimum; no arbitrary logic strings | F0065 S0001 |
| Assessment record | Immutable result of applying a selected rule to exact accepted inputs at a snapshot | EX-ASSESS-001 is BELOW_GUIDELINE; it does not reject the policy or become canonical automatically | F0065 S0002/S0003 |
| Semantic snapshot | A consistent read basis for selected valid/known coordinates and versioned inputs | A concurrent endorsement cannot mix old and new inputs in one assessment | F0020/F0065 S0004 |
| Extraction confidence | A signal about one model interpretation, distinct from evidence quality, authority, or approval | CASE-05: 0.99 confidence in a wrong amount still needs correction | F0006/F0016/F0022 |
| Assessment outcome | MEETS_GUIDELINE, BELOW_GUIDELINE, UNKNOWN, CONFLICT, or NOT_APPLICABLE under the bounded contract | Missing input is UNKNOWN; denied access is an error, not a revealing gap outcome | F0065 S0002 |
| Embedding | Model-produced numeric representation for retrieval, versioned separately from its source | EX-FUTURE-001: a similar aggregate-limit passage cannot supply an each-occurrence fact | F0033, v0.2A |
| Normative constraint | An obligation with authority, condition, requirement, and valid period, distinct from observed facts | EX-FUTURE-003: an issuance deadline does not establish that issuance occurred | F0052, v0.3 |
| Hypothetical scenario | A base snapshot plus explicit assumption overrides with isolated results | EX-FUTURE-004: an assumed higher limit does not overwrite the policy fact | F0053, v0.3 |

Existing Assertion, FactSlot, Canonical Fact Version, Derivation, and Review Decision definitions are illustrated by the source-to-fact and temporal sections of EX-GL-001. Every changed or new concept must link a worked/boundary example and owning story/contract before its plan is considered ready.

## F0002 identity and authorization refinements (proposed design)

These definitions refine the existing Tenant/Workspace/Knowledge Base/Principal terms for the approved F0002 requirements. Runtime proof and Phase B approval remain pending. Contract: [AuthX v1 schema](../schemas/authx-kernel.schema.json), [assembly plan](../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/feature-assembly-plan.md); worked and boundary examples: [EX-AUTHX](../features/F0002-tenancy-aware-domain-kernel-and-principal-contracts/worked-examples.md).

### Tenant entity identity
A stable entity identity within one tenant, which may have explicit associations to several KBs of that tenant. An association is not a membership or access grant. F0002-S0001; EX-AUTHX-002/003; ADR-0061. Distinct from the globally stable verified principal identity.

### Membership
A current trusted principal-to-tenant/KB association carrying a role, validity/revocation, revision and complete resource restriction slice. Matching dimensions from unrelated grants cannot be combined into broader authority. F0002-S0003; EX-AUTHX-007–009.

### Resource scope
The actual permitted tenant/KB and broker/account/policy resource population derived from trusted grants and authoritative resource metadata. Request filters only intersect this authority. F0002-S0003/S0004; EX-AUTHX-007/010/011.

### Resource envelope
The server-hydrated ownership, parent chain, classification/source requirements, evidence dependencies and revisions for a resource. It is not a public request DTO. F0002-S0004; EX-AUTHX-010–012.

### Delegation
An explicit binding between a verified executor and acting principal, with a finite action/resource ceiling, expiry and revocation. Effective permission is the intersection of current acting authority and that ceiling; no onward delegation in v1. F0002-S0005; EX-AUTHX-014–016.

### Authorization context
A current trusted carrier of verified identities, complete grant slices, optional delegation, policy release and trace; business query dates are separate from enforcement time. F0002-S0002/S0003/S0005; EX-AUTHX-004/008/014.

### Authorization decision
An append-only record of permission evaluation under exact current revisions; allowed does not mean a business mutation succeeded. A durable outcome and decision reference distinguish success, denial and failure. F0002-S0006; EX-AUTHX-017/018.

### Authentication failure event
A durable sanitized record of rejected credentials without looking up protected data or inventing a principal. Invalid tokens never appear in its payload. F0002-S0002/S0006; EX-AUTHX-005.
