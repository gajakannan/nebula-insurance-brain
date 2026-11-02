# Feature Assembly Plan — F0006: Assertion plane + origin + interpretation basis

**Created:** 2026-11-01
**Author:** Architect
**Status:** Phase B design approved by operator token `approve-phase-b` on 2026-11-01; implementation not started
**Run:** `2026-11-01-7d6d19ce` (A+B, new); Phase A approved with `approve-phase-a`. Phase B rework `2026-11-01-512e9303` (correction basis and v2 correction persistence, plan-review AR-1/AR-2) re-approved with `approve-phase-b` on 2026-11-01.
**NEBULA_PRODUCT_ROOT:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`

## Overview and Scope

Implement the approved five stories and 35 ACs using additive assertion semantics, deterministic structural admission and current-consumer safeguards. [ADR-0075](../../architecture/decisions/ADR-0075-versioned-assertion-semantics-and-admission.md) records the design; it and ADR-0065 remain Proposed pending their runtime proofs. This file is an implementation specification, not evidence of delivered code.

No new deployable, UI, HTTP assertion route, pipeline selection, permission grant, durable drop service, live open producer or full canonical orchestrator. Existing `direct-baseline` and v1 content writer stay default. F0004 origin qualification remains authoritative. Existing context/container diagrams remain applicable; the feature README supplies component and ER diagrams.

## Existing Code and Reconciliation

| Existing path | Current behaviour | Required change / boundary |
|---|---|---|
| `engine/packages/brain-contracts/src/brain_contracts/result.py` | Strict v1 `CandidateAssertion` (7 fields), `InterpretationResult`; shared with neuron | Preserve classes; add explicit dispatch in a new module, no permissive fallback |
| `engine/packages/brain-persistence/src/brain_persistence/models.py` | Assertion has 13 scalar columns and two ORM relationship attributes; raw MACHINE_EXTRACTION/HUMAN_REVIEW, proof version, basis, value and ownership | Add version discriminator default 1; retain all original data |
| `engine/apps/worker/src/brain_worker/document_delivery.py` | `DocumentResultImporter.run_one` validates v1, rejects entity/relationship output, writes assertion/evidence/review and delivery atomically | Keep v1-only; explicitly reject v2/unknown versions before effects; no new extraction activation |
| `engine/packages/brain-persistence/src/brain_persistence/repositories.py` | `create_corrected_assertion` copies only legacy fields; commit repository has no assertion eligibility guard | Preserve extension restrictions on corrections; resolve evidence/review lineage for guard |
| `engine/packages/brain-review/src/brain_review/decisions.py` | Existing immutable decisions, duplicate/stale/blocked handling | Keep lifecycle/authority; use repository correction support, reject unsupported semantic edits |
| `engine/packages/brain-temporal/src/brain_temporal/commit.py` | `CanonicalCommitService.commit` locks slot then writes commit/versions/outbox | Add mandatory repository guard before `register_commit` or any fact end; existing algorithm unchanged |
| `engine/apps/api/src/brain_api/routes/facts.py` | Current COMMIT authorization; 201/400/401/404/409/503 errors | Map ineligible attributable sources to 422 ProblemDetails; denial stays non-disclosing |
| `engine/packages/brain-content/src/brain_content/{records,contracts,service}.py` | Verified v2 block origins; honest legacy fallback | Reuse via authorized port; no changed writer flag or fabricated STATED origin |
| `engine/migrations/versions/0010_f0005_job_event_reason_expand.py` | Current latest migration at planning | Add `0011_f0006_assertion_semantics.py`, down_revision `0010`; recheck head at feature G0 |

No previous F0006 assembly plan exists. The raw origin-vocabulary difference and case/spacing example are reconciled explicitly in ADR-0075. No approved Phase A business requirement is silently changed.

## Build Order and Exact File Handoffs

Paths below are relative to the bound product root. New runtime paths are proposed and must not be added as as-built KG bindings during plan.

| Step | New files | Modified files | Stories / checkpoint |
|---|---|---|---|
| 0: capture baseline | `engine/tests/fixtures/assertions/legacy-before.json` | None | S0005; record real legacy identities, schema hashes and defaults before migration |
| 1: strict contracts/domain | `engine/packages/brain-contracts/src/brain_contracts/{assertions,dispatch}.py`; `engine/packages/brain-contracts/src/brain_contracts/schemas/{assertion-record-v2,interpretation-result-v2,assertion-admission-result-v1}.schema.json`; `engine/packages/brain-domain/src/brain_domain/assertions.py` | `engine/packages/brain-contracts/pyproject.toml` package data; package exports only | S0001/S0002; all planning contract fixtures validate; exact packaged-schema equality |
| 2: additive persistence | `engine/packages/brain-persistence/src/brain_persistence/assertion_models.py`; `engine/migrations/versions/0011_f0006_assertion_semantics.py` | `models.py`; model registration in migration metadata | S0001/S0002/S0005; real PG migration, composite ownership, version/extension constraints |
| 3: grounding/eligibility | `engine/packages/brain-assertions/pyproject.toml`; `src/brain_assertions/{__init__,ports,normalization,admission,eligibility}.py`; `src/brain_assertions/py.typed` | Engine workspace dependency configuration | S0003/S0004; pure reason-code and original-selector cases |
| 4: authorized write/read | `engine/packages/brain-assertions/src/brain_assertions/service.py`; `engine/packages/brain-persistence/src/brain_persistence/assertions.py` | Engine composition and dependency declarations as needed; no automatic worker registration | S0001–S0004; authorized internal seam, fresh-session reload, atomic failure/retry |
| 5: current consumers | No new transport surface | `document_delivery.py`; `repositories.py`; `brain_temporal/commit.py`; `brain_api/routes/facts.py`; `brain_api/errors.py`; `engine/packages/brain-security/src/brain_security/execution.py`; affected package dependency declarations | S0004/S0005; old paths reject v2 loss/guard bypass and retain v1 behaviour |
| 6: proof/rollout | `engine/packages/brain-assertions/tests/test_{normalization,admission,eligibility}.py`; `engine/tests/integration/test_assertion_{migration,admission,consumers}.py`; native fixtures under `engine/tests/fixtures/assertions/` | Existing review, temporal, importer and HTTP regression tests; engine lockfile; feature GETTING-STARTED/STATUS during implementation | All 35 ACs with real PostgreSQL and current service entry points; ≥80% changed-code coverage |

Backend owns domain/application contracts, admission, persistence, authorization and mutations. AI Engineer reviews shared DTO/producer compatibility and adjusts import shims only if needed; it does not add a model call, prompt, producer, direct SQL write, MCP, A2A or orchestration asset. Frontend is N/A. QE independently supplies expectations and runtime evidence. Security reviews source access, restriction inheritance and non-disclosure. DevOps proves migration, packaging and rollback on the existing stack. Architect signs off semantic and legacy compatibility constraints. No delegate or new agent runtime is introduced.

## Wire Contracts and Dispatch

Authored design schemas are `planning-mds/schemas/assertion-record-v2.schema.json`, `interpretation-result-v2.schema.json`, and `assertion-admission-result-v1.schema.json`. See `contract-examples.json` for 16 independently authored positive/negative schema cases. The legacy `interpretation-result.schema.json` and `brain_contracts.result` remain byte/behaviour compatible.

1. Strictly decode JSON: reject duplicate keys, non-finite numbers, invalid Unicode/JSON and unknown properties. Use packaged local schemas with a resolver that cannot fetch remote `$ref`s.
2. No explicit schema version means v1; exact integer 2 means v2; any other explicit value (including null, boolean or string) is `ASSERTION_CONTRACT_UNSUPPORTED`. Never swallow a validation failure and try a different reader.
3. A v2 result lists document-local `entities`, assertion candidates and an empty separate `relationships` array. Typed relationships use the assertion's ENTITY object. Entities are reference declarations, not canonical entity writes. Store only references used by accepted claims.
4. New typed claims require predicate/release; new open claims require a source phrase, mandatory quote, null predicate/release and EXPLICIT basis. Preserve complete source-word qualifiers, including optional nonempty `mood`.
5. Raw candidates contain untrusted `model_selector` hints. Accepted outputs are a separate protected envelope with server evidence, origin qualification, blocked operations, review reasons, server actor/time and per-item outcomes. Candidate input cannot grant eligibility or set server metadata.
6. The default F0005 importer accepts only v1. New v2 persistence is exercised by the authorized engine service and fixtures. F0016 must explicitly adopt the v2 seam, durable outcomes and run lifecycle before a production producer uses it. No complete run is inferred from successfully validating a candidate array.

### Application carriers and service signatures (Python 3.13)

These are design signatures; implement strict Pydantic wire adapters against the schemas and frozen, I/O-free domain carriers. `Json` denotes JSON primitives/arrays/objects only, with finite numbers; never arbitrary Python objects.

```python
from dataclasses import dataclass
from datetime import datetime
from typing import Literal, Mapping, Protocol, Sequence, Union
from uuid import UUID

