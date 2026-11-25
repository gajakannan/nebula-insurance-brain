# Feature Assembly Plan — F0009: Provenance + human-correction lineage

**Created:** 2026-11-24
**Author:** Codex / Architect
**Status:** Phase B approved 2026-11-24 by operator token `approve-phase-b`; implementation Not Started
**Plan Run:** 2026-11-24-bfdbbf04 (A+B, new)
**Rework Run:** 2026-11-24-c32acf46 (PHASE=B, existing). It resolves plan-review 2026-11-24-2af6f972 findings PR-H1 (refused-attempt replay) and PR-H2 (edge semantics). Approved 2026-11-24 by operator token `approve-phase-b`.
**Requirements:** Phase A explicitly approved with token `approve-phase-a` on 2026-11-24; six stories and 41 ACs.
**Governing design:** [ADR-0080](../../architecture/decisions/ADR-0080-bounded-provenance-and-correction-reservations.md) (Proposed; no formal acceptance by this plan).

## Overview

Build an internal exact-root provenance reader over the existing source/assertion/review/temporal records, persist one reserved future-learning identity per new effective CORRECT, and retain auditable non-applied submissions without changing review HTTP behavior. Current authority controls every source before materialization. All runtime paths below are proposed modifications/new files for the future feature action. This plan changes planning artifacts only.

The product is Python/FastAPI/SQLAlchemy, not the C# examples in the generic template. Source parsing, UI, new routes/grants, canonical orchestration and learning remain outside this feature. No cache is introduced: every explanation uses current authority and the same database transaction.

## Build Order

| Step | Scope | Stories | Integration checkpoint |
|---|---|---|---|
| 1 | Frozen domain carriers, schemas and F0011 consumer wiring | S0001/S0005/S0006 | Closed source refs and native/portable conformance; old HTTP contracts unchanged |
| 2 | Additive tables, constraints, append-only and safe rollback | S0002/S0005/S0006 | Real PostgreSQL ownership/semantic guard and downgrade proof |
| 3 | Review preflight, stale retention, atomic reservation and refusal attempts | S0002/S0005 | Fresh-query replay/stale/race/rollback evidence with zero canonical effects |
| 4 | Metadata-first scoped lineage reader and read-facade extension | S0001/S0003/S0004 | All source checks precede protected loads; deterministic bounded results |
| 5 | Temporal/ending/attestation closure, integration and delivery | S0003/S0004/S0006 | All 41 ACs mapped to observed proof; legacy compatibility, install/coverage/reviews |

## Existing Code (Must Be Modified)

| Exact product-relative path | Current state | Required change |
|---|---|---|
| engine/packages/brain-review/src/brain_review/decisions.py | ReviewDecisionService.submit; prior-event replay; has_any_decision rejects a distinct event; stale branch omits value/evidence/comment | Retain stale submission fields; call reservation port after save_decision for an effective CORRECT. Add explicit batch preflight/result carrier without changing event hash or canonical authority |
| engine/packages/brain-persistence/src/brain_persistence/repositories.py | SqlAlchemyReviewItemRepository; v2 correct_assertion_v2; v1 child insertion; ReviewDecisionAuditSink | Persist decided_at=decision.decided_at explicitly for new decisions (the current adapter otherwise uses a different server default); add reservation/refused-attempt ports, source-complete replay discovery, metadata/lock preflight and no-payload refusal audit |
| engine/packages/brain-security/src/brain_security/execution.py | read authorizes payload-derived additional_reads before return; mutate supports pre-operation source reads | Add opt-in metadata-first prepare_reads to read, preserving existing call signatures/defaults and same-UoW audit. Final recheck also runs when no old additional_reads callback exists |
| engine/apps/api/src/brain_api/routes/reviews.py | GET item and POST batch; mutation authorizes all tasks/source reads; maps already-decided to 422 | Preflight batch before any decision effect, commit refusal attempts only, raise existing 422 after that committed typed result. Keep POST request/receipt and GET response fields unchanged |
| engine/apps/api/src/brain_api/deps.py | Composition-root factories over session/execution/content store | Add get_provenance_reader factory; no route registers it yet. Integration tests exercise the exported factory/library boundary |
| engine/packages/brain-persistence/src/brain_persistence/models.py | Existing review/assertion/version rows | Add nullable server-owned correction_lineage_contract marker to ReviewDecisionRow; new table mappings live in provenance_models.py. No old-row backfill |
| engine/pyproject.toml, engine/uv.lock; brain-persistence/pyproject.toml; brain-api/pyproject.toml | Existing workspace/app dependency graph | Register brain-provenance and required inward dependencies; resolve lock in feature action. No Neuron producer change |
| scripts/contracts/sources.yaml and case/behavior/provenance/environment inventories | F0011 installed offline bundle | Add the explicit resources/consumers in contract-inventory.yaml; generate all runtime/Python/AJV artifacts through the shipped toolchain |

## New Files

