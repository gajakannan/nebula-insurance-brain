# Nebula Insurance Brain — Governed Evidence Retrieval & Spectral Graph Experiments

**Engineering design and coding-agent implementation handoff**  
**Version:** 1.4 (planning incorporation recorded; architecture proposal and feature approvals remain separate)\
**Prepared:** 2026-11-05  
**Revised:** 2026-11-06  
**Status:** Incorporated planning input (2026-11-06). The operator requested roadmap, feature, architecture and design incorporation; see [integrated design](governed-evidence-retrieval-design.md). F0068 now reserves the conditional spectral experiment and ADR-0076 is drafted as Proposed. No PRD, phase approval, ADR acceptance or runtime behavior is established; target retrieval features remain Planned. Subsequent feature plan actions consume §16.\
**Target repository:** https://github.com/gajakannan/nebula-insurance-brain  
**Research baseline:** SpectRAG, arXiv:2610.36991v3 (October 30, 2026)  
**Reference implementations:** https://github.com/SightAndCite/SpectRAG (official); https://github.com/aion7891/SpectraFuse (independent)

> **Handoff instruction:** Carry the baseline retrieval requirements into normal Nebula planning first. Implement only approved scope, natively in Nebula. Spectral computation is a conditional experiment, not a prerequisite for baseline retrieval delivery. Do not install, vendor, wrap, or copy SpectraFuse or SpectRAG as a runtime dependency. Do not adopt Neo4j/FAISS solely to match the reference code. Preserve Nebula’s canonical truth, evidence locators, authorization, temporal and projection contracts. This document proposes new design and code; it is **not** a statement that the described retrieval features already exist or authorization to start implementation.

## Review outcome

**2026-11-06:** The operator requested incorporation of the review corrections: align planning with prerequisite contracts, keep architectural KG edits with the architect, retain optional PPR, and stop using F0061 as an alias for an undecided experiment home. The operator also confirmed F0006 is merged. This records the handoff revision; D1–D9 remain decisions for their assigned planning phases, and no feature-plan or implementation approval is recorded here.

**Planning incorporation, 2026-11-06:** Under the operator's request, the Product Manager/Architect role pass carried RET requirements into feature READMEs, reserved F0068 (D3 recommended separate home) at v0.4+, drafted Proposed [ADR-0076](decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md), and updated blueprint/roadmap/KG, design, examples, evaluation and security inputs. Local planning baseline: `85384db`, containing archived F0006. D1 is incorporated and D2 drafted; D4–D9 and per-feature approvals remain pending. Experiment reservation is not its implementation, cost or activation decision. The earlier review outcome above describes the prior handoff revision.

---

## 0. Executive decision

**Planning direction incorporated:** Carry governed graph-assisted evidence retrieval into F0035/F0036, and reserve a separately scoped spectral experiment (F0068 under D3) to test whether spectral structure adds enough value to justify its cost. The baseline combines authorized hybrid retrieval, bounded typed expansion and token-budgeted context selection. The optional branch evaluates versioned spectral coordinates and heat diffusion against that baseline and an optional PageRank comparator when implemented. Treat every branch as an enhancement to *retrieval and analysis*, never as a truth, adjudication, access-control, or policy-evaluation engine.

**Scope:** Baseline: (1) versioned, typed evidence-retrieval graph; (2) bounded candidate expansion; (3) optional PageRank comparator; (4) token-budgeted set selection; (5) provenance-preserving traces, tests and early evaluation. Conditional spectral experiment scope (F0068): weighted numerical adjacency, Laplacian eigenpairs/coordinates, spectral closeness and heat diffusion. F0067 may later consume recorded diagnostics within its approved scope. Out of scope: changing canonical assertions; inferring accepted facts from embeddings; autonomous ontology mutation; replacing AGE, pgvector, Docling, or evidence selectors; training a new embedding model; running global spectral decomposition during every query; bringing the spectral experiment forward from its proposed v0.4+ horizon without a roadmap decision.

**Key engineering position:** Stable evidence, scope, temporal and projection contracts are the architectural commitment proposed here. Spectral scoring is an optional implementation strategy whose incremental benefit must be established on held-out insurance cases. Delivering the baseline without a spectral index is a valid outcome.

**Delivery posture:** No broad refactor and no all-in-one PR. First settle contracts and the threat model; next build the benchmark runner and synthetic fixtures; then implement and measure the baseline. Begin spectral work only after a recorded experiment decision. Where F0033–F0036 do not exist, prove contract adapters with synthetic fixtures and defer production integration until their contracts are ready. The 2026-11-06 incorporation carries planning requirements, examples, a Proposed ADR and roadmap/KG reservations into their owning documents. Full feature plans, schemas, executable contracts and proof approvals remain PR-01 deliverables.

| Existing feature | Proposed incorporation | Delivery boundary |
|---|---|---|
| F0035 | Authorized hybrid seeding, bounded typed expansion, projection compatibility and PPR comparison | Baseline retrieval; no spectral dependency |
| F0036 | Budgeted evidence context, locator revalidation, gaps and grounded answer-basis linkage | Baseline generation contract |
| F0068 — spectral experiment (D3 reservation) | Spectral/heat experiments, numerical artifacts and incremental cost/quality evaluation | Reserved at v0.4+; separate experiment scope/scheduling/cost decision still required |
| F0067 | Read recorded retrieval events and any approved diagnostics | Later consumer; no prerequisite for recording traces |