Kind = Literal["OPEN_STATEMENT", "TYPED_ASSERTION"]
Mode = Literal["ASSERTED", "OBSERVED", "DERIVED"]
Origin = Literal["DOCUMENT_INTERPRETATION", "SYSTEM_OBSERVATION", "HUMAN_REVIEW",
                 "CONVERSATION_DISCOVERY", "RULE_DERIVATION", "AGENT_ANALYSIS"]
Basis = Literal["EXPLICIT", "INFERRED", "AMBIGUOUS"]
Json = Union[None, bool, int, float, str, list["Json"], dict[str, "Json"]]

@dataclass(frozen=True)
class EvidenceClaim:
    artifact_id: UUID
    block_id: str
    quote: str
    model_selector: Mapping[str, Json] | None = None

@dataclass(frozen=True)
class EntityReference:
    id: UUID
    entity_type: str
    label: str
    introducing_evidence: tuple[EvidenceClaim, ...]

@dataclass(frozen=True)
class EntityObject:
    kind: Literal["ENTITY"]
    ref: UUID
    name: str

@dataclass(frozen=True)
class LiteralObject:
    kind: Literal["LITERAL"]
    value: Json

@dataclass(frozen=True)
class AssertionCandidate:
    id: UUID
    assertion_kind: Kind
    subject_ref: UUID
    object: EntityObject | LiteralObject
    predicate_id: str | None
    ontology_release: str | None
    source_relation: str | None
    qualifiers: Mapping[str, Json]
    time_mention_refs: tuple[UUID, ...]
    valid_time_claim: Mapping[str, Json] | None
    mode: Mode
    origin: Origin
    interpretation_basis: Basis
    model_confidence: float | None
    evidence: tuple[EvidenceClaim, ...]