| Proposed runtime path | Layer / owner | Purpose |
|---|---|---|
| engine/packages/brain-domain/src/brain_domain/provenance.py | Domain / Backend | Frozen query/result/ref/gap/reservation/attempt carriers and invariants; no I/O/schema imports |
| engine/packages/brain-provenance/pyproject.toml; src/brain_provenance/__init__.py; service.py; ports.py; py.typed | Application / Backend | Exported reader, metadata-first repository port, no SQL/content/model dependency |
| engine/packages/brain-persistence/src/brain_persistence/provenance.py | Infrastructure / Backend | Column-only discovery, structural association, exact authorized materialization and deterministic assembly |
| engine/packages/brain-persistence/src/brain_persistence/provenance_models.py | Infrastructure / Backend | Two new scoped append-only row mappings |
| engine/migrations/versions/0016_f0009_provenance_hooks.py | Infrastructure / Backend + DevOps | Additive DDL/semantic triggers and guarded downgrade, rebased if head advances |
| engine/packages/brain-provenance/tests/test_reader.py | Backend/QE | Closure, gaps, ordering/limits and no side-effect proof |
| engine/packages/brain-security/tests/test_provenance_prepared_read.py | Backend/QE | Source denial before load, audit/recheck/expiry and old read regression |
| engine/tests/integration/test_f0009_provenance.py | QE | PostgreSQL exact source/version and mixed-access traversal |
| engine/tests/integration/test_f0009_corrections.py | QE | Batch preflight, races, reservations, stale/replay, failure injection |
| engine/tests/integration/test_f0009_migration.py | QE/DevOps | Direct SQL invariants, immutable legacy snapshots and downgrade guard |
| engine/tests/fixtures/f0009_provenance.py | QE/Backend | Independently authored EX-PROV-001–005 setup/expected identities |
| engine/apps/api/tests/test_f0009_review_compatibility.py | Backend/QE | Same HTTP envelopes/statuses and current-authority replay |

Do not bind nonexistent runtime paths into code-index at plan. Planning artifact bindings are added now; feature G7 adds delivered paths. No new frontend/Neuron source, deployable or container is required. C4 L1/L2 topology remains the existing [context](../../architecture/c4-context.md)/[container](../../architecture/c4-container.md); the feature README adds ER/component views.

## Step 1 — Carriers and Contract Delivery (S0001/S0005/S0006)

The four authored schemas and [inventory](contract-inventory.yaml) are the field-level contract. Register their closed refs plus existing review-decision in F0011 during the feature action. The existing schemas are not HTTP submission/receipt aliases. A failed native reader never falls back to a different profile; exact decimal money remains its stored string/value under the selected compatibility profile.

Public signatures, with all carrier fields (Python 3.13+):

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Any, Literal, Mapping, Protocol
from uuid import UUID
from brain_domain.authx import ResourceKey, AuthorizationDecision
from brain_domain.principal import Principal

JsonObject = Mapping[str, Any]  # validates against the selected node data schema
RootKind = Literal['assertion', 'fact_version']
RecordKind = Literal['assertion', 'evidence', 'content_artifact', 'document_version',
 'source_document', 'interpretation_run', 'review_decision', 'review_attempt',
 'learning_reservation', 'fact_version', 'fact_change', 'derivation_reference']

@dataclass(frozen=True, slots=True)
class RecordRef:
    kind: RecordKind
    id: UUID

@dataclass(frozen=True, slots=True)
class ProvenanceQuery:
    root: RecordRef  # only RootKind is valid here
    anchor: ResourceKey
    contract: Literal['provenance-query/v1'] = 'provenance-query/v1'

@dataclass(frozen=True, slots=True)
class ProvenanceRecord:
    kind: RecordKind
    id: UUID
    data: JsonObject

EdgeKind = Literal['corrected_from', 'supported_by', 'ending_evidence', 'located_in',
 'interpreted_in', 'interprets', 'artifact_of', 'version_of', 'reviews', 'created_assertion',
 'reserved_learning', 'recorded_decision', 'split_of', 'changed_from', 'changed_to',
 'attested_by', 'derived_from']

@dataclass(frozen=True, slots=True)
class ProvenanceEdge:
    kind: EdgeKind  # allowed (source kind, target kind) pairs: Edge Semantics table
    source: RecordRef
    target: RecordRef

@dataclass(frozen=True, slots=True)
class MetadataGap:
    record: RecordRef
    field: str
    reason: Literal['LEGACY_UNQUALIFIED', 'METADATA_UNAVAILABLE', 'DERIVATION_UNAVAILABLE']

@dataclass(frozen=True, slots=True)
class ProvenanceResult:
    root: RecordRef
    tenant_id: UUID
    knowledge_base_id: UUID
    completeness: Literal['COMPLETE', 'INCOMPLETE']
    records: tuple[ProvenanceRecord, ...]
    edges: tuple[ProvenanceEdge, ...]
    gaps: tuple[MetadataGap, ...]
    contract: Literal['provenance-result/v1'] = 'provenance-result/v1'

@dataclass(frozen=True, slots=True)
class LearningCandidateReservation:
    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    review_decision_id: UUID
    original_assertion_id: UUID
    corrected_assertion_id: UUID
    reviewer_principal_id: UUID
    reserved_at: datetime
    contract: Literal['learning-candidate-reservation/v1'] = 'learning-candidate-reservation/v1'

@dataclass(frozen=True, slots=True)
class ReviewSubmissionAttempt:
    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    review_item_id: UUID
    review_batch_id: UUID
    original_assertion_id: UUID
    reviewer_principal_id: UUID
    submitted_at: datetime
    event_sha256: str
    assertion_version: int
    action: Literal['ACCEPT','CORRECT','REJECT','BLOCKED']
    reason_code: str | None
    corrected_value: JsonObject | None
    evidence: JsonObject | None
    reviewer_comment: str | None
    outcome: Literal['ALREADY_DECIDED','BATCH_REFUSED']
    authorization_decision_id: UUID
    contract: Literal['review-submission-attempt/v1'] = 'review-submission-attempt/v1'