**Where the spectral experiment lives (decision D3).** The 2026-11-06 planning incorporation reserves **F0068 — Spectral graph retrieval experiments**, following the recommended separate-feature option. F0061 retains dense+sparse retrieval, multivectors, reranking and optional Qdrant (ADR-0033). The alternatives considered were amending F0061 or leaving research unallocated; neither is used in this amendment. F0068 remains Planned at v0.4+ and does not block baseline planning. Its own scope/scheduling and experiment-cost decision after baseline measurement is still required before PR-07/PR-08; reservation is not activation approval. See the [feature](../features/F0068-spectral-graph-retrieval-experiments/README.md) and [decision map](governed-evidence-retrieval-design.md#6-decisions-and-remaining-feature-planning).

### 0.1 Users and problem

**Primary persona:** [Priya the GL Underwriter](../examples/personas/gl-underwriter.md). Typical question: "As of 2026-03-01, does the policy for this account exclude products-completed operations, and which endorsement changed that?" A correct answer needs the original form wording, the amending endorsement and its effective date, and the account/policy relationship, all within her current grants. **Secondary personas:** [business reviewer](../examples/personas/business-reviewer.md) (verifies the evidence behind an answer) and [domain steward](../examples/personas/domain-steward.md) (owns the meaning of relationship types used for expansion). No claims-handler persona exists; claims-context cases in §9.2 are fixture categories, not a persona commitment.

**Problem (to confirm in F0035 Phase A clarification):** hybrid retrieval ranks passages independently. Under a fixed context budget it can fill the window with similar passages and omit the amending or excluding evidence that changes the answer, producing a confident partial answer instead of a complete one or an explicit gap.

---

## 1. Repository baseline (2026-11-05 local checkout)

The revision was checked against local commit `de8813b` on `feat/f0006-assertion-semantics`, with this handoff untracked. This identifies the reviewed checkout; it does not claim verification of remote `main`. Recheck the baseline before each implementation PR.

### 1.1 Decisions and feature statuses

| Existing item | Observed status | Consequence for this design |
|---|---|---|
| ADR-0022 Apache AGE graph projection | **Accepted** | Canonical domain tables authoritative; AGE is rebuildable traversal projection. Do not create competing system of record. |
| ADR-0023 pgvector retrieval projection | **Accepted** | Vectors identify likely evidence; never establish truth. |
| ADR-0024 multi-modal search | **Accepted** | FTS + vector + graph + ontology + temporal + metadata + authorization is the intended fusion model. |
| ADR-0040 lossless content/evidence contract | **Accepted, proven** | Reuse parse-once six-file document bundle and precise evidence bindings; do not re-OCR/re-interpret for retrieval indexing. |
| ADR-0058 evidence anchoring/selector contract | **Accepted with amendments** | Accepted v0.1A shape is `nebula:BoxSelector`, with immutable artifact target, declared precision and `unresolved`. Full redundant W3C selectors remain a future enhancement; retrieval must not change the locator vocabulary. |
| ADR-0073 versioned content contracts/document metadata | **Proposed; Phase B approved** | Existing v1/v2 dispatch, artifact identity and activation rules must be respected; indexing must not implicitly upgrade content or infer missing legacy provenance. |
| ADR-0053 permission-safe retrieval/historical access | **Proposed** | Current grants govern access even for historical business queries; seek security approval before shipping. |
| ADR-0046 grounded answer and analytic query contract | **Proposed** | Answers must carry scope, time, evidence, abstention; counts and amounts require typed authorized queries, not RAG estimates. |
| ADR-0071 semantic trace + answer basis contract | **Proposed; binding carry-in direction** | Distinguish observed, considered-not-used, used-in-answer and gaps; only answer citations create used attribution. |
| ADR-0075 versioned assertion semantics and admission | **Proposed; Phase B approved** (F0006) | Assertion kind, mood, origin, source wording and the eligibility guard are defined here. Retrieval of a source statement never confers admission or canonical eligibility; bind `knowledge_mode` behavior to this contract. |
| ADR-0003 parse once; ADR-0007 full bitemporality; ADR-0010 provenance mandatory | **Accepted** | Named by the plan-review checklist (BRAIN-PARSE-ONCE/TEMPORAL/EVIDENCE); indexing reads persisted content, both time axes are honored, every selected item keeps lineage. |
| ADR-0019 conversation knowledge is not canonical by default | **Accepted** | Scenario/conversation knowledge never becomes canonical through retrieval. |
| ADR-0033 Qdrant is optional | **Accepted** | Governs F0061's current scope (decision D3). |
| ADR-0062 current authorization and durable decisions | **Accepted, bounded to F0002 scope** | Current-grant evaluation and decision records reused by retrieval eligibility. |
| ADR-0064 time interpretation and valid-time precision | **Proposed** | Precision and unknown bounds stay explicit in temporal eligibility. |
| ADR-0072 Observatory is a read-only projection | **Proposed** | F0067 reads retrieval traces; no write path. |
| F0033 pgvector; F0034 AGE | **Planned, v0.2A** | Verify contracts and use isolated adapters for fixtures; production retrieval integration depends on their delivery. |
| F0035 hybrid search; F0036 evidence-aware generation | **Planned, v0.2A** | Primary integration targets for the online pipeline. |
| F0061 advanced retrieval | **Planned, v0.4+** | Existing dense+sparse, multivector, reranking and optional Qdrant scope. Historical scope boundary; the incorporation reserves spectral work separately as F0068. |
| F0067 Graph Observatory | **Planned, v0.2B** | Later visualization consumer, not a prerequisite to correct trace emission. |

The README reports F0001 proofs implemented and F0005 synthetic Docling-Graph candidate development complete, **not** production-ready activation. The broader retrieval stack should be assumed planned unless code-level verification in the agent’s checkout proves otherwise. **Do not mark an ADR Accepted or a feature Implemented by editing prose alone.**

**F0006 note:** F0006 (assertion semantics) is archived as complete; the operator confirmed its merge on 2026-11-06. Use a planning baseline containing ADR-0075 and its glossary terms. The local commit cited above remains the reviewed source snapshot, not the merge commit.

**Terminology guard:** `knowledge_mode` (canonical / source / scenario) comes from master-blueprint §113.1. It is distinct from the glossary's [Fact Mode](../domain/glossary.md#fact-mode) (`ASSERTED`/`OBSERVED`/`DERIVED`) and from ADR-0075's assertion mood and eligibility. Phase B must bind these names without overloading any of them.

### 1.2 Existing code and contract anchors

- `engine/packages/brain-content/src/brain_content/`: content artifacts, version-dispatched manifests/records, verified document storage and contracts (ADR-0073).
- `engine/packages/brain-domain/src/brain_domain/`: facts, principals, tenancy and AuthX contracts. Reuse `OwnedScope` (tenant/workspace/knowledge base) and the existing requested-scope/resource-envelope types.
- `engine/packages/brain-persistence/src/brain_persistence/`: SQL persistence; no assumption that a graph or vector adapter already exists.
- `engine/packages/brain-security/src/brain_security/`: policy and authorization adapters.
- `engine/packages/brain-temporal/src/brain_temporal/`: temporal ranges, commits and outbox.
- `engine/packages/brain-review/src/brain_review/evidence.py`: review evidence handling.
- `engine/apps/api/src/brain_api/`: current API and routes.
- `engine/apps/worker/src/brain_worker/outbox_projector.py` and `brain_temporal/outbox.py`: current worker marks outbox events processed; it does **not** build AGE/vector projections. Define consumer-specific delivery/checkpoint and rebuild contracts with F0033/F0034 before attaching another projection to the shared processed marker.
- `neuron/packages/brain-extraction/src/brain_extraction/`: Docling-Graph pipeline and evidence interpretation; do not alter to make retrieval work.
- `planning-mds/architecture/graph-observatory-design.md` and `planning-mds/architecture/decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md`.
- `planning-mds/kg-source/**` is authored; `planning-mds/knowledge-graph/*.yaml` is compiled. Add KG links in authored shards and use existing compiler; never edit compiled YAML by hand.

**Agent verification gate:** Before each PR, inspect current checkout and report changes since this snapshot. The specific module paths below are *proposed new locations*, not assertions that those modules exist.

---

## 2. Research provenance and adoption rationale

SpectRAG (Sahinoglu et al., arXiv:2610.36991v3) proposes retrieval of a jointly useful **set** of chunks: hybrid seeding, a weighted graph over six edge signals, neighborhood expansion, spectral proximity/relevance propagation, and token-budgeted context selection. The official implementation uses FAISS, BM25, Neo4j and index-time utility questions; **these are implementation choices, not Nebula platform requirements**.

SpectraFuse is an **independent** implementation inspired by the paper. It includes modules for spectral coordinates, diffusion, expansion and context selection. Its published MultiHopRAG report shows tuned evidence recall under a 12,000-token budget of **0.846 vs 0.832** for its hybrid baseline: **+1.4 percentage points for the tuned full system**. Untuned defaults score **0.803**; a no-expansion ablation is reported at **0.705**. These are upstream results, not a Nebula reproduction. Candidate counts and budget utilization also differ across modes, so the no-expansion result alone does not isolate structural benefit. The report establishes neither improvement on insurance documents nor the isolated contribution of spectral computation. Treat the numbers as experimental motivation. Cross-check ambiguous equations against the paper and official implementation; capture immutable upstream revisions when recording a Nebula experiment.

**Nebula rationale:** A commercial P&C question may need a declarations block, endorsement effective date, exclusion text, related insured/location records and a loss event. Semantic top-k can miss bridge evidence. Graph traversal recovers related material; spectral coordinates capture broader structural neighborhoods; context-set optimization protects scarce tokens. Governing temporal/authorization/evidence controls remain superior to all learned or computed relevance scores.

References:

1. https://arxiv.org/abs/2610.36991
2. https://github.com/SightAndCite/SpectRAG
3. https://github.com/aion7891/SpectraFuse
4. https://github.com/aion7891/SpectraFuse/blob/main/docs/DESIGN.md (documents independent interpretation choices and ambiguities)
5. https://github.com/aion7891/SpectraFuse/blob/main/src/spectrafuse/utils/spectral.py
6. https://github.com/aion7891/SpectraFuse/blob/main/src/spectrafuse/utils/diffusion.py
7. https://github.com/aion7891/SpectraFuse/blob/main/src/spectrafuse/utils/selection.py

---

## 3. Architecture: planes, boundaries, and ownership

```text
Existing authoritative plane
  Immutable source artifacts + Docling normalized blocks + evidence locators
       -> source statements / reviewed accepted canonical facts / ontology
       -> bitemporal canonical records + policy/tenant authorization
                   |
                   | outbox/rebuild/versioned projection
                   v
Derived retrieval plane (NEW)
  Evidence blocks with canonical references
     + typed edges + individual raw edge signals
     + dense/lexical indexes (through F0033/F0035 adapters)
     + sparse weighted adjacency / optional experimental eigenpairs
                   |
                   v
Query execution (NEW)
 Verified principal + root/requested scope + knowledge mode + pinned snapshot
    -> authorized, time-correct seeds
    -> bounded typed graph expansion
    -> hybrid/expansion/PPR baseline; optional spectral/heat experiment
    -> context-set optimization under exact token budget
    -> canonical evidence revalidation + grounded answer contract
                   |
                   +----> ADR-0071 semantic execution trace
                   +----> F0067 Observatory (read-only)
```

### 3.1 Boundaries

1. **Source of truth:** Canonical tables and review/adjudication state. Neither spectral projection nor embeddings may write accepted assertions.
2. **Extraction:** Consume existing normalized native content + locators. Avoid doc conversion or LLM extraction from source within retrieval routines.
3. **Graph:** AGE remains the authoritative *traversal projection* for canonical domain relationships; spectral adjacency is a rebuildable, scoped *retrieval derivative* that may use sparse numerical arrays in object storage or a versioned relational table. It is not a second canonical knowledge graph.
4. **Models:** All scoring math accepts deterministic candidate/edge inputs and can run with no LLM. Index-time utility questions are an opt-in, auditable derivative with model/version/provenance identifiers.
5. **Access:** Authorization is an eligibility predicate, enforced before seeds/expansion and before any result or trace output. Requested root and filters only narrow current server-resolved grants; a principal's full visible corpus is not the default scope of an account/document question. No cross-tenant latent/aggregate leakage.
6. **Historical queries:** `valid_as_of` and `known_as_of` specify business history; **current grants** govern who may see that history, per ADR-0053 direction.
7. **Knowledge mode:** Preserve the blueprint section 113.1 distinction between source statements, accepted canonical state and scenario assumptions. Retrieval cannot promote a source claim to an accepted fact or silently substitute canonical state for the original document.
8. **Observability:** Trace events record operations, identifiers and sanitized score summaries; no raw prompts, response text, source excerpts or secret payloads in traces.

### 3.2 Package proposal (final placement subject to repo architecture review)

```text
engine/packages/brain-retrieval/                  # new Python package, or approved matching monorepo location
  src/brain_retrieval/
    contracts.py             # Pydantic/dataclass DTOs; no database dependency
    eligibility.py           # scoped candidate policy and temporal assertions
    edge_signals.py          # typed signal normalization and edge fusion
    graph_projection.py      # build/version/rebuild abstract interface
    spectral.py              # conditional spectral experiment: Laplacian, solver, eigenspace alignment
    diffusion.py             # PPR comparator; conditional experiment heat/proximity
    expansion.py             # bounded filtered candidate expansion
    fusion.py                # rank fusion and calibration
    context_selection.py     # token-set optimizer and reasons
    pipeline.py              # orchestration, feature flags, degradation
    telemetry.py             # ADR-0071 event writer adapter
    adapters/                # interfaces, then AGE/pgvector/Postgres adapters
  tests/unit/
  tests/property/
  tests/integration/
  tests/benchmark/
```

**Do not implement everything in `neuron` merely because the math uses NumPy.** Choose a package boundary at PR-01 with the architect, including whether existing planned `brain-search`/`brain-graph` packages can own these responsibilities before adding `brain-retrieval`. **Recommendation:** the master blueprint already plans `engine/packages/brain-search/` and `engine/packages/brain-graph/`; place fusion, expansion and selection in `brain-search` and typed-edge projection adapters in `brain-graph`. A new `brain-retrieval` package needs an explicit reason recorded in the ADR (decision D6). Math should be independent from storage and model serving; actual LLM answer generation can remain with the planned conversation/neuron integration. Respect existing `pyproject.toml` / `uv.lock` package management; dependencies should be reviewed, not silently added. The tree describes possible responsibilities, not a requirement to create every module before baseline delivery.

---

## 4. Derived retrieval contracts — proposed, versioned

The exact field naming must be aligned with existing Nebula schemas. The illustrative JSON below defines semantics and invariants, not an instruction to duplicate existing core identity types.

### 4.1 EvidenceBlockRef

```json
{
  "evidence_block_id": "eb_123",
  "canonical_artifact_id": "artifact_01",
  "artifact_version": "sha256:...",
  "document_version_id": "document-version_01",
  "content_contract_version": 2,
  "normalized_record_version": 2,
  "block_id": "docling-block-14",
  "section_path": ["Coverage", "Exclusions"],
  "text_fingerprint": "sha256:...",
  "locator_ref": "locator_01",
  "precision": "exact-span",
  "owned_scope": {
    "tenant_id": "tenant-A",
    "workspace_id": "workspace-A",
    "knowledge_base_id": "kb-A"
  },
  "binding_refs": ["evidence-binding_45"]
}
```

- Evidence block identity is immutable within an artifact version; re-indexing must be idempotent.
- Reuse the exact existing `OwnedScope` and artifact identity types; the human-readable identifiers here are illustrative. Ownership alone is not an access grant.
- Each `binding_ref` resolves to a source assertion and, when applicable, its accepted canonical fact/relationship versions, evidence/derivation refs and their temporal state. A block may have zero or many bindings with different valid/recorded intervals and admission states. Resolve them through the canonical APIs at the pinned snapshot; do not assign one canonical validity interval or acceptance status to the immutable block.
- Source availability/recording history and canonical business validity are separate predicates. `source` mode may retrieve original wording that has been superseded canonically; `canonical` mode must resolve the applicable accepted versions. Neither mode restores revoked access. Missing temporal precision remains explicit under ADR-0064.
- Evidence precision and selector vocabulary follow ADR-0058 as amended (`nebula:BoxSelector` today); `unresolved` stays unresolved regardless of retrieval score. This work does not require or activate full W3C selectors.
- Honor ADR-0073 version dispatch, artifact pins, v1 compatibility and v2 origin/anchor/table records. A v1 artifact is not silently upgraded; unsupported versions fail explicitly and missing legacy provenance stays unknown.
- Content resides in content store, not duplicated into spectral arrays/trace blobs.

### 4.2 TypedEvidenceEdge

```json
{
  "src": "eb_123",
  "dst": "eb_456",
  "direction": "undirected-for-spectral-projection",
  "relation_type": "MODIFIED_BY_ENDORSEMENT",
  "raw_signals": {
    "semantic": 0.42,
    "adjacency": 0.0,
    "section": 0.0,
    "shared_entity": 0.90,
    "citation": 1.0,
    "utility_question": null,
    "canonical_relation": 1.0
  },
  "edge_weight": 0.78,
  "edge_model_version": "insurance-v1",
  "input_refs": ["canonical-relationship-version_12", "evidence-binding_45"],
  "semantic_snapshot_id": "snapshot_897",
  "eligibility_class": "same-security-scope"
}
```

- Six research signals: semantic, adjacency, section, shared entity, citation, utility-question. **Seventh Nebula-specific typed canonical relationship** is proposed as a separate signal; never treat it as part of the paper's six.
- Keep raw signals and normalized weights for recomputation. `null` means absent/not evaluated; do not silently treat missing as a valid zero unless the weight normalization policy explicitly says so.
- Store original directed and typed relationships separately. Symmetrization for a Laplacian is a *derived numerical choice*, not a rewrite of domain meaning (`EXCLUDES` is not reversible).
- Each projected edge must retain input-version references sufficient to re-evaluate its mode, temporal and dependency authorization predicates. Both endpoints being visible does not establish visibility of the relationship or its evidence dependencies. Semantic/section/adjacency edges also record their input artifact versions and construction recipe.
- Do not merge evidence across access domains solely because of entity-name overlap. Entity matching uses canonical identity and permission scope where available.

### 4.3 SpectralProjectionManifest

```json
{
  "projection_id": "spectral-2026-11-05-001",
  "schema_version": "1.0",
  "source_commit_watermark": "commit-897",
  "semantic_snapshot_id": "snapshot_897",
  "temporal_view_id": "temporal-view_42",
  "knowledge_mode": "canonical",
  "ontology_release_id": "ontology-r42",
  "graph_projection_id": "age-proj-r31",
  "embedding_model_id": "embedding-model@version",
  "edge_weight_profile_id": "gl-coverage-v1",
  "eligibility_partition_id": "scope-partition-A",
  "requested_scope_fingerprint": "sha256:...",
  "authorized_corpus_fingerprint": "sha256:...",
  "authorization_basis": {
    "policy_release_id": "policy-r7",
    "grant_revision": "authority-r19",
    "resource_restriction_revision": "restrictions-r24"
  },
  "content_generation_id": "content-generation_8",
  "node_count": 10000,
  "edge_count": 46000,
  "components": 15,
  "eigenpairs_requested": 32,
  "eigenpairs_retained": 32,
  "solver": "symmetric-sparse-eigsh",
  "algorithm_version": "spectral-1.0.0",
  "artifact_hashes": {"node_map": "sha256:...", "adjacency": "sha256:...", "eigenpairs": "sha256:..."},
  "built_at": "2026-11-05T12:00:00Z",
  "state": "READY"
}
```

- Version key must include the full graph content/edge weighting and admissible security partition—not merely a wall-clock build date.
- `temporal_view_id` must resolve to immutable canonical `valid_as_of`/`known_as_of` coordinates and precision/selection policy; `semantic_snapshot_id` identifies the consistent read basis. A recorded-time watermark does not define a valid-time slice. Mode, scope, authorized corpus and input revisions are part of compatibility and the build identity. §8 defines the proposed conservative compatibility policy.
- Authorization basis fields describe how the artifact was built; they do not grant permission to read it. Resolve current grants/restrictions again on use. Keep internal fingerprints and revision metadata behind the authorized API; they are not public topology summaries.
- Persist a canonical node-ID-to-matrix-row map, deterministic sorted order, and checksums.
- Query must pin the manifest version; stale/missing/unavailable projection reports a defined fallback, not a silent replay against current graph.
- Specifying `valid_as_of` at query time does not automatically make a precomputed eigenbasis correct for every historical graph; see §8 temporal strategies.

### 4.4 Retrieval request/response

All type names below are semantic placeholders to bind to existing schemas at PR-01; this is not a second identity or authorization type system. The request is an internal service object constructed after identity verification. Client filters may only narrow scope; authorization context and execution pins are service-resolved.

```python
RetrievalMode = Literal[
    "hybrid_only", "graph_expand", "graph_ppr",
    "graph_spectral", "graph_heat", "graph_ppr_spectral",
    "spectral_no_expansion",
]

@dataclass(frozen=True)
class RetrievalRequest:
    query: str
    principal: PrincipalRef
    root: ContextRootRef
    requested_scope: RequestedScope
    knowledge_mode: Literal["canonical", "source", "scenario"]
    scenario_ref: ScenarioRef | None
    valid_as_of: TemporalCoordinate
    known_as_of: TemporalCoordinate
    token_budget: int
    profile_id: str
    retrieval_mode: RetrievalMode
    trace_id: str

@dataclass(frozen=True)
class RetrievalExecutionBasis:
    semantic_snapshot_id: str
    valid_as_of: TemporalCoordinate
    known_as_of: TemporalCoordinate
    ontology_release_id: str
    root: ContextRootRef
    knowledge_mode: Literal["canonical", "source", "scenario"]
    scenario_ref: ScenarioRef | None
    requested_scope_fingerprint: str
    authorization_basis_ref: str
    projection_ids: tuple[str, ...]
    retrieval_profile_version: str
    effective_mode: RetrievalMode
    model_profile_id: str
    tokenizer_revision: str

@dataclass(frozen=True)
class SelectedEvidence:
    evidence_block_id: str
    source_artifact_id: str
    locator_ref: str
    precision: str
    binding_refs: tuple[str, ...]
    token_count: int
    selection_reason: Literal["anchor", "bridge", "coverage", "backfill"]
    score_components: dict[str, float]
    graph_path_ids: tuple[str, ...]

@dataclass(frozen=True)
class EvidenceContext:
    basis: RetrievalExecutionBasis
    selected: tuple[SelectedEvidence, ...]
    considered_not_selected_ids: tuple[str, ...]
    token_count: int
    max_token_budget: int
    payload_hash: str
    gaps: tuple[str, ...]
    reason_codes: tuple[str, ...]
```

Pin the execution basis once and pass it through every adapter. The immutable authorization-basis reference records policy, grant, resource/dependency restrictions and delegation revisions used for the decision; it is not reusable permission. Recheck current authority at the final evidence boundary. Record all actual projection IDs, including an empty tuple for a supported lexical-only path, and the effective mode after fallback. Do not fabricate a spectral ID when no spectral artifact was used. `scenario` mode requires an explicit scenario ref and remains unavailable until its owning contracts are delivered; unsupported modes reject explicitly without substituting canonical or source semantics.

Response does **not** determine “used in answer.” That is established downstream exclusively by the grounded answer basis contract and ADR-0071 `ANSWER_BASIS_LINKED` event.

---

## 5. Weighted graph construction

### 5.1 Candidate graph vertices

Use evidence blocks with precise source and tenant refs. A separate conceptual/entity graph may be projected into evidence-to-evidence links via canonical entity references, but do not collapse entities and documents into a single untyped adjacency without explicit projection rules. Record provenance and role of every projected edge.

### 5.2 Signals and initial policy

| Signal | Construction | Safety boundary | Initial weight |
|---|---|---|---:|
| semantic similarity | Positive cosine between configured kNN blocks | Same authorized projection partition; only admissible nodes | 0.20 |
| section hierarchy | Same/related section in immutable artifact | Same artifact version, never cross-tenant | 0.15 |
| shared canonical entity | Match canonical entity IDs referenced by blocks | No string-only identity merge | 0.15 |
| document adjacency | Consecutive anchored blocks | Same artifact/version, no section-bypass | 0.05 |
| explicit citation | Source reference/hyperlink/endorsement link | Verify referenced target and its access | 0.10 |
| utility-question similarity | Optional model-generated question embeddings | Derivative only; model+prompt provenance | 0.05 |
| **canonical insurance relation** | COVERAGE_OF, AMENDS, EXCLUDES, EFFECTIVE_AT, LOCATION_OF etc. | Typed and provenance-anchored | **0.30** |

**These weights are proposed seed values only** (experiment hypotheses, not business rules; decision D7); calibrate with held-out insurance evaluation, do not import paper defaults blindly. Normalize within active signals with a documented policy, and prevent a missing expensive signal from accidentally boosting another signal without a recorded profile change.

For signals \(x_{ij}^{(r)} \in [0,1]\):

\[
 W_{ij}=\sum_r \alpha_r x_{ij}^{(r)};\quad W_{ij}\leftarrow 0 \text{ if }W_{ij}<\tau.
\]

Require `W_ij >= 0`, finite values, deterministic `top_k_edges`, bounded degree, and recorded symmetrization strategy (`max`, `mean`, or `union`) for the **spectral** layer. Preserve directed graph traversal separately.

### 5.3 Insurance-specific edge profiles

These profiles are retrieval-tuning hypotheses, not insurance business rules. Any insurance meaning they rely on (what amends, excludes or covers what) must trace to the glossary, ADR-0070 and owning ontology features; the domain steward confirms profile semantics before tuning (decision D7).

- `gl_coverage`: prioritize explicit endorsement/amendment/exclusion, declared coverage and effective time; no inference of cover from semantic similarity.
- `claims_context`: prioritize claim, event, property/location, policy-term and exposure evidence, within authorized account scope.
- `underwriting_guideline`: prioritize authoritative guideline/version/line-of-business links; separate source document statements from approved enterprise guidelines.
- `generic_document`: paper-like signals, without authoritative boosts where no canonical facts exist.

Profile must be selected based on typed query intention or explicit user scope and recorded with the answer. Profiles can influence retrieval only; they must not alter adjudication.

---

## 6. Spectral mathematics and implementation requirements

These requirements apply to the conditional spectral experiment (F0068; PR-07/PR-08). The PPR comparator in §6.5 can be evaluated with the baseline without an eigenbasis. Baseline retrieval must not import spectral solver dependencies merely to satisfy this section.

### 6.1 Normalized Laplacian

For undirected nonnegative weighted adjacency \(W\), degree \(d_i=\sum_j W_{ij}\), \(D=\mathrm{diag}(d_i)\):

\[
L_{sym}=I-D^{-1/2}WD^{-1/2}.
\]

Use sparse CSR/CSC for production-size graphs. For isolated nodes, define `D^-1/2_ii=0`; explicitly specify isolated-node diagonal behavior, test it, and keep isolated blocks available through lexical/vector retrieval. For connected components, use stable eigenpair sorting and drop **all** near-zero trivial eigenmodes when constructing nontrivial coordinates. The simplistic “drop only eigenvector 1” approach fails for disconnected graphs; test disconnected components.

### 6.2 Eigenpairs and embeddings

Solve \(L_{sym} u_i=\lambda_i u_i\) for the lowest nontrivial eigenpairs. Suggested start: 16 or 32 nontrivial dimensions; validate eigenspace quality before saving. When eigenvalues are nearly repeated, individual eigenvectors are not uniquely oriented: raw coordinate comparisons across separate builds are **not** valid. Persist a versioned basis and, where necessary for monitoring, compare subspaces/projection matrices or align within degenerate eigenspaces. A sign flip in an eigenvector must not change pairwise distances in one build.

Required validations:

1. Shape, finite entries and non-negative eigenvalues within numerical tolerance.
2. Residual \(\|LU-U\Lambda\|_F/\max(1,\|U\Lambda\|_F)\) under chosen threshold.
3. Orthogonality \(\|U^TU-I\|_F\) under threshold.
4. Connected component/isolated-node behavior; dimensions when `n < dims+1`.
5. Deterministic node ordering, no dense `n x n` matrix for large graphs.
6. Rebuild reproducibility at the **subspace/scoring** level, not exact eigenvector signs.

### 6.3 Spectral proximity

For query seeds with weights \(p_i\), a simple experimentally testable structural proximity is a kernel-weighted coordinate similarity:

\[
z_i=[u_1(i)e^{-t\lambda_1},...,u_m(i)e^{-t\lambda_m}],\quad
\mu_q=\sum_{i\in seeds}p_i z_i.
\]

Normalize scores, compare candidate vs. seed centroid, and treat this as one configurable *approximation*, not the only definition of “spectral relevance.” Avoid assigning strong relevance to a disconnected component just because its eigenvector coordinates happen to be close. Test query-local connectivity and component membership explicitly.

### 6.4 Heat-kernel diffusion

For query seed vector \(s_0\):

\[
s_t=e^{-t L_{sym}}s_0\approx U_m e^{-t\Lambda_m}U_m^T s_0.
\]

If using a truncated basis, include/properly handle the zero-eigenvalue subspace, and measure truncation error against a small exact `scipy.linalg.expm` baseline. For disconnected graphs, diffusion must not move score mass across components. Clamp or calibrate any numerical negative artifacts before ranking, with documented treatment.

### 6.5 Personalized PageRank comparator

Keep PPR as a comparator and optional ensemble feature:

\[
p_{k+1}=\beta s_0 +(1-\beta)P^T p_k
\]

where `P` is a **row-stochastic** random-walk transition matrix; define sink/dangling-node handling explicitly. The symmetric-normalized adjacency iteration used in some reference implementations is a related diffusion recurrence but is **not strictly the canonical probability-preserving PageRank update**. Name it accurately if using that form. Test conservation of mass for stochastic PPR, seed restart, disconnected components and convergence.

### 6.6 Feature separation and evaluation

Implemented modes must be independently switchable within the registry: `hybrid_only`, `graph_expand`, `graph_ppr`, `graph_spectral`, `graph_heat`, `graph_ppr_spectral`, `spectral_no_expansion` (ablation). Registry membership does not require implementation: PPR remains optional and spectral modes belong to the conditional experiment. Reject unimplemented modes explicitly. Avoid calling a 2-hop walk “spectral” when no eigenbasis is used. Provide score components with bounded normalized ranges and explicit fusion calibration.

**Potential future uses beyond RAG** (not in initial release): ontology community candidates, bridge detection, anomalous relationships, drift alerts. Every proposed relationship remains reviewable; no automatic accepted ontology changes.

---

## 7. Online retrieval pipeline

**Hard ordering:** requested root/scope, knowledge mode, current permission and temporal eligibility must constrain every operation that can influence output. The source of authorization is existing Nebula AuthX, not retrieval configuration. A pinned canonical snapshot and a pinned authorization decision are distinct: the former preserves business consistency; the latter must be refreshed when current authority changes.

```python
async def retrieve_context(req: RetrievalRequest) -> EvidenceContext:
    basis = execution.resolve_and_pin(
        req.principal, root=req.root, requested_scope=req.requested_scope,
        knowledge_mode=req.knowledge_mode, scenario_ref=req.scenario_ref,
        valid_as_of=req.valid_as_of, known_as_of=req.known_as_of,
    )
    plan = projections.compatible_plan_or_fallback(
        basis, profile_id=req.profile_id, requested_mode=req.retrieval_mode,
    )  # No compatible optional artifact -> authorized baseline or explicit gap.
    basis = execution.bind_plan(basis, plan)
    budget = context_budget.resolve(
        requested=req.token_budget, model_profile=runtime.model_profile,
        query=req.query, prompt_template=config.prompt_template,
        reserved_output_tokens=config.context_budget.reserved_output_tokens,
    )

    seeds = hybrid_retriever.search(
        req.query, basis=basis, plan=plan,
    )
    eligibility.assert_admissible(seeds, basis)

    candidates = plan.expand_if_enabled(
        seeds, basis=basis,
        max_hops=config.max_hops, max_candidates=config.max_candidates,
        permitted_edge_types=config.edge_types,
    )
    eligibility.assert_admissible(candidates, basis)

    scores = ranker.score(
        req.query, seeds, candidates, basis=basis, plan=plan,
        mode=plan.effective_mode,
    )
    selected = context_selector.choose(
        candidates, scores, budget=budget.evidence_tokens,
        model_tokenizer=budget.tokenizer,
    )

    # Recheck current authority; resolve bindings according to mode and snapshot.
    verified = evidence.resolve_and_reauthorize(selected, basis=basis)
    context = assemble_context(verified, basis=basis, budget=budget)
    context_budget.verify_serialized_payload(context, budget)
    trace.record_nonblocking(req, seeds, candidates, context)
    return context
```

This is **interface-level pseudocode**; it must be adapted to existing package and AuthX APIs, not pasted into production as-is.

Every adapter must apply eligibility within its search/traversal operation; the assertions above validate that contract and cannot repair influence from ineligible inputs. If final authorization removes an item, recompute coverage/gaps and serialize/count the final context again. Any backfill uses the same scope, snapshot and authorization boundary. Recording failure marks trace completeness and never fails the answer, per ADR-0071.

### 7.1 Seeding

Fuse lexical, vector and optional utility-question ranks via Reciprocal Rank Fusion:

\[
RRF(d)=\sum_{r\in retrievers}\frac{w_r}{k+r_r(d)}.
\]

Start with deterministic weights, then tune. Preserve per-retriever seed ranks. Do not assume global vector distance is comparable to keyword score; calibrate before weighted blending. Missing vector/graph backends must degrade to authorized lexical retrieval, not break the policy boundary.

### 7.2 Graph expansion

Defaults for experiments (not contractual): 20 seed blocks; up to 2 hops; max 200 candidates; per-node fan-out cap, per-edge-type caps and total compute/time limits. Walk typed edges, preserve the actual path to each candidate, and ensure every intermediate vertex/edge is authorized. Prioritize canonical relationship edges, but test whether this overshadows needed source claims.

Twenty expansion seeds are not a cap on the standalone hybrid comparator: that comparator must retrieve enough candidates to use the same evidence budget (§9.4). Seed count, candidate pool size and final token count are separate parameters.

### 7.3 Ranking

Fuse base relevance and graph scores with a versioned profile. The core comparator is `base` vs `PPR` vs `spectral` vs `heat` vs `ensemble`. Do not use a confidence-looking score as a probability unless calibrated. Graph structural proximity may rank *candidates* only; source authority is a separate filter/assertion-resolution stage.

### 7.4 Context-set optimization

Formalized under token budget \(B\): maximize a set utility over relevant, diverse and complementary evidence with required coverage constraints. An example greedy marginal utility is:

\[
U(c\mid C)=a\,Rel(c)+b\,Prox(c)+c\,ClusterGain(c,C)
+d\,SourceGain(c,C)-\lambda\,Red(c,C)-\kappa\,Risk(c).
\]

`Risk` here is **retrieval provenance risk**, not underwriting risk. Hard exclusions are performed before utility calculations; this term may only downrank admissible but lower-quality evidence. No penalty may override a mandatory authorized citation needed for the final answer. Selection should use a protected anchor core, coverage-aware expansion, redundancy control, token-cost tie-break and backfill only if it increases expected usefulness. Measure the tendency to select very short chunks; SpectraFuse reports its default length bias hurt recall.

Constraints:

- Resolve the effective evidence budget as `min(requested_budget, model_context_window - fixed_input_tokens - reserved_output_tokens - safety_margin)`. Fixed input includes the actual system prompt, question, conversation/tool payloads and template. Reject an invalid/nonpositive budget explicitly; a proposed 8,000-token evidence budget cannot fit a 4,096-token window. Note: the existing 4,096-token default belongs to the extraction adapter (`neuron/packages/brain-extraction/src/brain_extraction/vllm_graph_client.py`, `openai_compatible_adapter.py`); no answer-generation model profile exists yet. Defining it is decision D5 for F0036 Phase B.
- The final serialized evidence payload, including separators, wrappers, citations and source references, must tokenize to at most the effective budget with the exact target model tokenizer/revision. Count the complete payload after grouping and reauthorization; sums of separately tokenized snippets are not sufficient. No words-based heuristic in production.
- Track coverage obligations for query subquestions, relevant policy term, endorsement version and exclusions; missing required proof leads to an explicit gap/abstention rather than fabricated completeness.
- Do not split a table row/endorsement effective clause in a way that changes semantics. Respect Docling block precision.
- Return source order, document grouping and `selection_reason` for each item.
- Citation spans resolved only by existing evidence anchoring and grounded-answer contracts.

---

## 8. Security, temporal consistency, and information leakage (release blockers)

Security owns plan-review rule BRAIN-AUTHORIZATION. This section is input to `planning-mds/security/authorization-review.md` and a threat model using the nebula-agents threat-model template; it is not the security review itself.

### 8.1 Authorization requirements

1. Candidate IDs, expansion neighbors and edge existence all require authorization **before** scoring or logging.
2. Shared global spectral coordinates may encode restricted topology even when final chunks are filtered. Avoid per-tenant cross-domain contamination: generate scoped partitions or prove mathematically and through red-team tests that unauthorized nodes cannot affect scores, counts, neighbors or timing. Partitioning by tenant alone may be insufficient for finer grants.
3. At query time, use a compatible filtered projection; if current grants are narrower than the partition, either derive an authorized query-local subgraph and compute scoring there, or fall back to non-spectral retrieval. **Do not treat post-hoc hiding of unauthorized results as sufficient.**
4. Test cross-tenant entity collisions, edges through unauthorized intermediary, historical access revocation, counts/facets and timing side channels, traces, caches and derived artifacts.
5. Authorized queries must be auditable without recording source text in traces.

**Proposed initial policy to bind at PR-01:** Construct the request's eligible corpus and typed relationships using existing AuthX `OwnedScope`, requested filters, current grant slices, parent/classification/source restrictions and evidence dependencies. Apply the root and expansion policy before ranking. Do not combine attributes from different grant slices to manufacture authority. A precomputed spectral artifact may be used only when its complete influence domain matches that authorized requested corpus and the temporal/mode contract below; matching tenant IDs or hiding rows afterward is insufficient.

Compatibility must check the semantic snapshot, requested root/scope fingerprint, knowledge mode, authorized node/edge/input fingerprints, policy release, authority/grant revision, resource/dependency restriction revisions, ontology release, content generation, edge recipe and embedding model. A mismatch makes the spectral artifact unusable for that request. Initially, revisions must match exactly; relaxing that rule requires a separately reviewed proof of equivalent admissible inputs. Recheck current authority before returning evidence. Cache keys and trace/replay reads follow the same scope and revision checks; an old authorization decision is not a cache-read grant.

When the basis is incompatible, use baseline retrieval on an authorized, temporally compatible view. An approved spectral experiment may instead construct a bounded query-local graph from admissible inputs and compute its own spectrum within documented latency/memory caps; do not slice rows from an incompatible global basis. If neither path is available, return an explicit gap/unavailable result. A proposed build manifest never authorizes use of private topology.

**Required negative proof:** With the request's admissible inputs unchanged, add/change/revoke an unauthorized node or edge and verify that returned IDs, paths, score components, context and visible counts do not change; examine timing/cache behavior for inference channels. Test root narrowing separately from permission narrowing. Any unresolved leak prevents production use of that scoring path.

### 8.2 Bitemporal requirements

A current spectral projection does not automatically represent the graph *as of* a historical effective/known time. A commit watermark captures delivery progress, not both temporal dimensions. **Proposed initial policy:** reuse a stored spectrum only for the exact pinned semantic snapshot, precision-aware valid/known coordinates, knowledge mode and authorized corpus it was built for. Initially there is no claim that one spectrum serves a range of times.

- **Default fallback:** lexical/vector retrieval and optional AGE traversal using their own compatible snapshot/temporal contracts, without spectral scoring. Current-only AGE topology is not a historical fallback. If no compatible backend exists, report the gap instead of querying today's graph silently.
- **Conditional local experiment:** build a bounded authorized/time-filtered candidate graph and its spectrum from the pinned inputs. This is an opt-in spectral experiment, with explicit resource limits and a distinct local projection ID.
- **Later optimization:** build reusable versioned temporal slices only when evaluation shows enough reuse to justify their cost. Broader interval compatibility must prove identical admissible nodes, edges, weights and corpus-level ranking inputs throughout the claimed interval.

**Do not** apply historical filters only after using a future-state spectral embedding; later knowledge can leak into candidate rank and may change a historical answer. Define precision-aware effective dates and `known_as_of` via canonical temporal types. Current grants always checked.

For `source` mode, select the requested immutable source version subject to its recorded availability and current access; later canonical supersession does not erase its wording. For `canonical` mode, resolve applicable accepted facts/relationships and bindings at both coordinates. Neither mode may include inputs not yet known at `known_as_of`. PR-01 must bind these distinctions to the existing source, admission and temporal contracts with executable examples.

### 8.3 Projection/version atomicity

- Persist spectral artifacts with a build manifest and checksums; switch availability atomically from `BUILDING` to `READY` after all validations pass.
- Projection inputs must reference an outbox/semantic commit watermark, ontology release, evidence-block generation, embedding-model version and edge-weight profile.
- Bind all those inputs to one reproducible read basis; a manifest listing independently sampled revisions does not prove a consistent snapshot. Document per-consumer checkpoints, replay/rebuild and cutover semantics before extending the current mark-processed-only outbox worker.
- On partial failure, keep old usable version and mark new failed; no mixed node-map/eigenpair/graph revisions.
- Support idempotent rebuild and bounded retention of referenced versions for audit/replay, consistent with existing policy.
- Distinguish *statistical freshness* from *semantic correctness*. A slightly stale version may be acceptable only if contractual temporal and grant compatibility are verified; never silently use mismatched versions.

---

## 9. Test plan and benchmark specification

### 9.1 Unit/property/math tests

| Test | Required assertion |
|---|---|
| Toy line/star/clique/bridge graphs | Eigenvalue ordering and known structural behavior; distinguish local hop vs global spectral proximity. |
| Isolated vertices & disconnected components | No NaN/Inf; no diffusion across components; correct trivial eigenmode handling. |
| Repeated/near-degenerate eigenvalues | Stable subspace comparisons despite sign/rotation; no arbitrary cross-version raw coordinate alignment. |
| Sparse vs dense small graphs | Eigenvalues, diffusion and ordering within numerical tolerances. |
| Heat diffusion vs exact matrix exponential | Bounded error on small graphs for chosen truncation. |
| PPR stochastic implementation | Conservation, restart and convergence with explicit sinks. |
| Symmetric matrix from directed domain edges | Projection is documented; canonical direction is unchanged. |
| Token budget | Exact tokenizer count never exceeds budget including metadata. |
| Empty/one-node graph & missing embeddings | Controlled fallback with reason code. |
| Determinism | Same manifest inputs -> same mapping and equivalent scores, absent allowed solver tolerance. |
| Root/scope narrowing | An authorized account/document query never broadens to the principal's entire visible corpus. |
| Source vs canonical mode | Original wording remains retrievable in source mode after supersession; canonical mode selects the applicable accepted version at the pinned coordinates. |
| Revision/temporal mismatch | Reject an incompatible optional basis and record the effective fallback; no silent current-graph replay. |
| Model context budget | Final serialized input plus reserved output fits the configured model window, including a 4,096-token profile. |

### 9.2 Insurance synthetic golden corpus

Minimum 120 questions as an initial target (not an existing corpus guarantee), distributed:

- 30 simple single-evidence facts (no regression allowed).
- 30 cross-document coverage/endorsement/exclusion joins.
- 20 `valid_as_of`/`known_as_of` and conflicting amendments.
- 20 authorized cross-entity claim/location/exposure traversals.
- 10 missing evidence/unanswerable questions requiring abstention.
- 10 adversarial cross-tenant/revoked-grant/leakage queries.

This distribution and its insurance scenarios are fixture design choices for Phase A to confirm, not business rules; insurance meaning in gold answers must trace to the glossary and owning features. Per the [examples contract](../examples/README.md), documentation/development examples stay outside the frozen evaluation holdout.

Fixture documents should include declarations, endorsements, cancellations, schedules of locations, claim narratives, underwriting guidelines and source-only unaccepted claims. Keep all data synthetic; precise gold `evidence_block_id` sets, admissibility, temporal truth, answer and citation spans must be adjudicated. Include paired source/canonical questions and broader-permission/narrower-root cases. Split tuning, validation and held-out test by document/account families, keeping paraphrases and related versions together; do not tune on test labels. PR-01 must map these cases to glossary definitions, a worked example, a boundary case and owning feature/story/contract links in the examples coverage map before new semantic contracts are approved.

### 9.3 Metrics

**Retrieval:** Recall@5/10, complete-gold-evidence-set recall, evidence precision, bridge-evidence recall, MRR, nDCG, redun­dancy rate, source/section diversity, budget-weighted evidence recall.

**Grounded answer:** answer correctness, abstention precision/recall, citation faithfulness, number/limit calculation accuracy (via typed query, **not** pure RAG), conflict/supersession resolution and evidence anchoring precision.

**Operational:** p50/p95/p99 retrieval latency, token count, index build time, spectral solver residual, memory/index size, projection staleness/fallback rate, per-tenant resource consumption.

**Security (hard):** zero unauthorized IDs in candidates, traversal paths, scores returned, traces, log fields, cached artifacts, external responses, and no history-based access restoration. Include tests for count/timing inference channels.

### 9.4 Minimum ablation matrix

Run A–C for the baseline, D if the optional PPR comparator is implemented, and the applicable E–G rows only when their spectral modes are pursued. Record unimplemented comparisons as unavailable rather than fabricating results or making optional modes a baseline prerequisite.

| Mode | Hybrid seeds | Expansion | PPR | Spectral coords | Heat | Context selector |
|---|---|---|---|---|---|---|
| A | yes | no | no | no | no | top-k |
| B | yes | no | no | no | no | budget-aware |
| C | yes | yes | no | no | no | budget-aware |
| D | yes | yes | yes | no | no | budget-aware |
| E | yes | yes | no | yes | no | budget-aware |
| F | yes | yes | no | yes | yes | budget-aware |
| G | yes | yes | yes | yes | optional | budget-aware |

Build the corpus and executable benchmark runner in PR-02, before spectral implementation. Record baseline runs as each real adapter becomes available; synthetic adapter results are interface proofs, not production-quality retrieval evidence.

Run two complementary comparisons:

1. **Controlled component ablations:** hold token budget, eligible corpus, hybrid seed ranking/count, selector settings and split fixed as appropriate for the component under test. For scoring-only comparisons, also hold the candidate graph fixed. Record candidate counts, selected tokens and budget utilization to expose bottlenecks.
2. **Strong end-to-end baseline:** allow hybrid A/B to retrieve up to the same candidate cap as graph-assisted modes, enough to fill the same evidence budget. Do not restrict hybrid retrieval to the 20 expansion seeds while graph modes consider 200 candidates. Give competing modes comparable tuning effort and report latency/index cost. Include the project's reranker baseline when available, without making its implementation a new prerequisite.

Report paired bootstrap confidence intervals and breakdown by query type. Compare spectral gain beyond `C`, `D` and the strong hybrid baseline, not only against naive dense RAG. Add heat-only (`graph_heat`) and `spectral_no_expansion` rows if those experimental modes are pursued. No gain from expansion or the selector may be attributed to spectral computation without its own ablation.

### 9.5 Proposed release gates (operator approval required)

These retrieval gates are named RG0–RG5 so they are not confused with the nebula-agents plan-action gates G1–G5 (clarification, tracker sync, Phase A approval, ontology sync, Phase B approval). They are feature acceptance criteria to fold into the owning PRDs, not additional framework gates.

- **RG0 design:** New ADR reviewed; no contradiction with accepted ADRs or KG source; interface and security threat model accepted.
- **RG1 primitives:** Baseline graph/selection and any PPR comparator pass their tests. For the conditional spectral branch, numerical/property tests, reproducible offline artifacts and representative sparse-solver scale proofs are additionally required.
- **RG2 retrieval:** No single-hop regression beyond pre-agreed tolerance; demonstrable multi-hop evidence-set gain on held-out synthetic corpus; configurable modes and fallback.
- **RG3 governance:** 100% pass of permission, bitemporal, evidence-locator and answer-basis invariants, including adversarial tests.
- **RG4 operations:** p95 latency/index cost within documented budget and fail-open only to **safe simpler retrieval**, never to unfiltered retrieval.
- **RG5 promotion:** Review baseline and spectral paths independently. Spectral experiments use the D3-reserved F0068 home and require explicit scope/scheduling and cost approval; activation requires shadow evidence, incremental quality/cost benefit against the strongest eligible baseline, limited opt-in and feature-owner approval. Production default is a separate decision. Baseline delivery does not wait for spectral approval.

**Target-setting:** Pre-register tolerances, minimum worthwhile gains and latency/index-cost limits after baseline measurement and before held-out evaluation. No numeric gain target is set in advance. Governance invariants remain hard requirements. Report spectral benefit separately; if it is absent or outweighed by cost, retain the baseline and defer the spectral branch.

---

## 10. Agent work breakdown and PR sequence

Agent roles are aligned to Nebula's agent workflow; actual assignments/parallelization must follow the installed `nebula-agents` skills, `agent-map.yaml`, gates and repository contribution instructions.

**Mapping to the plan action:** this PR sequence is a delivery outline, not a framework run plan. PR-01 spans the owning features' `plan` actions per §16.6: the product manager may start F0035 Phase A to clarify requirements; F0033/F0034 projection contracts and checkpoint decisions must be settled before F0035 Phase B is approved; F0036 binds its generation/model contract after the F0035 retrieval interface is settled. Phase A artifacts belong to the product manager; Phase B ADRs, schemas and architectural KG bindings belong to the architect. PR-02 onward map onto `feature` action runs for the owning features once their plans are approved. Requirement IDs in §16.2 are the traceable form of the acceptance items below.

### PR-01 — Architecture decision, contracts and dependency map

**Owner:** architect + product-manager; **review:** security, backend, AI, QA.  
**Tasks:** Read relevant accepted/proposed ADRs; refine `ADR-0076-governed-graph-assisted-evidence-retrieval.md` (drafted by the 2026-11-06 incorporation) from the §16.3 draft decisions, using the normal lifecycle. Map baseline responsibilities to F0035/F0036, use the reserved F0068 home while retaining its separate experiment decision, and identify F0067's later read-only consumption. Update authored KG relationships and required glossary/example coverage. Bind existing ownership, requested-scope, knowledge-mode, content-version, temporal and evidence contracts; add one retrieval-mode enum, DTO schemas and reject/fallback reasons. Settle the conservative compatibility policy in §8, revision/cache semantics, projection checkpoints and the model-window budget contract.\
**Acceptance:** validators/compilers pass; no hand-edit of compiled KG; feature phases/statuses remain accurate; source/canonical and narrowed-root examples are executable; the threat model and initial fallback strategy are reviewed. Remaining implementation decisions have owners. Baseline contracts do not require an eigenbasis.  
**Do not:** mark Proposed ADRs as Accepted without proof/review.

### PR-02 — Insurance fixtures, benchmark runner and baseline protocol

**Owner:** QA + AI engineer + product-manager; **review:** architect + security.  
**Tasks:** Build the §9 corpus and versioned split manifest, gold evidence/binding labels, benchmark interfaces, budget checks, ablation runner and paired bootstrap reporting. Establish controlled and strong hybrid comparison protocols. Record any available baseline with its actual adapter/model/corpus versions; pre-register quality/cost thresholds before held-out scoring.  
**Acceptance:** runner works without a spectral dependency, validates budget/candidate-count reporting and keeps related document/account families in one split. Fixture/adapter-only runs are labelled. Freeze the holdout before tuning; report progress honestly if real backend delivery is pending.  
**Do not:** defer evaluation tooling until the last PR or claim retrieval quality from fake adapters.

### PR-03 — Typed graph primitives and compatible projection adapters

**Owner:** backend + security + data engineer; **review:** architect + QA.  
**Tasks:** Build deterministic node maps, typed provenance-linked edges, bounded adjacency interfaces and projection version/compatibility checks. Implement rebuild/checkpoint/atomic-publication contracts and canonical/outbox/AGE/pgvector adapters only where upstream contracts are ready. Keep optional numerical signal weighting independent of canonical relationship meaning.  
**Acceptance:** authorized intermediate/dependency checks, root and temporal isolation, source/canonical distinctions, idempotent recovery and coherent version pins pass. Use in-memory fixtures first when upstream runtime delivery is absent.  
**Dependency:** F0033/F0034 contract readiness; defer production integration until delivered.  
**Do not:** create a canonical fact store, consume events solely through the existing global processed marker, or build an eigenbasis in this baseline PR.

### PR-04 — Hybrid retrieval, bounded expansion and PPR comparison

**Owner:** backend + AI engineer; **review:** security + QA.  
**Tasks:** RRF seeding, `hybrid_only`/`graph_expand` modes, optional stochastic `graph_ppr` comparator, typed candidate paths, calibrated score components, bounded work and safe degradation. Feed each mode into the PR-02 runner as it becomes available.  
**Acceptance:** repeatable rankings, authorized root-scoped candidates, explicit timeout/fallback outcomes and strong hybrid candidate-budget parity; PPR mass/restart/convergence tests apply if that comparator is implemented.  
**Dependency:** F0035 contract and upstream backend readiness.  
**Do not:** treat scores as canonical confidence or require spectral scoring for baseline search.

### PR-05 — Budget-aware EvidenceContext and grounded answer linkage

**Owner:** AI engineer + backend; **review:** QA + security.  
**Tasks:** Protected anchors, coverage/novelty/redundancy, exact final-payload token counting, source grouping, existing locator resolution, current reauthorization, explicit gaps and grounded answer-basis adapter. Preserve v1/v2 content dispatch and original-source vs canonical semantics.  
**Acceptance:** locators/precision remain honest; model window and reserved output are respected; reauthorization removals recompute coverage/budget; `selected` never means `used`; analytics use the typed authorized query path. Run A–C context/answer comparisons, adding D if PPR is implemented.  
**Dependency:** F0036/ADR-0046 contract review and evidence/content consumers.

### PR-06 — Baseline trace contract and measured delivery evidence

**Owner:** backend + QA + AI engineer; **review:** architect + security.  
**Tasks:** Wire ADR-0071 events at retrieval, traversal, selection and revalidation boundaries as those operations land; produce the answer-basis event from the grounded answer. Finalize version/scope-aware replay references, completeness handling and baseline quality/latency/index-cost reports. F0067 visualization remains separate.  
**Acceptance:** recording failures do not fail answers; considered/used attribution is exact; no excerpts/private payloads in traces; approved baseline invariants and applicable A–D comparisons pass (§9.4). Reuse this instrumentation if spectral modes are later added.  
**Dependency:** ADR-0071 schema and existing read-path trace ownership; no dependency on F0067 rendering.

### PR-07 — Conditional spectral computation experiment (F0068)

**Owner:** AI engineer; **review:** architect + QA + security.  
**Entry gate:** F0068 is reserved under D3; an explicit scope/scheduling and experiment-cost decision after baseline results is still required. This handoff does not authorize bringing v0.4+ work forward.\
**Tasks:** Optional weighted numerical adjacency, normalized Laplacian, component-aware sparse eigenpairs, zero-mode handling, spectral coordinates, solver diagnostics and checksummed versioned artifacts. Apply §8 compatibility before any production-path use.  
**Acceptance:** applicable §9.1 math tests, sparse scale/memory budgets and subspace/scoring reproducibility pass. Register numerical artifacts as derived and access-controlled.  
**Do not:** make the baseline import the solver or introduce per-request global eigendecomposition.

### PR-08 — Conditional scoring modes, ablations and shadow integration

**Owner:** AI engineer + backend; **review:** QA + security.  
**Tasks:** Spectral closeness, truncated heat kernel, optional PPR/spectral fusion, registered ablation modes and sanitized trace extensions. Evaluate stored compatible bases and any approved bounded local experiment separately; shadow traffic remains permission-safe.  
**Acceptance:** zero-mode/component and exact-small-graph tests pass; E–G plus heat-only/no-expansion results isolate incremental effects against strong hybrid/C/D baselines. Record effective fallback and projection IDs; no default activation.  
**Dependency:** PR-07 experiment approval, compatible inputs and baseline trace instrumentation.

### PR-09 — Benchmarks, tuning and promotion evidence

**Owner:** QA + AI engineer + product-manager; **review:** architect + security.  
**Tasks:** Consolidate the runner and results developed from PR-02 onward, paired confidence intervals, operational costs and independent review. Recommend baseline rollout and, only if pursued, a separate spectral rollout/defer decision. Publish fallback/rollback evidence and approved feature/KG status changes.  
**Acceptance:** applicable §9 hard gates and pre-registered quality/cost thresholds pass. Baseline delivery can close without PR-07/PR-08; record the spectral branch as deferred, not implemented.  
**Do not:** attribute baseline gains to spectrum or promote an optional mode solely because academic recall improves.

### Dependencies / parallelization

```text
PR-01
  -> PR-02 (fixtures + runner; measure each subsequent delivery)
  -> PR-03 -> PR-04 -> PR-05 -> PR-06 (baseline)
                                  |-> PR-09 (baseline rollout)
                                  |-> explicit spectral experiment decision (F0068 reserved under D3)
                                      -> PR-07 -> PR-08 -> PR-09 (spectral decision)

F0033/F0034/F0035/F0036 delivery remains a separate dependency.
```

**Planning opportunities for parallel work:** fixture authoring, approved threat-model proofs and pure baseline primitives can proceed independently after PR-01 where the workflow permits. No agent assignment or parallel execution is authorized by this note. Do not attempt DB integration before contracts are settled, or spectral implementation before the experiment entry gate.

---

## 11. Configuration and operations

Illustrative **proposed** configuration—not existing Nebula settings:

```yaml
retrieval:
  default_mode: hybrid_only
  allowed_modes: [hybrid_only, graph_expand, graph_ppr]  # omit graph_ppr when unimplemented
  max_hops: 2
  max_candidates: 200
  max_fanout_per_node: 20
  edge_profile: generic_document_v1
  trace_mode: sanitized
  context_budget:
    model_profile_id: configured_runtime_profile  # resolves window + exact tokenizer revision
    evidence_token_cap: null                     # bounded by request and available model window
    reserved_output_tokens: 512                  # provisional; validate against model profile
    safety_margin_tokens: 64                    # provisional
  spectral_experiment:
    enabled: false                 # default until release gates
    allowed_modes: [graph_spectral, graph_heat, graph_ppr_spectral]
    spectral_dims: 32
    spectral_solver: sparse_eigsh
    heat_t: 1.0
    missing_projection_behavior: authorized_hybrid_fallback
    shadow_evaluation: false
  ppr_restart: 0.15
  convergence_tolerance: 1.0e-7
```

The request, schema, runner and configuration all use the `RetrievalMode` enum in §4.4. Allowlist only implemented modes; omit `graph_ppr` when the optional comparator is absent. Baseline modes are eligible for normal planning; spectral modes require the approved experiment flag and allowlist. `spectral_no_expansion` is a benchmark-only enum value, never a production allowlist entry. An unimplemented/disabled/unapproved mode is rejected explicitly; a permitted mode whose optional artifact is incompatible takes the recorded safe fallback. Configuration does not authorize roadmap or feature activation by itself.

Security constraints and version compatibility are **not operator-overridable** through ordinary feature flags. Validate config/schema and reject dangerous combinations, unresolved model profiles and invalid context budgets. Add build metrics: index lag, applicable solver residual/component count, `build_failures`, rate of stale projection fallback, authorization failures, p95 retrieval latency, per-tenant cost. Rollback to a prior manifest must still pass current compatibility checks; otherwise use compatible authorized hybrid retrieval or report a gap.

Resource sizing: benchmark 1k/10k/100k+ evidence blocks with representative sparse degrees and historical slices; measure CPU/memory/build costs and convergence before choosing a hard dimensionality or recomputation strategy. Consider SciPy sparse eigensolvers, `expm_multiply` for heat on selected sizes, and small-graph exact solvers for proofs. Do not infer production latency from SpectraFuse's in-memory benchmarks.

---

## 12. Risks, alternatives and explicit open decisions

| Risk / decision | Suggested resolution | Owner / gate |
|---|---|---|
| Cross-permission structure leakage through shared eigenbasis | Bind exact authorized-corpus/revision compatibility and safe fallback at PR-01; prove adversarial non-influence before use | Security / PR-01, RG3 |
| Historical validity of spectral basis | Bind exact snapshot/valid-known view initially; compatible baseline fallback; local experiments/slice reuse require explicit proof | Architect + temporal / PR-01, RG3 |
| Disconnected components/zero eigenvalues | Component-aware computation and test battery | AI / RG1 |
| Utility-question index-time hallucinations/cost | Optional, provenance-tagged derivative; do not treat as canonical | AI / RG2 |
| Incorrect acceptance of source claims | Resolve bindings by explicit knowledge mode at the pinned snapshot; source retrieval never confers canonical admission | Backend / RG3 |
| Over-weighting semantic links vs insurance typed edges | Profile-based ablation and gold-set tuning | AI + domain expert / RG2 |
| Spectral compute scalability | Sparse solvers, offline builds, bounded basis and partitioning | Platform / RG4 |
| Score instability across graph versions | Pin basis version, record drift, compare invariant subspaces | AI / RG1,RG4 |
| Solver/rebuild failure | Atomic manifests; authorized hybrid fallback | Backend / RG4 |
| Proposed vs accepted ADR status | Do not bypass governance; record evidence for status changes | Architect / RG0 |
| Should graph math live in engine or neuron? | Prefer isolated pure package; settle against existing architecture | Architect / PR-01 |
| Cost of spectral partitions/slices under fine-grained grants | Begin with exact compatibility/fallback; evaluate reuse and local computation only in the approved experiment | Security + platform / PR-01, PR-07 |
| Spectral benefit absent or smaller than operating cost | Retain measured baseline, publish ablations and defer spectral delivery | Product + AI / experiment decision, PR-09 |
| Which tokenizer, budget, and edge weights? | Use target model tokenizer and held-out tuning, not copied defaults | AI + product / RG2 |

**Alternatives considered:**

- **Adopt SpectraFuse as runtime library:** rejected for now; creates a competing indexing/storage contract and insufficiently accounts for Nebula's permission/time/authority boundaries. Still useful reference code.
- **Adopt official SpectRAG stack end to end:** rejected; Neo4j/FAISS and default models are not Nebula requirements.
- **Hybrid + bounded graph traversal/context selection, with optional PPR:** valid baseline and a complete delivery outcome when it meets approved requirements. Spectral computation must demonstrate additional value to displace it.
- **Global unfiltered spectrum + post-query ACL filter:** rejected unless formal threat model establishes no unauthorized influence; default prohibited.
- **Recompute full spectrum per query:** rejected as normal path; query-local bounded experiments are possible for rare historical/filter scopes.

---

## 13. Coding-agent execution prompt (paste into Nebula agent orchestrator)

**When using nebula-agents:** prefer invoking the `plan` action as described in §16.6 over pasting this prompt; the action supplies its own role sequence, gates and evidence package. Add ADR-0003/0007/0010/0064/0075 to the reading list below.

> **Task:** Plan *Nebula Governed Evidence Retrieval & Spectral Graph Experiments* following `nebula-spectral-graph-intelligence-handoff.md`. This proposal requires normal planning, ADR and execution gates; it does not authorize implementation or changes to accepted contracts. The target repo is `gajakannan/nebula-insurance-brain`; use the installed sibling `nebula-agents` framework and repository `.nebula-project.yaml`/contribution gates for subsequent authorized work. Identify the current branch/commit and its relationship to `main`; read README, blueprint, ADRs 0022/0023/0024/0040/0046/0053/0058/0071/0073, relevant feature artifacts and source schemas. Produce a verified dependency/discrepancy report. Start with **PR-01 only when assigned**: ADR draft, scope/mode/snapshot and versioned content/evidence contracts, conservative compatibility/fallback policy, threat model, feature/KG/example mappings and executable acceptance plan. Preserve `nebula:BoxSelector` and v1/v2 dispatch. Do not mark planned work implemented, create a truth store, import reference runtime libraries or expose private trace payloads. After approval, follow the baseline PR-02–PR-06 path with early evaluation and PR-09 rollout evidence. PR-07/PR-08 belong to F0068 under D3 and require an explicit experiment/scheduling/cost decision after baseline measurement; they are not automatic follow-ons. Optional mathematics must prove disconnected-graph, eigenspace and heat/PPR correctness. Every delivered path must prove current-grant/root isolation, mode-aware bitemporality, evidence anchoring, model-window token limits, non-blocking traces and pinned replay. Report spectral incremental benefit and cost separately; defer it when the evidence does not justify delivery. Keep changes small and aligned with authored KG compilation.

**Expected outputs from agent at each PR:**

1. Change summary and design/ADR references.
2. Paths actually modified and API/schema diff.
3. Tests and exact commands executed; pass/fail evidence.
4. Authorization, temporal, provenance, rollback and migration impact.
5. Open decisions/risks and next PR dependencies.

**Stop/review conditions:** existing architecture contradiction, missing required approved contract, inability to prove scope isolation, irreversible data migration, cross-tenant spectral leakage, untested score use as source authority, or historical projection mismatch.

---

## 14. Authoritative source links and status references

### Research / implementations

- Paper: https://arxiv.org/abs/2610.36991 (v3 revised 2026-10-30)
- Official code: https://github.com/SightAndCite/SpectRAG
- SpectraFuse independent implementation: https://github.com/aion7891/SpectraFuse
- SpectraFuse design choices: https://github.com/aion7891/SpectraFuse/blob/main/docs/DESIGN.md
- SpectraFuse evaluation: https://github.com/aion7891/SpectraFuse/blob/main/benchmarks/results/multihoprag/REPORT.md

### Nebula

- Repository README: [README.md](../../README.md)
- Blueprint: [master-blueprint.md](master-blueprint.md)
- ADR-0022: [ADR-0022-apache-age-is-the-graph-projection.md](decisions/ADR-0022-apache-age-is-the-graph-projection.md)
- ADR-0023: [ADR-0023-pgvector-is-a-retrieval-projection.md](decisions/ADR-0023-pgvector-is-a-retrieval-projection.md)
- ADR-0024: [ADR-0024-search-is-multi-modal.md](decisions/ADR-0024-search-is-multi-modal.md)
- ADR-0040: [ADR-0040-lossless-content-and-evidence-contract.md](decisions/ADR-0040-lossless-content-and-evidence-contract.md)
- ADR-0046: [ADR-0046-grounded-answer-and-analytic-query-contract.md](decisions/ADR-0046-grounded-answer-and-analytic-query-contract.md)
- ADR-0053: [ADR-0053-permission-safe-retrieval-and-historical-access.md](decisions/ADR-0053-permission-safe-retrieval-and-historical-access.md)
- ADR-0058: [ADR-0058-evidence-anchoring-and-selector-contract.md](decisions/ADR-0058-evidence-anchoring-and-selector-contract.md)
- ADR-0071: [ADR-0071-semantic-execution-trace-and-answer-basis-contract.md](decisions/ADR-0071-semantic-execution-trace-and-answer-basis-contract.md)
- ADR-0073: [ADR-0073-versioned-content-contracts-and-document-metadata.md](decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md)
- ADR-0075: [ADR-0075-versioned-assertion-semantics-and-admission.md](decisions/ADR-0075-versioned-assertion-semantics-and-admission.md)
- Scope contract: `engine/packages/brain-domain/src/brain_domain/tenancy.py` (`OwnedScope`) and `authx.py` (`RequestedScope`/`ResourceEnvelope`)
- Authorization evaluator: `engine/packages/brain-security/src/brain_security/evaluation.py`
- Evidence mapper: `engine/packages/brain-review/src/brain_review/evidence.py`
- Versioned content records: `engine/packages/brain-content/src/brain_content/records.py` and `contracts.py`
- F0035: [README.md](../features/F0035-hybrid-search-and-authorized-scope/README.md)
- F0036: [README.md](../features/F0036-evidence-aware-retrieval-and-grounded-generation/README.md)
- F0061: [README.md](../features/F0061-advanced-retrieval/README.md)
- F0067: [README.md](../features/F0067-graph-observatory/README.md)
- F0068: [README.md](../features/F0068-spectral-graph-retrieval-experiments/README.md)
- Integrated design: [governed-evidence-retrieval-design.md](governed-evidence-retrieval-design.md)
- ADR-0076: [Proposed retrieval contract](decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md)

---

## 15. Definition of done

**Baseline:** Ready for normal production consideration only when the owning feature requirements/ADR contracts are approved; requested root/scope, current grants, knowledge mode, source availability and canonical bitemporality are proven; content/evidence versions and locator precision survive context assembly; the complete serialized input fits the target model window with output reserved; selected/considered/used attribution is correct; trace recording is sanitized and non-blocking; replay pins actual execution versions; strong hybrid and graph/PPR comparisons meet pre-registered quality/cost criteria; and fallback, monitoring and rollback are tested. No spectral artifact is required to meet this definition.

**Conditional spectral branch:** Belongs to F0068 under D3 and additionally requires explicit scope/scheduling/cost approval, numerical/component/eigenspace and heat tests, exact authorized/temporal projection compatibility, held-out ablations showing worthwhile incremental benefit over the strongest eligible baseline, measured build/latency/retention costs and approved staged activation. Record a defer decision when these conditions are not met. **No acceptance of source assertions or ontology edits may result solely from retrieval or spectral ranking.**

**Recommended immediate next step:** review this revised handoff, then assign PR-01 through normal planning when authorized. Bind the scope/mode/snapshot and compatibility contracts before implementation, establish fixtures and the benchmark runner in PR-02, and measure the baseline before deciding whether to schedule spectral work. Do not start by installing either SpectRAG implementation.

---

## 16. Planning intake for nebula-agents (product manager and architect)

This section adds what the `plan` action's product-manager (Phase A) and architect (Phase B) roles and `plan-review` (`docs/plan-review-checklist.md`) need. It does not replace §0–§15; it makes them traceable.

### 16.1 Plan-review rule map

| Rule | Owner | Where this handoff addresses it | What Phase A/B must still produce |
|---|---|---|---|
| BRAIN-SCOPE | product-manager | §0, §0.1, §16.2 | PRD scope, exclusions and story acceptance criteria |
| BRAIN-AUTHORITY | architect | §1.1, §16.3 | ADR-0076 drafted as Proposed; dependencies on Proposed ADRs labeled |
| BRAIN-EVIDENCE | architect | §3.1, §4.1, RET-36-03/04 | Evidence-lineage data requirements and proof plan |
| BRAIN-PARSE-ONCE | architect | §3.1 item 2, RET-33-02 | Indexing requirements reading persisted content only |
| BRAIN-TEMPORAL | architect | §8.2, RET-35-04 | Temporal read requirements and tests |
| BRAIN-AUTHORIZATION | security | §8.1, RET-35-01/02/03 | Entry in `security/authorization-review.md` and negative test plan |
| BRAIN-BUILDABILITY | code-reviewer | §10, §16.2, §16.5 | Stories with owners, prerequisites, interfaces and validation |
| BRAIN-EXAMPLES | architect | §9.2, §16.4 | EX-RET examples, glossary terms, coverage-map rows |

### 16.2 Carry-in requirements (Phase A inputs)

Proposed "must" requirements, numbered for traceability into PRDs and stories. Feature status does not change. Spectral requirements (§6, §8.1 compatibility for spectral artifacts) belong to F0068 under D3 and are not carried into v0.2A.

**F0033 — pgvector retrieval (v0.2A)**

- **RET-33-01** Embedding records must carry source block ID, owned scope, artifact/content version, model ID and version, so an eligibility predicate can run inside the vector query.
- **RET-33-02** Indexing must read the persisted content artifact and be idempotent per artifact version.
- **RET-33-03** The projection must expose a stable version identifier that an execution basis and trace can cite.

**F0034 — AGE graph projection (v0.2A)**

- **RET-34-01** Projected relationships must keep type, direction and input-version references sufficient to re-evaluate mode, temporal and authorization predicates per edge (§4.2).
- **RET-34-02** The projection must define its own consumer checkpoint and rebuild contract; it must not reuse the shared processed marker of the current outbox worker (§1.2).
- **RET-34-03** Traversal must accept an eligibility predicate applied to every intermediate vertex and edge.
- **RET-34-04** Current-only topology must declare itself as such and must not serve as a historical fallback (§8.2).

**F0035 — Hybrid search and authorized scope (v0.2A)**

- **RET-35-01** Seeds, expansion neighbors, edge existence and counts must be authorized before scoring or logging (§8.1 items 1–3).
- **RET-35-02** A rooted query must never broaden to the principal's full visible corpus.
- **RET-35-03** Negative proof (§8.1): with admissible inputs unchanged, changing or revoking an unauthorized node or edge must not change returned IDs, paths, score components, visible counts or selected context.
- **RET-35-04** Every request must pin one execution basis (§4.4); incompatible or missing projections must take a recorded authorized fallback or return an explicit gap.
- **RET-35-05** Implemented modes must be independently switchable. `hybrid_only` and `graph_expand` are baseline modes; `graph_ppr` remains an optional comparator. Unknown, unimplemented or disabled modes must be rejected explicitly.
- **RET-35-06** Expansion must be bounded by hops, candidates, fan-out, per-edge-type caps and wall-clock limits, and must record the path to each candidate (§7.2).
- **RET-35-07** Seed fusion must preserve per-retriever ranks and must not blend uncalibrated raw scores (§7.1).
- **RET-35-08** Backend loss must degrade to authorized lexical retrieval, never unfiltered retrieval.
- **RET-35-09** PPR, if implemented, must be row-stochastic with explicit dangling-node handling (§6.5).

**F0036 — Evidence-aware retrieval and grounded generation (v0.2A)**

- **RET-36-01** The effective evidence budget must be resolved from a model profile naming window and exact tokenizer revision (§7.4); non-positive budgets must be rejected.
- **RET-36-02** The final serialized payload must tokenize within the effective budget, measured after grouping and reauthorization.
- **RET-36-03** Each selected item must carry locator, declared precision, binding references and selection reason; precision is never upgraded by retrieval.
- **RET-36-04** Selected evidence must be revalidated and reauthorized before use; removals must recompute coverage, gaps and token count.
- **RET-36-05** Missing required evidence must produce an explicit gap or abstention (ADR-0046).
- **RET-36-06** Table rows and endorsement effective clauses must not be split in a way that changes meaning.
- **RET-36-07** "Selected" must never be reported as "used"; used-in-answer comes only from `ANSWER_BASIS_LINKED` (ADR-0071).
- **RET-36-08** Trace recording must be non-blocking and sanitized.

**F0067 — Graph Observatory (v0.2B)**

- **RET-67-01** The Observatory may read recorded retrieval events; retrieval delivery does not depend on F0067 (ADR-0072).

### 16.3 Proposed ADR-0076 (draft incorporated; architect refines in F0035 Phase B)

Drafted as [ADR-0076 — Retrieval graph structure is a governed, derived ranking signal](decisions/ADR-0076-governed-graph-assisted-evidence-retrieval.md), still Proposed. The decisions below are its carry-in direction:

- The retrieval plane is a rebuildable derivative of content, assertions and canonical relationships; it owns no truth and writes nothing to the authoritative plane.
- Authorization, root narrowing, `knowledge_mode` and temporal eligibility apply inside every search and traversal operation, before scoring, counting, logging or tracing.
- Each request pins one execution basis; optional projections are used only when exactly compatible, otherwise a recorded authorized fallback or a gap.
- Domain relationship direction and type are preserved; symmetrization exists only inside derived numerical structures.
- Retrieval selects evidence; only the grounded answer establishes use (ADR-0046, ADR-0071).
- Precomputed global graph structures spanning authorization boundaries, including spectral bases, are prohibited unless a reviewed proof shows no unauthorized influence.

The ADR stays Proposed until RET-35-03, temporal isolation and answer-basis linkage proofs pass.

### 16.4 Examples and glossary (BRAIN-EXAMPLES)

| Concept | Worked example | Boundary example | Owner |
|---|---|---|---|
| Bridge evidence under budget | EX-RET-001: exclusion question needs form + endorsement + effective date; selection keeps all three | Near-duplicate form passages fill the budget; selector must prefer the endorsement | F0036 |
| Authorized expansion | EX-RET-002: expansion from a policy to its location schedule within grants | Path through an unauthorized intermediary yields no candidate and no count change | F0035 |
| Source vs canonical mode | EX-RET-003: source mode returns superseded original wording | Canonical mode at the same coordinates returns the amended accepted version | F0035/F0036 |
| Root narrowing | EX-RET-004: account-rooted query stays inside the account | Broader grants still expose no other-account evidence | F0035 |
| Selected vs used | EX-RET-005: five items selected, two cited | Uncited items are "considered, not used" | F0036, ADR-0071 |
| Projection fallback | EX-RET-006: incompatible projection triggers recorded lexical fallback | No silent replay against the current graph | F0035 |

Reuse [EX-FUTURE-001](../examples/future-semantics.md#retrieval-projection). The incorporation adds evidence block, evidence context, retrieval execution basis, retrieval mode, projection compatibility and bridge evidence to the [glossary](../domain/glossary.md#governed-evidence-retrieval), with EX-RET-001–006 in the [examples coverage map](../examples/README.md#governed-retrieval-coverage). They remain illustrative; feature plans must bind stories and executable proofs.

### 16.5 Open decisions

| ID | Decision | Recommendation / owner | When |
|---|---|---|---|
| D1 | Carry §16.2 into F0035/F0036 (and F0033/F0034/F0067 hooks) as PRD inputs | Incorporated 2026-11-06 under the operator request; PM owns later PRDs/stories | Per-feature Phase A remains pending |
| D2 | Draft ADR-0076 from §16.3 | Drafted as Proposed in the incorporation; Architect refines and records proofs | F0035 Phase B approval remains pending |
| D3 | Home for the spectral experiment (§0) | F0068 reserved at v0.4+ following the recommended separate-feature option | Experiment scope/scheduling/cost decision still required before PR-07 |
| D4 | Owner and timing of the §9.2 corpus and runner | Quality engineer + product manager | F0035 Phase A |
| D5 | Answer-generation model profile (window, tokenizer, reserved output) | AI engineer + architect | F0036 Phase B |
| D6 | Package placement (§3.2) | Architect | F0035 Phase B |
| D7 | Initial edge weights and insurance edge profiles (§5.2–5.3) | AI engineer + domain steward | F0035 Phase B, then tuning |
| D8 | Projection consumer checkpoints and rebuild semantics | Architect | F0033/F0034 Phase B; settled before F0035 Phase B approval |
| D9 | Cache-key and replay authorization rules | Security | F0035 Phase B |

### 16.6 Framework path

This handoff is not itself a plan run. The incorporation record above changes planning scope/reservations but grants no per-feature phase, experiment-implementation or activation approval.

1. Record the planning checkout/revision containing the merged F0006 contracts and the applicable operator decisions in "Review outcome". Start framework sessions in the sibling `nebula-agents` repository with `NEBULA_PRODUCT_ROOT` explicitly pointing to this Brain checkout.
2. F0035 Phase A may start first to clarify the downstream user requirements. Run the plan action (`agents/actions/spec/plan.yaml`) with `FEATURE_ID=F0035`, `PHASE=A`, `FEATURE_MODE=existing`, using §0.1, §16.2 (F0035 block), §9.2 and §16.4. The product manager authors PRD, stories and STATUS, resolves D4, and confirms needed dependency/ADR relationships against the incorporation. The architect owns edits to architectural KG shards, including `governed_by`; the PM does not author those bindings. Complete the action's G1–G3 requirements and approval steps.
3. Plan F0033 and F0034 with their RET hooks through their own Phase A/B actions, subject to their prerequisites. Settle projection identities, eligibility/temporal interfaces and D8 consumer checkpoint/rebuild semantics before approving F0035 Phase B. This is a contract-planning dependency; upstream runtime implementation need not precede downstream planning.
4. After F0035 G3 approval and the prerequisite contracts are settled, run its Phase B. The architect refines the existing Proposed ADR-0076, binds the retrieval schemas from §4 under `planning-mds/schemas/`, and resolves D2/D6/D7 with the named owners; Security resolves D9. The architect updates F0035's authored KG shard, including applicable `governed_by` references to `adr:0046`, `adr:0071` and `adr:0076` (now a registered Proposed ADR), and removes `coverage_excluded` only with substantive mappings. Execute the plan action's G4 compile and `validate.py --check-drift` operations, followed by its full G5 exit-validation and Phase B approval sequence; a standalone `validate.py` pass does not replace those gates.
5. Plan F0036 through its own Phase A/B actions using the settled F0035 retrieval interface and its RET requirements. Resolve D5 (answer-generation model profile) in F0036 Phase B. Carry RET-67-01 into F0067's own planning; its rendering remains a later consumer. Each feature retains its own phase approvals and dependency evidence.
6. Plan-review checks each feature with `scripts/validation/validate_plan_readiness.py`, the framework review action and the §16.1 rule map. Implementation follows the approved feature dependencies: F0033/F0034 before production F0035 integration, then F0036.
7. Spectral work (§6, PR-07/PR-08) starts only after baseline measurement, F0068 has its own approved plan, and its scope/scheduling and experiment-cost decision is recorded. That allocation does not block baseline planning.