@dataclass(frozen=True)
class ProducerContext:
    tenant_id: UUID
    knowledge_base_id: UUID
    actor_id: UUID
    artifact_id: UUID
    document_version_id: UUID
    run_id: UUID
    origin: Origin
    model_id: str
    prompt_hash: str
    trace_id: str

@dataclass(frozen=True)
class VerifiedBlock:
    artifact_id: UUID
    block_id: str
    text: str
    native_selector: Mapping[str, Json]
    text_origin: Literal["STATED", "OCR", "TRANSCRIBED", "DESCRIBED"] | None
    origin_qualification: Literal["qualified", "legacy_unqualified"]
    producer: Mapping[str, Json] | None
    producer_confidence: float | None

@dataclass(frozen=True)
class TimeReference:
    id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    artifact_id: UUID
    block_id: str
    words: str

class AdmissionSources(Protocol):
    async def block(self, context: ProducerContext, block_id: str) -> VerifiedBlock: ...
    async def time_reference(self, context: ProducerContext, ref: UUID) -> TimeReference: ...

class AssertionAdmissionService:
    async def check_items(self, context: ProducerContext,
                          entities: Sequence[EntityReference],
                          items: Sequence[bytes], *, truncated: bool,
                          uninterpreted_blocks: Sequence[str]) -> "AdmissionBatch": ...

class AssertionWriteService:
    async def admit(self, principal: "Principal", context: ProducerContext,
                    entities: Sequence[EntityReference], items: Sequence[bytes], *,
                    delivery_key: str, truncated: bool = False,
                    uninterpreted_blocks: Sequence[str] = ()) -> "AdmissionBatch": ...
    async def read(self, principal: "Principal", assertion_id: UUID) -> "AssertionRead": ...

@dataclass(frozen=True)
class SourceAccessProof:
    tenant_id: UUID
    knowledge_base_id: UUID
    unit_of_work_id: UUID
    source_artifact_ids: tuple[UUID, ...]
    authorization_decision_ids: tuple[UUID, ...]

class AssertionEligibilityGuard(Protocol):
    async def require_commit_sources(self, *, evidence_refs: Sequence[UUID],
                                     review_decision_id: UUID | None,
                                     authorized_scope: tuple[UUID, UUID],
                                     closes_existing: bool,
                                     source_access: SourceAccessProof | None) -> None: ...
```

`AdmissionBatch` is the typed adapter of the complete admission-result schema, with accepted record/server-evidence/review/blocked-operation/actor/time fields and every outcome field. `AssertionRead` discriminates legacy raw projection from version-2 record plus verified metadata; no default mode/quote/release is invented. A production time resolver initially raises UNKNOWN_REFERENCE for nonempty references until F0016 supplies one; fixture resolvers explicitly declare their scoped references. This does not implement time-mention production or resolution.

## Data Model and Database Integrity

New tables retain structural tenant/KB ownership and server actor/time. Every new table is append-only. `assertion_semantics` is a semantic extension, not a parallel assertion identity or a new truth plane.

| Table / carrier | Fields and constraints |
|---|---|
| Existing `assertion` | Existing 13 scalar columns and both ORM relationships preserved; add `semantic_contract_version SMALLINT NOT NULL DEFAULT 1 CHECK (... IN (1,2))`. New v2 typed core uses the actual predicate as slot_type; open core uses reserved `__OPEN_STATEMENT_V2__` only as an internal compatibility carrier. It is never returned as an ontology predicate or passed to old DTOs. Main value is the source literal object, or an explicit `{literal: scalar}` / `{object_ref: UUID}` carrier; the extension's complete record is authoritative for v2. The v2 carrier's `subject_type` is the admitted subject reference's `entity_type`; it is never inferred from the predicate or value. A correction child copies its original's `subject_type`. The carrier's `interpretation_basis` must equal `record.interpretation_basis`. |
| `assertion_document_reference` | `id UUID PK`, `document_version_id UUID`, `tenant_id UUID`, `knowledge_base_id UUID`, `entity_type TEXT`, `label TEXT`, `created_by UUID -> principal`, `created_at TIMESTAMPTZ`; all NOT NULL. Unique `(id, document_version_id, tenant_id, knowledge_base_id)`; FK document-version owner. A reference is local to one immutable document version; F0017 attaches canonical identity later. |
| `assertion_name_claim` | `document_version_id UUID`, `tenant_id UUID`, `knowledge_base_id UUID`, `normalized_name TEXT`, `entity_ref UUID`, `created_by UUID`, `created_at TIMESTAMPTZ`; all NOT NULL. PK `(document_version_id, tenant_id, knowledge_base_id, normalized_name)`; composite FK `(entity_ref,document_version_id,tenant_id,knowledge_base_id)` to reference. Name key uses the documented NFC/case/whitespace normalization only; it is an admission uniqueness key, never a canonical name fact. |
| `assertion_semantics` | `assertion_id UUID PK`, `document_version_id UUID`, tenant/KB, `subject_ref UUID`, nullable `object_ref UUID`, `assertion_kind TEXT`, `fact_mode TEXT`, `assertion_origin TEXT`, nullable `predicate_id TEXT`, nullable `ontology_release TEXT`, `record JSONB`, `entity_snapshots JSONB`, `verified_evidence JSONB`, `time_reference_snapshot JSONB`, `raw_item_sha256 CHAR(64)`, `admission_sha256 CHAR(64)`, `created_by UUID`, `created_at TIMESTAMPTZ`. All other fields NOT NULL. Composite owner FK to assertion; scoped document/reference FKs for subject and object; principal FK. |

The full `record` validates against assertion-record-v2. Snapshot only references actually used by accepted claims. Time snapshots retain the resolved scoped reference ID and words without producing an interval. Evidence IDs, selector, raw quote, normalization version, block origin/qualification, producer and confidence are server-owned and inserted with ordinary AssertionEvidence rows. Treat verified origin as a retained snapshot of the immutable source, not a caller-set assertion field.

### Migration SQL and guards

The migration creates the three tables with the exact columns above. Use existing owner-key constraints from migrations 0005/0006. SQL backstops, in addition to service schema validation:

```sql
ALTER TABLE assertion ADD COLUMN semantic_contract_version smallint NOT NULL DEFAULT 1
  CHECK (semantic_contract_version IN (1,2));