```

Serialization uses existing snake_case wire names, UUID strings and timezone-aware ISO timestamps. `RecordRef` preserves kind+ID, so different record kinds cannot collide. Null represents stored unavailable/legacy data only; an inapplicable model field on a human correction is not a missing producer. Enforce one record per (kind, ID), root existence with matching kind/ID, all edge endpoints present, and COMPLETE iff there are no applicable metadata gaps. Domain checks enforce these graph invariants beyond schema shape. Sort records by (kind, UUID), edges by (kind, source kind/ID, target kind/ID), gaps by (record kind/ID, field, reason). No user-supplied actor, owner, policy or authority token is a query field.

### Edge Semantics (rework run 2026-11-24-c32acf46, resolves plan-review PR-H2)

Every edge reads `<source> <kind> <target>`. Only the pairs below are valid; `provenance-result-v1.schema.json` enforces them per kind (`edges.items.oneOf`), and the domain rejects any other pair. The retired name `reviewed_by` is replaced by `reviews`, with the direction reversed.

| Kind | Source kind | Target kind | Stored basis |
|---|---|---|---|
| corrected_from | assertion | assertion | HUMAN_REVIEW child -> `original_assertion_id` |
| supported_by | assertion | evidence | `assertion_evidence.assertion_id` |
| supported_by | fact_version | evidence | version `evidence.refs[]` (assertion_evidence IDs) |
| ending_evidence | fact_version | evidence | version `evidence.ending_refs[]` |
| located_in | evidence | content_artifact | `assertion_evidence.artifact_id` |
| interpreted_in | assertion | interpretation_run | `assertion.run_id` |
| interprets | interpretation_run | content_artifact | `semantic_interpretation_run.artifact_id` |
| artifact_of | content_artifact | document_version | `content_artifact.document_version_id` |
| version_of | document_version | source_document | `document_version.source_document_id` |
| reviews | review_decision | assertion | decision's `review_item.assertion_id` |
| reviews | review_attempt | assertion | attempt `original_assertion_id` |
| created_assertion | review_decision | assertion | `corrected_assertion_id` |
| reserved_learning | review_decision | learning_reservation | `learning_candidate_reservation.review_decision_id` |
| recorded_decision | fact_version | review_decision | version `review_decision_id`; implies no acceptance by review |
| split_of | fact_version | fact_version | remainder `split_of_version_id` (same slot) |
| changed_from | fact_change | fact_version | `canonical_fact_change.from_version_id` |
| changed_to | fact_change | fact_version | `canonical_fact_change.to_version_id` |
| attested_by | fact_version | content_artifact | artifacts behind the version's refs/ending_refs, emitted only when an `attested_*` date is exposed (the `current_attesting_artifact_keys` join) |
| derived_from | assertion or fact_version | derivation_reference | stored derivation/input reference only |

Graph invariants, beyond the schema:

- Edges are unique by (kind, source, target). The schema sets `uniqueItems`.
- Both endpoints of every edge appear in `records`.
- Every non-root record is connected to the root when edge direction is ignored. An unreachable record is an assembly defect, never padding.
- `corrected_from` and `split_of` are directional ancestry and must be acyclic.
- One stored link yields exactly one edge. The reader never infers an edge, e.g. corrected_from from a split, or support from a review decision.

QE derives expected edges for EX-PROV-001–005 from this table before implementation output exists (S0006 AC5).

Checkpoint: [contract-examples.json](contract-examples.json) passes local Draft202012 validation with a closed registry. It includes an edge-bearing correction lineage and negative cases for reversed direction, a retired kind, a duplicate edge and a wrong endpoint kind. Runtime feature tests must also prove JSON Schema/generated Pydantic and the portable headless AJV subset, original native differential cases and install outside a source checkout. No runtime conformance is claimed by plan.

## Step 2 — Persistence and Migration (S0002/S0005/S0006)

Use the complete base DDL in [migration-design.sql](migration-design.sql). Existing owner unique keys from migrations 0005/0006 satisfy the composite references. There is no FK to a future LearningCandidate table and no nullable field on a mutable review item.

Add these SQL validation functions/triggers with `SECURITY INVOKER SET search_path=pg_catalog,public`, using SQLSTATE `check_violation` and constant messages without values:

1. `brain_f0009_append_only`: reject UPDATE/DELETE per row and TRUNCATE per statement on both new tables. Owner columns cannot be changed because no update is allowed. No CASCADE on parent links.
2. `brain_f0009_reservation_guard` BEFORE INSERT: select the decision, item and original/child assertion; require one tenant/KB; the decision is non-stale CORRECT, its corrected_assertion_id equals NEW.corrected_assertion_id, its item/batch references agree, its reviewer/time equal NEW.reviewer_principal_id/reserved_at, the item's assertion is NEW.original_assertion_id, and the child is HUMAN_REVIEW with original_assertion_id pointing to that original. The verified principal is supplied by the existing review boundary. Require matching semantic contract versions; existing F0006 guards own the child's complete v2 semantics/evidence.
3. `brain_f0009_attempt_guard` BEFORE INSERT: item matches NEW.original_assertion_id/batch and ownership; authorization_decision_id names the staged audit_event whose actor/resource/action matches reviewer/item/annotate authority. The row outcome is non-applied only; it contains no corrected child/candidate identity.
4. Add `review_decision.correction_lineage_contract smallint NULL` with a CHECK allowing NULL or 1, initially no default/backfill. A server-owned BEFORE INSERT trigger unconditionally stamps 1 for new rows, overriding submitted values. Existing rows remain NULL and append-only. `brain_f0009_reservation_guard` requires marker=1, so historical decisions cannot acquire fabricated reservations. A DEFERRABLE INITIALLY DEFERRED constraint trigger on newly inserted decisions requires every non-stale CORRECT with a child to have exactly one matching reservation by transaction end. The application normally inserts after save_decision; the constraint trigger refuses a missing row rather than synthesizing one. The unique decision/child constraints make a later second reservation impossible. This enforces atomicity without timestamps, transaction-ID comparisons or a future learning table.

Append-only trigger protection for review_decision UPDATE/DELETE/TRUNCATE is added if absent after inspecting the then-current migration chain; this protects the decision half of the new linkage. Existing assertion/source/version guards remain. The migration does not rewrite source artifacts, old assertions/evidence/decisions, canonical rows or old hashes.

Upgrade: pause review writers; run read-only legacy snapshots/preflight; acquire table locks in existing parent-to-child order; install new tables/constraints/functions/triggers and supporting indexes in one migration transaction; verify keys and zero new rows; resume writers after package/schema install. No data backfill.

Downgrade: quiesce writers, then in the same transaction acquire ACCESS EXCLUSIVE on the two new tables and review_decision (fixed lexical order), refuse if either new table has any row, and only then drop new triggers/indexes/tables/functions and the new nullable correction_lineage_contract column. The lock prevents an emptiness-check/write race. No `CASCADE`, truncation, forced-data-loss path or old-row mutation. After real reservations/refused submissions exist, rollback means redeploying a compatible reader or forward repair while retaining the schema/data; an old writer that cannot satisfy the reservation constraint cannot resume silently. DevOps proves empty down/up and populated refusal.

Checkpoint: PostgreSQL direct inserts challenge composite owners, wrong original/child/reviewer/decision links, new-decision atomic reservation, historical NULL-marker refusal, UPDATE/DELETE/TRUNCATE, duplicate constraints and audit failure rollback. The then-current head is 0015; feature G0 rebases 0016 if necessary.

## Step 3 — Existing Review Boundary (S0002/S0005)

Add repository ports to the existing `ReviewItemRepository` (the same unit of work, no new commit in a port):

```python
async def lock_batch_items(self, ids: tuple[UUID, ...]) -> None: ...
async def reserve_learning_reference(self, decision: ReviewDecision) -> UUID: ...
async def record_refused_submission(
    self, request: DecisionRequest, *, outcome: str,
    authorization: AuthorizationDecision, submitted_at: datetime
) -> UUID: ...
```

`reserve_learning_reference` resolves the item/ownership from trusted stored rows, generates one server UUID, uses the decision's exact reviewer/time, inserts after `save_decision`, validates through F0011 and flushes. Unique decision/child IDs and the trigger guard prevent duplicate or unrelated reservation. Failure propagates before audit/commit; the existing mutation facade rolls back every staged business row. Replay never calls this method.

Batch logic, preserving the existing POST receipt schema:

1. Authenticate through existing dependency. `execution.mutate` authorizes all review_task:annotate keys and metadata-only source READ keys before any claim payload/decisions are loaded. Extend source discovery to every existing original/child/decision evidence source, including v1 sources where attributable and replayed event sources; never silently skip a modern source because its root has legacy ancestry. Unregistered legacy references remain explicitly qualified, never fabricated.
2. Lock every review_item FOR UPDATE in ascending UUID before checking its decision state. Recheck the discovery fingerprint after locks: a newly added source/decision/child must fail safely and retry as a fresh operation rather than using an incomplete authorized source set. Resolve submitted evidence.source as an immutable local artifact identity and prove it belongs to the item’s source chain; never fetch an external URI or trust a request locator as authority. Existing resource-access locks remain held. Reject a mismatched batch/item with the existing 422 after audit, never before task access.
3. Compute the unchanged event hash. Replay identity comes only from ReviewDecision rows. A prior effective/stale ReviewDecision with the same (item, event) returns its original duplicate identity, with no extra review_decision_recorded event or reservation; the normal per-request authorization audit remains. A stored refused attempt never short-circuits a request (operator decision 2026-11-24, "always re-evaluate", resolving plan-review PR-H1). A submission that matches a refused attempt is evaluated against current state like any new submission, so a sibling refused only because of another item applies when resubmitted in a clean batch.
4. Preflight all nonduplicate items before any correction. If any has a distinct existing decision, prepare a `RefusedBatch` covering every nonduplicate submission: ALREADY_DECIDED for each item that has a distinct decision, BATCH_REFUSED for the others. Duplicates create no attempt.
   - Attempt rows are get-or-create on the unique key (review_item_id, event_sha256, outcome), under the item locks already held. A matching row is reused unchanged: its first submitted payload, actor/time and authorization_decision_id stay as stored, and the table stays append-only. A changed outcome for the same event (BATCH_REFUSED earlier, ALREADY_DECIDED now) appends a new row.
   - Store the submitted revision/value/evidence/comment and verified actor/time without returning them.
   - No child, ReviewDecision, reservation or item status change is staged for a refused batch.
   - When a later effective or stale ReviewDecision shares (item, event) with an earlier attempt, both rows coexist. The decision governs later replays because step 3 checks only decisions, and the reader exposes the attempt as history through its `reviews` edge.
5. Each refused request writes one `review_submission_refused` audit per attempt it refused, whether that attempt row is new or reused. The audit records an event per request; the attempt rows record distinct submissions. Each audit carries a safe attempt ID/outcome, verified actor, matching authorization ID/policy/grant revision; no value/comment/excerpt). Return the typed refusal from the operation so only refusal records/audit commit; after `execution.mutate` returns, the route maps that result to the unchanged sanitized 422. If audit/storage fails, return existing 503 with no success. Do not raise inside the operation and accidentally roll back the very refusal attribution this story requires.
6. For a clean batch, call the existing submit service. On stale revision, retain submitted corrected_value/evidence/reviewer_comment in its existing non-applied ReviewDecision, keep current stale routing, create no child/reservation. On BLOCKED keep current blocking semantics; no new reopen/second-review policy is introduced. ACCEPT/REJECT create no reservation.
7. Effective CORRECT uses existing v1/v2 child creator, saves decision, reserves reference and writes existing review_decision_recorded audit. Mutate commits the whole batch once; a failure anywhere leaves no partial successful correction/decision/reference. Any failed validation keeps its existing sanitized status and durable authorization failure audit. Source evidence is unchanged.

`RefusedBatch(attempt_ids: tuple[UUID,...])` is an internal tagged result, not a new HTTP response. Do not silently return 200 for a losing submission or add a reservation field to old receipts. The existing `review_decision_recorded` outcome description is unchanged; for new refusal audit the safe description is “Review submission not applied.”, event_type `review_submission_refused`, operation_outcome `failed`, payload keys `attempt_id` and `outcome` only. Existing audit metadata supplies verified principal, trace, policy/revision and authorization ID.

### HTTP Responses / Casbin

| Existing surface | Current successful body | Failure behavior / change |
|---|---|---|
| POST /reviews/batches/{review_batch_id}/decisions | 200 ReviewDecisionReceiptOut with existing decision_ids/applied/duplicate/stale/blocked fields | 404 missing/inaccessible task/source; 422 existing decision/shape/evidence conflict (now auditable); 503 authority/storage/audit unavailable. Framework request validation keeps existing 422. No added response fields |
| GET /reviews/{review_item_id} | 200 ReviewItemOut, same latest decision projection | Same 404/503 behavior. Do not expose attempt rows or reserved references on this legacy route |
| GET /facts/{factSlotId} and POST commit | Existing payload/status and guards | Regression only; no new lineage field, reason vocabulary or canonical orchestration |

Use real policy resource strings: `review_task:annotate`, `review_task:read`, `fact_slot:read`, `content_artifact:read`. The prose `review:annotate` shorthand in the PRD maps to the existing typed review_task resource. No policy.csv/Casbin model edit or new grant; parent/classification dependencies remain conjunctive. ProblemDetails retain code/traceId and application/problem+json.

### Mutation Traceability

| Entry/action | Endpoint/service | Carrier/effect | Authority/concurrency | Validation/failure | Persistence/audit proof |
|---|---|---|---|---|---|
| Existing reviewer submits CORRECT (S0002) | POST batch -> execution.mutate -> batch preflight -> ReviewDecisionService.submit | New child + decision; original unchanged | Verified reviewer, review_task:annotate + all source READ; sorted item locks and unchanged hash | Stale non-applied; unresolved/invalid or losing batch keeps existing 422/no correction | Fresh-session child/decision and existing audit; whole-batch rollback; no canonical version/outbox |
| Effective correction reserves reference (S0005) | Same POST/service -> repository.reserve_learning_reference | One append-only decision/child-scoped reservation | Same UoW, unique decision/child, new-decision marker and deferred DB guard | Any reference/audit error rolls correction back; replay no extra row | Fresh-session same UUID; zero learning/model/dataset calls |
| Losing submission retention (S0002) | Same POST -> preflight -> RefusedBatch | Get-or-create attempt rows + one refusal audit per refused request | Same current task/source authority and locks; unique item/event/outcome; refused attempts never replay | Preserve 422 after audit-only commit; resubmitting a refused sibling alone re-evaluates and can apply | Attributed submitted value/evidence retained in protected table; no accepted decision/child/reservation for the refused request |
| Operator upgrade/rollback (S0006) | Alembic proposed 0016 | New tables/guards; no legacy backfill | Deployment authority, quiesced writers/table locks | Populated downgrade refuses before drop | Compare original bytes/IDs; down/up empty and populated refusal logs |

## Step 4 — Metadata-First Internal Reader (S0001/S0004)

```python
from collections.abc import Awaitable, Callable, Sequence
from brain_domain.authx import Action, NO_FILTER, RequestedScope
from brain_security.execution import AuthorizationExecution