-- On assertion_semantics (constraints in CREATE TABLE):
CHECK (assertion_kind IN ('OPEN_STATEMENT','TYPED_ASSERTION')),
CHECK (fact_mode IN ('ASSERTED','OBSERVED','DERIVED')),
CHECK (assertion_origin IN ('DOCUMENT_INTERPRETATION','SYSTEM_OBSERVATION','HUMAN_REVIEW',
  'CONVERSATION_DISCOVERY','RULE_DERIVATION','AGENT_ANALYSIS')),
CHECK ((assertion_kind = 'OPEN_STATEMENT' AND predicate_id IS NULL
        AND ontology_release IS NULL AND record->>'interpretation_basis' = 'EXPLICIT')
    OR (assertion_kind = 'TYPED_ASSERTION' AND length(predicate_id) > 0
        AND length(ontology_release) > 0)),
CHECK (jsonb_typeof(record) = 'object' AND jsonb_typeof(verified_evidence) = 'array'
       AND jsonb_array_length(verified_evidence) > 0),
CHECK (record ?& ARRAY['id','assertion_kind','mode','origin','qualifiers','evidence']),
CHECK (record->>'id' = assertion_id::text AND record->>'assertion_kind' = assertion_kind
       AND record->>'mode' = fact_mode AND record->>'origin' = assertion_origin),
CHECK (raw_item_sha256 ~ '^[0-9a-f]{64}$' AND admission_sha256 ~ '^[0-9a-f]{64}$')

CREATE INDEX ix_assertion_semantics_subject
  ON assertion_semantics (tenant_id, knowledge_base_id, subject_ref);
CREATE INDEX ix_assertion_semantics_document
  ON assertion_semantics (tenant_id, knowledge_base_id, document_version_id);
```

Use `IS NOT NULL` with conditional text checks and `coalesce(..., false)` where JSON presence is required; SQL NULL must not bypass a CHECK. Mirror record predicate/release/subject/object to denormalized columns with explicit `IS NOT DISTINCT FROM` comparisons. Validate confidence is null or finite in [0,1] in both DTO and database main-row check. Source ownership is never inferred from an ID's format.

Create `brain_assertion_v2_integrity()` as a constraint-trigger function and attach DEFERRABLE INITIALLY DEFERRED triggers to inserts on assertion and assertion_semantics. At transaction end: v2 assertion must have exactly one extension with matching owner, origin/basis/core carrier, evidence rows and scoped source; a version-1 row must have none and cannot use the reserved sentinel. A direct core-only v2 insert or orphan extension fails. Trigger checks must use actual row values/record data, not a supplied boolean flag.

Reuse `brain_append_only()` for the three new tables. Add original-field immutability triggers on assertion and assertion_evidence. Preserve the existing staleness mechanism: an assertion UPDATE may only increment `version` by exactly one with every other field unchanged; evidence UPDATE/DELETE and assertion DELETE fail. A migration adds discriminator metadata, not reconstructed provenance. All FK ownership and append-only failures need real PostgreSQL cases, including service-role SQL attempts.

Lock the source `document_version` row before checking/inserting name claims, and process documents in UUID order. The unique scoped name key is the concurrency backstop. A same-entity exact replay is idempotent; a different entity gets NAME_CLAIMED_BY_ANOTHER without replacing the first claim. Failed assertions must not reserve names/references: validate purely first, then use a per-item savepoint for the name/claim transaction; map a name conflict to the explicit rejection outcome. Infrastructure/authorization/audit failures roll back the entire admitted write, not just one item.

No FK to a future ontology-release/time-mention table is invented. Predicate/release are opaque, nonempty, pinned identifiers from trusted interpretation context; representation is not ontology validation. Time reference resolution must verify owner and persisted existence through the supplied port before admitting it; future F0016 owns that store and its eventual FK migration.

## Admission Logic and Outcomes

1. Through the existing authorization facade, hydrate and lock the run/artifact/document ownership. The server constructs ProducerContext and validates requested IDs and allowed producer origin; actor/origin are not trusted from model data. Deny before any source text read. New writes require current artifact INTERPRET authority; read hooks require source READ authority. No cached authorization decision is reused.
2. Decode each raw item independently, validating its version-2 schema. Hash exact raw bytes; redact the general error to a stable code. Keep protected excerpts only in the return/outcome persistence boundary. A malformed item does not discard other complete, valid items.
3. Check subject is a listed, same-document entity reference. Validate each referenced entity's name in its introducing quote. Fetch sources only from the authorized artifact; validate quote/block identity. Pending/unknown source integrity is not a fabricated selector.
4. For declared object references, check ID/name against the listed reference. For an undeclared object, retain its supplied source name as a literal and emit OBJECT_UNDECLARED. If that name is outside the quote, reject NAME_NOT_IN_QUOTE; never invent a name from the UUID.
5. Resolve time-reference IDs through the scoped port and check each reference's words occur in an evidence quote on the assertion it dates. No time computation. Unknown/dangling refs produce UNKNOWN_REFERENCE; absent words produce TIME_NOT_IN_QUOTE.
6. Ground every evidence quote. Normalization order is NFC with source-range mapping, alphabetic line-break hyphen join, Unicode casefold, whitespace collapse, then adjacent-currency-symbol space removal. Retain original quote and text. Numeric values/commas/decimal points are never rewritten or compared for semantic truth.
7. Unique normalized match maps its union of original ranges back to native location: PDF page/regions, DOCX paragraph/run part, XLSX sheet/cell, CSV row/column, preserving verified multi-region selectors. Only claim span precision where original mapping is unique and contiguous. Multiple matches fall back to verified cell/block/page/document precision, or unresolved if no honest locator exists. Model offsets are discarded even if plausible. Repeated equal values in different cells cannot choose a cell without independently verified source identity.
8. Apply all applicable checks and retain every distinct failure; one rejected item produces no assertion/evidence/name effects. Reason precedence affects display only, not recording. Use the schema's item_path to distinguish entity declarations from assertion positions.
9. Add TRUNCATED_OUTPUT once per affected block/terminal output; keep complete independently checked items. Add BLOCK_UNINTERPRETED for each block with no parsable items. Set `requires_partial` exactly when either issue is present. Ordinary item rejection also remains visible, with counts/outcomes handed off; F0016 decides its broader run policy. Never report missingness NOT_FOUND from these outcomes.
10. Derive eligibility/review hooks from kind, supplied mood and verified support, not confidence. Persist admitted records with trusted actor/time and return every protected outcome. F0016 must persist outcomes before claiming run completion; the F0006 service does not set a run COMPLETE or create a durable drop table.

| Check | Outcome |
|---|---|
| Quote absent from claimed block after documented normalization | REJECTED / QUOTE_NOT_IN_SOURCE |
| Introducing entity/object name absent from its quote | REJECTED / NAME_NOT_IN_QUOTE |
| Another entity already owns normalized name in the document | REJECTED / NAME_CLAIMED_BY_ANOTHER |
| Time words absent from assertion evidence | REJECTED / TIME_NOT_IN_QUOTE |
| Missing listed subject or unresolved time reference | REJECTED / UNKNOWN_REFERENCE |
| Undeclared object with a source name | Retained literal + SIGNAL / OBJECT_UNDECLARED |
| Malformed item/inconsistent candidate shape | REJECTED / MALFORMED_ITEM |
| Truncated/incomplete model output | RUN_ISSUE / TRUNCATED_OUTPUT; complete items retained |
| No parsable output for a block | RUN_ISSUE / BLOCK_UNINTERPRETED |

The service is structural and makes zero model/conversion/OCR calls. A true quote with a false extracted amount can pass; the value remains for semantic review, as required by S0003 AC7.

## Atomic Writer, Replay and Read Projection

Within `AuthorizationExecution.mutate`, validate expected run/artifact/owner and take the source-document/name locks. Use a stable delivery key scoped to run/producer. Assertion ID is the existing primary key; admission hash covers canonical JSON of validated record, selected references, verified source hashes/selectors, producer context and normalization version. Exclude server timestamp from the replay hash. Existing identical ID/hash/owner returns the original row and actor/time; changed payload, ownership or source hash is `ASSERTION_ID_CONFLICT` (409 internally), never an overwrite.

For each accepted item insert local references/name claims, legacy carrier (`semantic_contract_version=2`), extension, deterministic AssertionEvidence IDs and required review hook/item. Use UUID5(assertion ID, evidence ordinal) and UUID5(assertion ID, review reason) as stable identities, following the existing importer pattern; this is not a run-ID generation mechanism. Different contexts cannot replay someone else's assertion: scope/producer/run/delivery identity participate in the hash and are checked before lookup results are disclosed.

Review hook: use existing PROVENANCE_CORRECTION for described/unqualified/unresolved support and EXTRACTION_CORRECTION for existing confidence handling; retain specific reason codes in the semantic extension and internal projection. A new HTTP/display schema is not required now. Mood/open restrictions remain even if a review hook is acknowledged. Crash before commit leaves no claim/evidence/review set; after commit replay returns one set. No new canonical write is triggered. A failure writing authorization/review audit aborts the mutation under the existing facade.

`read()` first resolves the owning source and uses the existing READ facade before returning the internal projection. Legacy raw fields remain raw and version=1, with explicitly labelled compatibility origin only. Never synthesize a mode, quote or ontology release for old rows. Old DTO projection of a version-2 open record is unsupported; it is rejected rather than exposing the internal sentinel as meaning.

## Eligibility and Existing Consumers

| Stored source | Resolution / canonical creation | Auto acceptance | Close / supersede | Required handling |
|---|---|---|---|---|
| OPEN_STATEMENT | Block | Block | Block | Retain storage; F0066 alignment later |
| Any mood-bearing claim | Block | Block | Block | Retain condition/candidate; no normative engine now |
| Typed, only qualified DESCRIBED support | Review required for any initial accepted use | Block | Block | DESCRIBED_EVIDENCE hook; a reviewer cannot turn the described words into STATED |
| Typed, verified STATED/OCR/TRANSCRIBED support | Necessary structural preconditions met; existing policy still decides | Existing policy only; no new auto-acceptance | Existing policy/commit checks still apply | Retain actual precision and producer confidence |
| Unknown/unqualified/unresolved support | Existing provenance review applies | Block | Existing review/commit restrictions; no new authority | Never qualify legacy origin silently |

Mixed evidence: only DESCRIBED restrictions apply when *all* evidence is qualified DESCRIBED. A non-described item must be verified, attributable supporting evidence before it clears described-only status; an unresolved/unqualified item cannot clear it. Mood and kind restrictions always dominate. INFERRED/AMBIGUOUS are retained and are not false by definition or automatically accepted. Operative provisions have a policy-as-subject proposition without world-condition mood; the embedded premise stays a separate mood-bearing claim. No word-list classifier infers this distinction.

`CanonicalCommitService.commit` calls mandatory `repository.require_commit_sources(...)` after slot/owner lock and determining whether current versions overlap, before `register_commit`, closing any range or writing outbox. Repository resolution walks `evidence_refs -> assertion_evidence -> assertion_semantics`, and `review_decision_id -> review_item/assertion + corrected_assertion_id -> original_assertion_id` ancestry. Check all associated owners and current read access to sources through the trusted authorization facade within the same unit of work. No supplied eligibility booleans. Detect cycles/corrupt links as refusal, not legacy fallback. Pure/domain test repositories implement this required method; there is no permissive default.

For a v2 reference or lineage, all referenced sources must resolve; unknown/mixed/unowned references cannot switch the operation into the legacy branch. Supplied evidence which disagrees with review lineage is rejected. For all-legacy pilot proposals keep existing behaviour, including unregistered UUIDs: F0006 does not claim to solve F0018's complete provenance orchestration. A caller copying an arbitrary number without attributable assertion lineage cannot be identified by structural checks; this is an explicit legacy boundary, not a new source eligibility grant.

Review correction: `create_corrected_assertion` preserves v2 subject/object identity, kind, mode, property/release, source phrase, qualifiers/mood, **interpretation basis** and the original evidence restriction snapshots. It stamps HUMAN_REVIEW and the actual reviewer/clock, and updates only the value through the existing entry point. If a new evidence locator is supplied, it must be re-admitted against the same authorized source. Otherwise the original verified evidence is retained. The old endpoint cannot clear mood, change kind or basis, or silently reclassify described evidence. Unsupported semantic changes return the existing 422; full v2 semantic editing, including a reviewer-supplied basis, is a later contract amendment. Original claims/decisions are never rewritten.

**Correction interpretation basis (resolves plan-review AR-1; operator decision 2026-11-01).**

- *v2 correction:* a correction of a v2 assertion copies the original's `interpretation_basis` unchanged into both the carrier column and `record`. An INFERRED or AMBIGUOUS claim therefore stays INFERRED or AMBIGUOUS after review (S0001 AC4). The review request gains no basis member.
- *v1 correction:* a correction of a v1 assertion keeps the existing hard-coded `EXPLICIT` behaviour of `repositories.py`. This is an explicit legacy compatibility boundary, not a new rule. It preserves the existing review regression contract (S0005 AC3). A v1 child stays `semantic_contract_version=1`, cannot satisfy any v2 eligibility precondition, and is never cited as evidence that a claim was explicitly supported. Tests must assert both branches.

**v2 correction child persistence (resolves plan-review AR-2).** A correction of a v2 assertion writes a v2 child in the same unit of work as the existing review decision:

1. *Carrier:* a new `assertion` row with a fresh ID, `semantic_contract_version=2`, `run_id` NULL, `origin='HUMAN_REVIEW'` and `original_assertion_id` set. `subject_type`, `slot_type`, tenant/KB and inherited basis are copied from the original. `value` holds the corrected literal carrier, and `model_confidence` is NULL.
2. *Extension:* one `assertion_semantics` row.
   - Copied from the original's extension: `document_version_id`, tenant/KB, `subject_ref`, `object_ref`, kind, mode, predicate/release, `entity_snapshots` and `time_reference_snapshot`.
   - Set for the child: `assertion_origin='HUMAN_REVIEW'`. `record` is the original record with `id` set to the child ID, `origin` set to HUMAN_REVIEW, the inherited basis, and the object replaced by the corrected value. It must validate against assertion-record-v2.
   - A correction that would change an ENTITY object reference, kind or open-statement wording is rejected with 422.
   - `verified_evidence` is the original snapshot, or the snapshot from re-admitting the new locator.
3. *Evidence rows:* new `assertion_evidence` rows owned by the child, with IDs `UUID5(child_id, ordinal)`. They copy artifact, block, page, bbox, character range and precision from the original rows, or take them from the re-admitted locator. Original evidence rows are never updated or re-pointed. This gives every v2 assertion its own evidence set, as the deferred integrity trigger requires, while lineage reaches the original through `original_assertion_id`.
4. *Hashes:* both use the same canonical JSON serialization as admission.
   - `raw_item_sha256` is the SHA-256 of the strictly validated correction input `{review_item_id, assertion_version, corrected_value, evidence_seen}`. This is the human-review analogue of the raw model item.
   - `admission_sha256` is the SHA-256 of `{child record, original_assertion_id, verified evidence snapshots including source hashes/selectors, normalization version, reviewer principal ID, review_item_id}`, excluding server timestamps.
   - Correction replay is still governed by the existing duplicate/stale decision checks, not by a new hash-replay path.
5. *Integrity trigger:* `brain_assertion_v2_integrity()` accepts a v2 row with NULL `run_id` only when `origin='HUMAN_REVIEW'` and `original_assertion_id` references a v2 assertion with the same tenant/KB/document version, kind, predicate/release, subject reference, mood qualifiers and basis. A v1 original may only have a v1 child. Any other combination fails at commit.

## Current HTTP Contract and Mutation Traceability

No new HTTP route or mandatory request member. API changes are documented in `api/brain-api.yaml`: commit adds an eligibility error; review describes retained v2 restrictions. ProblemDetails remains `application/problem+json` with stable `code` and `traceId`.

| Entry / action | Service and carrier | Authorization / concurrency | Failure / audit / test |
|---|---|---|---|
| Internal authorized candidate submit (S0001–S0004) | AssertionWriteService.admit → assertion + extension/references/evidence/hook | content_artifact:interpret via current facade; doc lock; ID/hash replay | Source denial non-disclosing; malformed item outcomes; transaction rollback on infra failure; authorization/import/review trace; fresh PG reload |
| Existing v1 result delivery (S0005) | DocumentResultImporter.run_one → unchanged legacy rows | Existing job principal/lease/outbox transaction | Unsupported v2/unknown version before effects; replay unchanged; importer tests |
| Review Panel submit correction (S0001/S0005) → POST /reviews/batches/{reviewBatchId}/decisions | ReviewDecisionService.submit → repository additive correction | review_task:annotate; existing assertion version, stale/duplicate checks | 200 existing receipt; 404 inaccessible; 422 invalid/unsupported semantic change; existing review audit; original/child reload |
| Existing pilot commit (S0004/S0005) → POST /facts/{factSlotId}/commits | CanonicalCommitService.commit → source guard → current commit algorithm | fact_slot:commit plus current source READ; existing slot lock/current-version and audit UoW | 201 success; 400 range; 401 credentials; 404 denied/unowned; 409 stale/concurrent; 422 ASSERTION_INELIGIBLE; 503 dependency/audit; zero rejected canonical effects |
| Internal scoped read / existing GET /reviews/{reviewItemId} | Internal AssertionRead or unchanged review DTO | Source READ / review_task:read; no mutation | Existing errors; v2 internal restrictions retained for F0022 hook; no new UI required |

### Authorization facade integration

The current `AuthorizationExecution.mutate` takes one action for all keys and commits its unit of work. Do not nest `read()` inside it. Add an optional trusted callback to this existing method:

```python
additional_reads: Callable[[], Awaitable[Sequence[ResourceKey]]] | None = None
```

After primary action authorization/recheck, call it to discover source IDs and owners through the trusted repository (no source text), then call the existing shared `decide` orchestration with Action.READ for the sorted unique content-artifact keys. Merge the primary/source Evaluated lists, refuse through the existing `_deny` path if any decision fails, stage all audits, and recheck all before invoking `operation`. All locks, audits and effects use the same session/store; do not commit inside the callback. Exceptions use the existing rollback/fresh failure-audit path for the combined decision list. Existing no-callback callers behave identically. Add expiry, revocation, source denial, audit failure and callback-failure unit tests in `engine/packages/brain-security/tests/test_execution.py` (create a focused file if it does not exist at feature G0).

The facts route supplies the callback only for attributable v2 evidence/review lineage and identifies the primary fact-slot COMMIT decision by resource/action instead of tuple-unpacking a single decision. Pass a trusted in-memory `SourceAccessProof` (scope, current UoW identity, source resource IDs and their audit decision IDs) into the repository's eligibility guard; it is not a request DTO. Add optional internal `source_access: SourceAccessProof | None = None` to `CanonicalCommitService.commit`; the repository verifies it, and no public request field is added. Direct application callers must use the same facade for v2 sources or are refused. The guard verifies this proof against the current unit of work and discovered sources; a supplied boolean or stale/client-created context is never accepted. Legacy-only proposals need no new READ authority. This is a consumer enforcement adaptation, with no change to policy grants or scope evaluation.

A denied source stays 404, even if its semantic restriction would otherwise be 422. Return no protected quote/reason to an unauthorized caller. Already authorized 422 carries stable code only, not a source excerpt. Retain existing fact/review error contract behaviour outside the new guard.

## Validation Matrix and Completion Gates

| Story criteria | Required implementation verification |
|---|---|
| S0001 AC1–AC7 | Fresh-session PG records for all dimensions and confidence boundaries; two competing amounts; append-only source/evidence; illegal enum, ownership and no-canonical-write cases; v2 corrections of INFERRED/AMBIGUOUS claims keep their basis; v1 correction legacy EXPLICIT boundary asserted separately |
| S0002 AC1–AC7 | Typed/open record invariants and fixture storage without a model; v1/new schemas; old reader refusal; local/dangling/cross-scope refs; no fabricated old fields |
| S0003 AC1–AC8 | Every reason/signal, raw-item identity, all simultaneous failures, partial/truncated retention; four native formats, repeated values, NFC/case/currency whitespace/hyphen mapping; genuine quote/misread value; no unauthorized content read |
| S0004 AC1–AC6 | Subjectivity, offered limit, warranty, conditional and operative provision; described-only versus qualified OCR/transcribed/mixed support; unknown origin; independent restrictions and review projection |
| S0005 AC1–AC7 | v2 correction child carrier/extension/evidence rows/hashes satisfy the deferred trigger, with `subject_type` copied; trigger rejects mismatched or v1→v2 children; existing importer/review/commit entry points, mixed/correction ancestry guard bypass, source revocation, atomic review insertion failure and retry, migration and guard-preserving rollback, independently authored examples and coverage |

Planning validation: schema-check all three authored contracts and 16 expected valid/invalid examples using offline local references; semantic teaching validator; story/tracker validators; G4 compile/drift and G5 full exit sequence. No current runtime behaviour is inferred from these passes.

Implementation commands are proposed until executed in the feature run:

```bash
# cwd: engine/migrations (alembic script_location is relative to this directory)
uv run --project .. alembic upgrade head
# remaining commands: cwd product root
uv run --project engine pytest engine/packages/brain-assertions/tests engine/tests/integration/test_assertion_migration.py engine/tests/integration/test_assertion_admission.py engine/tests/integration/test_assertion_consumers.py
uv run --project engine pytest engine/packages/brain-persistence/tests engine/packages/brain-review/tests engine/packages/brain-temporal/tests engine/apps/api/tests/test_reviews.py engine/apps/api/tests/test_facts.py
uv run --project neuron pytest neuron/tests/integration/test_document_process_recovery.py
```

Existing recovery suite `neuron/tests/integration/test_document_process_recovery.py` and migration configuration `engine/migrations/alembic.ini` were verified on disk. New assertion test paths are proposed implementation outputs from the file table. The commands above have not been run at plan; the feature action supplies its existing database configuration, and QE records exact executed commands, fixture fingerprints and PostgreSQL evidence. Schema-only tests cannot substitute for the runtime matrix.

Implementation NFRs: at least 80% changed-code coverage; zero unauthorized returned/source-read content in negative tests; zero conversion/OCR/model calls in structural admission; atomic one-logical-effect replay; no changed defaults/grants. Capture latency/sample sizes as observations without inventing a product SLO.

## Rollout, Rollback and Caching

1. Capture v1 schema hashes, representative assertion/correction/evidence IDs, current defaults and current consumer regression results. Confirm migration head before naming 0011; if another head exists, reconcile migration lineage at feature G0.
2. Apply additive migration with v1 discriminator default. Deploy guard-capable readers/correction/commit paths before enabling any internal v2 writes. Validate package schemas are shipped and cannot fetch network refs. Keep automatic importer v1-only.
3. Run the full fixture/PG/current-consumer matrix on the existing local Compose topology. No model provider is required for admission proof; reuse immutable native fixtures. Do not enable content v2 or Graph selection.
4. Once v2 rows exist, never deploy a binary that can read them as v1. To roll back writing, stop v2 callers, retain extension tables and guard-capable compatibility readers. Migration downgrade must refuse if any v2 assertion/reference/name/semantics row exists. Only an empty new surface permits dropping new tables/column after verification/backup; do not delete evidence to make downgrade pass.
5. No result, eligibility or authorization cache. Cache only immutable packaged schemas and versioned normalization code; the existing content store verifies immutable source bytes. Current grants and source access are rehydrated per operation.

## Dependencies, Future Handoffs and Approval

Delivered F0001–F0005 approval references are in run artifact-trace.md; current consumer adoption proof is pending implementation. F0007/F0009/F0010/F0017 consume claim identity/lineage; F0015/F0016 consume the versioned candidate/admission seam; F0016 owns durable drops, time references and full outcomes; F0018 owns complete source/commit orchestration; F0022 owns new display; F0026 owns production/frozen evaluation; F0065 consumes accepted canonical facts only; F0066 owns live open extraction/alignment; F0052/F0053 own routing execution. No reverse dependency is introduced.

G4 must compile the authored feature/node shards and pass drift. G5 must pass every exit command in order before operator Phase B approval. After explicit approval, update approval metadata, attest, and rerun G5 including compile, coverage refresh and plain KG validation. No further planning edit follows that final refresh. All stories remain Not Started until the later feature action; plan approval is not feature completion.