@dataclass(frozen=True, slots=True)
class ProvenancePlan:
    root: RecordRef
    anchor: ResourceKey
    tenant_id: UUID
    knowledge_base_id: UUID
    record_refs: tuple[RecordRef, ...]
    source_keys: tuple[ResourceKey, ...]
    metadata_fingerprint: str

class ProvenanceRepository(Protocol):
    async def discover(self, query: ProvenanceQuery) -> ProvenancePlan: ...
    async def materialize(self, plan: ProvenancePlan) -> ProvenanceResult: ...

class ProvenanceReader:
    def __init__(self, repository: ProvenanceRepository,
                 execution: AuthorizationExecution) -> None: ...
    async def read(self, principal: Principal, query: ProvenanceQuery, *,
                   trace_id: str, requested: RequestedScope = NO_FILTER) -> ProvenanceResult: ...

# Add one optional keyword to AuthorizationExecution.read, leaving all current
# parameters/default behavior and the post-load additional_reads hook intact:
# prepare_reads: Callable[[], Awaitable[Sequence[ResourceKey]]] | None = None
```

Reader execution:

1. Validate query field/UUID shape only; this cannot authorize anything. `execution.read` authorizes/locks query.anchor for READ first; unknown/inaccessible anchor gets the existing AuthorizationDenied with non-disclosing mapping.
2. `prepare_reads` calls repository.discover, holding only metadata privately. Select explicit ID/ownership/link/version columns, JSON evidence ref IDs and needed temporal window metadata; never load Assertion.value, review corrected_value/comment, excerpt/text, model payload or source bytes. No ORM entities that populate identity-map protected fields.
3. Prove root association: fact_version must have slot_id=anchor.id for fact_slot; assertion must belong to the anchor's review_item assertion or its stored correction ancestry/children for review_task; content_artifact anchors must lie on the root assertion/run/evidence chain. Reject arbitrary-anchor, owner mismatch or cross-slot split links before payload. Canonical roots use fact_slot anchors only; no broad tenant membership fallback.
4. Discover the finite closure and its current source/resource keys. All rows share the root tenant/KB. Include review tasks for exposed review decisions/attempts; if the principal lacks review_task READ, the whole explanation is denied even when fact READ is held. Reserve rows inherit their decision/task authority. For every evidence artifact, original/child/ancestor, ending ref and attestation source, include CONTENT_ARTIFACT READ. Canonical endpoint versions include their FACT_SLOT READ; source model/run/doc nodes inherit their artifact READ. There is no new authorization resource.
5. Return sorted unique access keys. The new read hook evaluates/locks them inside the same facade/UoW before calling load; any denied/missing requirement aborts the entire result and persists existing denial audit. No nested execution.read, new transaction, cached grants or payload-derived implicit fallback.
6. `load` calls repository.materialize(plan): in deterministic row-kind/UUID order lock/check selected semantic rows FOR SHARE after resource locks; re-discover/refingerprint scalar topology and compare to the plan before loading sensitive columns. A concurrent append/version/ownership change either linearizes before this snapshot or raises sanitized LINEAGE_UNAVAILABLE and writes a failed audit; never reselect different endpoints silently. A source-authority expiry is rechecked before protected load and again after it, even without the existing additional_reads callback. Share locks block concurrent revocation until the response's audit commit.
7. Assemble only planned/authorized records, with exact stored serializers, deterministic order, honest metadata availability and named gaps. Validate output through installed F0011 before audit commit. Oversize/profile/contract invariant failures expose no partial graph; existing safe 500/503 mapping is used and business effects stay zero.
8. Facade appends all authorization decisions, commits once and returns. Repository/reader never commits, parses, calls a model or writes canonical/learning state. No explanation cache.

Traversal limits are fixed design constants: 256 assertion-correction links (matching F0006), 2048 typed records, 8192 edges and the F0011 byte/depth/node limits for serialization. Refuse immediately at limit+1 without returning partial IDs/counts. Cycle/limit/topology-change category is LINEAGE_UNAVAILABLE; bad structural association, dangling protected target and denied/missing root use non-disclosing LINEAGE_NOT_FOUND/AuthorizationDenied. Unknown field metadata is not a dangling record: after complete access checks it produces INCOMPLETE plus METADATA_UNAVAILABLE. Missing mandatory v2 carrier/invalid semantics is an integrity failure, never downgraded to legacy.

Completeness: COMPLETE means every traversed required identity resolves, all required access was checked, and the metadata applicable to these actually delivered producers is present. HUMAN_REVIEW has no model producer, so absence of its own model version is inapplicable; its original machine node retains its recorded context. Legacy unqualified origin/semantics or an unavailable referenced derivation producer yields INCOMPLETE; it does not create a source or imply no evidence is needed. No source text is logged to repair a gap.

Checkpoint: denied current source triggers zero protected `materialize` calls. Root-only grants never suffice for source or review record payloads. Compare missing/cross-scope and revoked/ending/ancestor/attestation/replay outputs including logs. Unit/fake-store proof verifies decision/load/audit order; PostgreSQL multi-session proof verifies grant-revision/revocation locking and concurrent appends without payload leakage.

## Step 5 — Temporal and Source Closure / Delivery (S0003/S0004/S0006)

- Exact fact_version nodes use the shipped FactVersionOut normalization; `temporal.split_of_version_id` is read as same-slot predecessor metadata, with the original timestamps/value/evidence intact. Preserve validity_unknown_from and unknown-end fields; no call chooses a new value at “now.” Canonical version rows and canonical_fact_change remain read-only.
- Follow the root version's stored supporting refs and ending_refs as different edge kinds; resolve each evidence ID to its assertion and artifact, then its correction ancestors and producing run/document/artifact. Never infer direct evidence from a review or turn a split link into corrected_from.
- Include direct incoming canonical changes (to=root), outgoing changes (from=root) and their exact endpoints; recurse only the predecessor ancestry of those endpoints, not outgoing chains of every discovered version. Bound the set globally, deduplicate typed refs and use tri-color cycle detection for directional ancestry edges. A legitimate split graph/DAG with shared predecessors is not a cycle. Link-only change endpoints never trigger an unbounded slot scan.
- Attestation source discovery reuses the metadata joins behind SqlAlchemyCanonicalFactRepository.current_attesting_artifact_keys for the exact stored temporal window and every split predecessor whose dates are exposed. No selected document dates are disclosed until those source reads pass. If needed dates could only be reconstructed from a later human selection, report unavailable and retain stored metadata; never substitute a current date for the stored attestation. F0008 second-remediation commit response is unchanged.
- CanonicalFactChangeRow has reason/from_version_id/to_version_id/created_at but no actor or commit column. Return those exact values; derive actor/commit only if an unambiguous stored canonical_commit/audit relation supplies them, otherwise null and an availability gap. Do not invent a new column or guess an actor from the current request.
- Existing derivation references may be passed through only as typed stored references/input IDs under the same source/slot access; no derivation table/engine is added. A nonexistent producer is explicit DERIVATION_UNAVAILABLE. F0018 owns dependency tables and F0065 assessment lineage; this feature must not fabricate their records.

### Developer and QE Proof

Backend owns fast domain/review/provenance/security unit tests for each changed operation and denial, then PostgreSQL integration tests. Existing `engine/apps/api/tests/test_reviews.py` and `test_facts.py` remain regression gates. No new UI test is needed; headless AJV conformance is contract tooling only. QE authors independent expectations/negative cases before consuming implementation output. The future feature action records exact commands and expected/actual IDs/outcomes for EX-PROV-001–005 and each individual AC.

Proposed verification from product root after implementation (paths above are not created by plan):

```bash
uv run --project engine python -m pytest engine/packages/brain-provenance/tests engine/packages/brain-review/tests engine/packages/brain-security/tests
uv run --project engine python -m pytest engine/tests/integration/test_f0009_provenance.py engine/tests/integration/test_f0009_corrections.py engine/tests/integration/test_f0009_migration.py engine/apps/api/tests/test_f0009_review_compatibility.py
uv run --project engine python scripts/contracts/generate.py --check
uv run --project engine python scripts/contracts/check.py
pnpm --dir experience contracts:check
```

DevOps uses the established integration PostgreSQL fixture/Compose profile rather than inventing a connection string; no credential appears in a report. Validate actual invocation syntax at feature G0 and record every command's real exit/result. Installed-package smoke verifies the exported reader and F0011 resources outside checkout. Coverage floor is 80% changed executable lines, alongside all PostgreSQL obligations; passing unit coverage cannot substitute for concurrency/rollback proof.

## Acceptance Criteria to Implementation / Proof Map

The matrix below maps every AC separately. Runtime feature evidence fills exact test IDs/results; unchecked planned proof is not a completed AC.

| Story AC | Build step | Specific proof |
|---|---|---|
| F0009-S0001 AC1 | 4 | Exact v2 assertion/source metadata and stored precision round-trip |
| F0009-S0001 AC2 | 4 | Exact requested canonical version; no latest substitution |
| F0009-S0001 AC3 | 4 | Stored producer hashes/version values; missing metadata gap |
| F0009-S0001 AC4 | 5 | Direct evidence vs stored/undelivered derivation distinction |
| F0009-S0001 AC5 | 4 | Missing link, tri-color cycle and each limit+1 refuse; edge-table pair/uniqueness/reachability invariants |
| F0009-S0001 AC6 | 4 | Zero parse/model/canonical calls and existing read audit |
| F0009-S0001 AC7 | 4 | Missing/inaccessible equivalence; authorized legacy incomplete |
| F0009-S0002 AC1 | 3 | Fresh-session decision/item/batch/actor/value/evidence/child linkage |
| F0009-S0002 AC2 | 3 | v2 child remains v2; original/source/canonical byte snapshots unchanged |
| F0009-S0002 AC3 | 3 | Decision/child/reservation/audit fault-injection whole-batch rollback |
| F0009-S0002 AC4 | 3 | Same event replay, current reauthorization, zero second business audit |
| F0009-S0002 AC5 | 3 | Stale submitted payload retained, non-applied, no child/reservation |
| F0009-S0002 AC6 | 3 | Two-session competing event and mixed-batch rejection retain attempt; BATCH_REFUSED sibling resubmitted alone applies; repeat refusal reuses the row and writes a new audit |
| F0009-S0002 AC7 | 3 | Action/unresolved/malformed matrix with no fabricated child/reservation |
| F0009-S0002 AC8 | 3 | Reviewer identity spoofing rejected and zero canonical/outbox writes |
| F0009-S0003 AC1 | 5 | Exact temporal coordinates/unknown/legacy metadata preserved |
| F0009-S0003 AC2 | 5 | Remainder same-slot predecessor with original payload/evidence/timestamps |
| F0009-S0003 AC3 | 5 | Correction/split/change edge kinds and real nullable actor/commit fields |
| F0009-S0003 AC4 | 5 | Distinct support/ending edges and current READ on both |
| F0009-S0003 AC5 | 5 | Reviewed uncommitted assertion vs independently committed stored link |
| F0009-S0003 AC6 | 5 | Broken/cross-slot/cyclic owner-aware history refusal on PostgreSQL |
| F0009-S0003 AC7 | 5 | Read-only version/change snapshots; F0008 guard/temporal regressions |
| F0009-S0004 AC1 | 4 | Metadata source closure; denied source means zero protected loads |
| F0009-S0004 AC2 | 4 | Cross-tenant/KB/mixed-access refusal exposes no partial graph |
| F0009-S0004 AC3 | 5 | Revoke ancestor/ending/attestation while retaining root/historical access |
| F0009-S0004 AC4 | 4 | Exhaustive existing-role/nonmember/unverified/external matrix |
| F0009-S0004 AC5 | 4 | Spoofed IDs/owners and parent+classification conjunction; direct SQL keys |
| F0009-S0004 AC6 | 4 | Durable authorization audit, no business effects, expiry/revocation races |
| F0009-S0004 AC7 | 4 | Log/output non-disclosure on every traversal/replay category |
| F0009-S0005 AC1 | 2 | One valid new CORRECT decision/original/child/actor reservation |
| F0009-S0005 AC2 | 3 | Reservation or audit failure atomically rolls correction back |
| F0009-S0005 AC3 | 3 | Duplicate/concurrent events preserve one reference ID |
| F0009-S0005 AC4 | 3 | All non-effective actions + historical rows produce no reference |
| F0009-S0005 AC5 | 3 | Zero learning/promotion/corpus/holdout call and byte counters |
| F0009-S0005 AC6 | 4 | Reference inherits current complete correction/task/source authority |
| F0009-S0006 AC1 | 2 | Legacy byte-for-byte snapshots with no fabricated backfill |
| F0009-S0006 AC2 | 2 | Empty down/up and populated downgrade refusal under writer locks |
| F0009-S0006 AC3 | 1 | Per-resource consumer inventory + installed schema/native/portable conformance |
| F0009-S0006 AC4 | 3 | Old HTTP route/request/receipt/fact/commit fixture parity |
| F0009-S0006 AC5 | 5 | EX-PROV-001–005 PostgreSQL expected/actual repro and denial audit |
| F0009-S0006 AC6 | 5 | 41/41 AC evidence, changed-code coverage and required signoffs |

## Scope Breakdown and Handoffs

| Owner | Work / completion boundary |
|---|---|
| Backend | Domain/application/infra changes, schema inventory, atomic review integration, protected reader and fast tests |
| QE | Independent scenario fixtures, all AC mappings, real PostgreSQL/concurrency/rollback/security-negative proof, coverage |
| Security Reviewer | READ-before-materialize, current grants/replay, no protected logs, scopes/trigger privilege review |
| Code Reviewer | Independent correctness, native compatibility and no canonical/producer scope expansion |
| DevOps | Migration ordering/locks, old-writer compatibility, package install and safe downgrade/forward-repair procedure |
| Architect | G0 design reconciliation and proposed ADR proof gates; accepts no semantic change silently |
| Frontend / AI | No new UI/model behavior. Headless shared contract checks remain part of F0011 tooling; consult only if a shared consumer regression appears |

## Integration Checkpoints and Completion Criteria

- Step 1: all authored examples validate; new resource/consumer entries and closed refs integrate with F0011; existing OpenAPI paths/status/DTO fields unchanged.
- Step 2: PostgreSQL rejects invalid owner/decision/child/reviewer/reservation links and mutation/truncate; no seeded legacy bytes change; populated downgrade refuses under locks.
- Step 3: replay/stale/racing/mixed batches have specified effects and fresh-query audit; reservation failure leaves zero business rows; annotation writes zero canonical rows.
- Step 4: metadata discovery authorizes all sources before protected loads; complete current-authority/race/limit matrix passes with no partial output/log leak.
- Step 5: exact temporal/ending/attestation lineage and EX-PROV expected/actual reproduction pass; 41/41 AC mapping, at least 80% changed-code coverage and all required roles pass in the later feature action. Planning checks are not runtime proof.

## Risks and Blockers

| Risk | Mitigation / owner |
|---|---|
| Shared authorization-facade regression | Opt-in prepare_reads, default-compatible callers, final expiry recheck and existing F0002/F0007/F0008 regression suite; Backend + Security |
| Existing elevated application DB role | Explicit ownership/application tests and SECURITY INVOKER guards; F0018 retains RLS/role remediation |
| Refused batch audit accidentally rolled back | Typed refusal result commits audit-only state before route raises unchanged 422; QE mixed-batch/fault injection |
| Refused attempt blocking a later valid submission | Replay identity from ReviewDecision only; attempts are history, never a replay key (PR-H1); QE resubmission case |
| Edge semantics drifting between producer, QE and later consumers | Closed per-kind endpoint table enforced in the schema and the domain; negative contract cases (PR-H2); Architect |
| Legacy provenance cannot meet modern completeness | Explicit authorized INCOMPLETE gaps, no invented producer/metadata/backfill; Architect |
| Reservation invariant accidentally applied to historical decisions | Nullable immutable server marker for new inserts plus deferred constraint and direct-SQL legacy refusal proof; Backend + Architect |

## DI Registration / Runtime Deployment

`get_provenance_reader` constructs SqlAlchemyProvenanceRepository and the current AuthorizationExecution from the same AsyncSession. The new application package depends inward on brain-domain/security/contracts; persistence implements its port. brain-review's reservation methods stay on its repository port, avoiding a brain-review <-> brain-provenance dependency cycle. Register package workspace sources/locks in feature action. No cache, new container, environment requirement, credentials, policy release or Casbin sync.

## Planning Status and Follow-ups

The four schemas, proposed SQL, inventory and examples are design artifacts. Their runtime/generated snapshots, migration, reader, tables and proof remain Not Started. Both explicit operator approvals are recorded (Phase A approve-phase-a; Phase B approve-phase-b). G4 compiled authored KG shards; the G5 journal/manifest records ordered pre-approval checks and post-approval refresh/publication. Automated publication writes the approved plan manifest last. A separate plan-review must precede implementation. No feature role report or evidence index is created during plan.
