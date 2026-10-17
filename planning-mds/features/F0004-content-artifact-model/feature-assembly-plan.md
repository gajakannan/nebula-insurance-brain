# F0004 — Content artifact model — Assembly plan

**Author:** Architect\
**Status:** Phase A approved by operator “proceed with Phase B”; Phase B design approved by explicit `approve-phase-b` on 2026-10-16. Reworked for plan-review `2026-10-16-a186bc18` findings in plan run `2026-10-16-fce2ff91`, for re-review `2026-10-16-b98c71c4` in plan run `2026-10-16-06e0131a`, and for a full-review gap list in plan run `2026-10-17-620b7618`; each re-approved with `approve-phase-a` and `approve-phase-b`. Runtime implementation and ADR proof gates remain outstanding.\
**Plan run:** `2026-10-15-bbd8df01`; reworks `2026-10-16-fce2ff91`, `2026-10-16-06e0131a`, `2026-10-17-620b7618`\
**NEBULA_PRODUCT_ROOT:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`

## Overview and authority

Implement the four approved [PRD](PRD.md) stories as versioned content contracts, a shared verification/publication boundary, normalized content indexes and append-only document-date metadata. Preserve legacy bytes/IDs and existing current-scope authorization. [ADR-0073](../../architecture/decisions/ADR-0073-versioned-content-contracts-and-document-metadata.md) records the design, reconciliation and proof gates; it remains Proposed. Accepted ADR-0040/0058-as-amended/0059 remain governing baselines; broader ADR-0060/0064/0065 obligations are not activated.

This is a Python/FastAPI/SQLAlchemy design under SOLUTION-PATTERNS, not the framework template's illustrative C# stack. All runtime paths below are **implementation targets**, not evidence that changes have shipped. Existing file paths were checked; new files are explicitly labeled. No new service/container, public mutation endpoint, UI, model engine or permission grant is introduced.

## Build order

| Step | Outcome | Stories | Owner |
|---|---|---|---|
| 1 | Per-item provenance spike with an exit decision; then versioned manifest/records and legacy dispatch with executable contract examples | S0001, S0002, S0004 | AI engineer (spike) + Backend; Architect records the exit decision |
| 2 | Shared verifier, source identity and fenced ready publication with indexed content | S0001, S0002 | Backend + AI engineer |
| 3 | Append-only document-date candidates/selections and internal read/write handoff | S0003 | Backend |
| 4 | Authorized consumer integration, migrations, restart/restore and compatibility proofs | S0004 and all cross-story cases | Backend + QA + DevOps; Security review |

## Existing code and reconciliation

| Existing path | Audited behavior | Planned change |
|---|---|---|
| `engine/packages/brain-content/src/brain_content/manifest.py` | Strict Pydantic v1 models; `ArtifactManifest` has 17 fields | Keep explicit v1 model; add v2 and a discriminated reader using planning schemas. Preserve import compatibility until all callers adopt the union. |
| `engine/packages/brain-content/src/brain_content/store.py` | Async API store writes marker last, but neither publication nor file reads verify all declared hashes | Delegate to the same verifier as the worker. Route reads return exact retained manifest bytes/files after full validation. |
| `engine/packages/brain-content/src/brain_content/checkpoints.py` | Sync manifest-last publication, identical retry, hash/scope checks, separate four-file run outputs | Reuse those guarantees; version hash/namespace dispatch, enforce record/native asset closure, and preserve corruption-as-failure. |
| `neuron/packages/brain-ingestion/src/brain_ingestion/bundle_writer.py` | Native JSON and five parse payload files; source retained as `source.<ext>`; duplicate block ID per provenance region; table dimensions only | V2 one block per attributable native item/origin with multiple regions, table/cell relations, explicit geometry and truthful producer metadata. Preserve a v1 reader; no synthetic backfill. |
| `neuron/packages/brain-interpretation/src/brain_interpretation/parsed_content.py` | `ParseResult` has six fields: document, page count, failed pages, OCR page count, status, warnings | Add a versioned projection handoff carrying per-item origin/producer and asset closure. Keep the existing conversion result readable; page OCR counts alone cannot populate block origins. |
| `neuron/packages/brain-ingestion/src/brain_ingestion/document_worker.py` | Conversion callback builds/publishes through queue fencing; reuse loads saved JSON | Inject the v2 builder/verifier and common ready registrar; do not copy scheduler/retry logic. Fail closed on corrupt accepted artifacts or insufficient origin metadata. |
| `neuron/packages/brain-ingestion/src/brain_ingestion/worker_cli.py` | `version_id=uuid5(document_id, recipe)`, `artifact_id=uuid5(version_id,'content')`; scoped source retention | Resolve existing source/artifact first; retain historical IDs. New sources use ADR-0073 identities; changed recipe cannot implicitly reparse a previously accepted source. |
| `engine/apps/worker/src/brain_worker/document_delivery.py` | `register_document_artifact()` persists source/version/artifact before extraction; importer checks identities | Extend this existing registration transaction with contract/manifest hashes, normalized indexes and mutation audit. Importer adopts verified existing metadata without a second publication event. |
| `engine/packages/brain-jobs/src/brain_jobs/queue.py` | `publish_transaction(lease, operation)` holds the generation fence | Reuse this API for marker/ready registration. Scheduling and lease policy remain F0005. |
| `engine/packages/brain-persistence/src/brain_persistence/models.py` | Source/version/artifact from 0001; one-artifact-per-version unique constraint; F0002 scoped keys | Add nullable expansion columns, normalized index/date models; remove only the single-artifact cardinality constraint after reconciliation. Preserve all parent ownership constraints. |
| `engine/apps/api/src/brain_api/routes/content.py` | Two authorized GET routes; files must appear in manifest | Use versioned verified reads with hydrated scope; preserve 404 non-disclosure and audit-before-payload. No date data is appended to an immutable manifest response. |
| `scripts/ops/backup.sh`, `restore.sh`, `verify_citations.py` | Local DB/content backup and citation restore drill | Add verified artifact/run-output inventory and metadata/date/index checks; use an isolated restore target and a quiesced local writer window. |

The published v1 schema now admits observed `source.pdf`; it otherwise retains its legacy fields. No previously stored byte stream or archive requirement is rewritten. F0005's existing checkpoint/registration machinery is reused; this feature does not claim it was missing or that Graph is production-qualified.

## Contract inventory and serialization

| Contract | Purpose |
|---|---|
| [Manifest v1](../../schemas/content-artifact-manifest.schema.json) | Legacy reads, with the documented retained-PDF filename clarification |
| [Manifest v2](../../schemas/content-artifact-manifest-v2.schema.json) | New parse bundles, source/asset inventory, explicit geometry conventions and recipe identity |
| [Manifest read union](../../schemas/content-artifact-manifest-read.schema.json) | Existing manifest GET returns the version actually stored; unknown versions fail |
| [Content records v2](../../schemas/content-records-v2.schema.json) | Exactly one typed block/table/layout JSON object per JSONL line |
| [Document-date records](../../schemas/document-date-record.schema.json) | Append-only candidate/selection handoff, independent of bundle hashes |
| [Interpretation output manifest](../../schemas/interpretation-output-manifest.schema.json) | Existing run v1 plus proposed v2 pipeline/date-basis reference; never parse-owned |
| [OpenAPI](../../api/brain-api.yaml) | Existing two content GETs, version union and integrity/unavailable errors |

JSON uses snake_case, UUID strings and UTC RFC3339 recorded timestamps. Date values are lexical YEAR (`YYYY`), MONTH (`YYYY-MM`) or DAY (`YYYY-MM-DD`), never padded; reject invalid calendars and unsupported precision. Decimal page coordinates are finite numbers. Offsets are half-open Unicode code-point indexes into exact `block.text`; `identity-unicode-v1` does not normalize whitespace or rewrite Unicode. UI UTF-16 conversion remains F0022.

PDF pages are one-based; table rows/columns are zero-based. Canonical geometry is top-left PDF points after declared crop/rotation; `native_to_canonical=[a,b,c,d,e,f]` means `x'=a*x+c*y+e`, `y'=b*x+d*y+f`. Store dimensions/rotation/transform when known; otherwise `geometry_state=unavailable`, null geometry, reason and coarse/unresolved anchors. Never substitute page height zero. Original native geometry remains in retained JSON.

File descriptors contain exactly path, SHA-256 and byte length. V1 hashes concatenate sorted file digests. V2 hashes the sorted descriptor list serialized with sorted keys, ASCII escaping and compact separators. Manifest bytes are excluded from their own inventory; their exact hash is stored in PostgreSQL. V2 source is `source.pdf`; native resource references must resolve to embedded data or declared `assets/<safe-name>.<extension>` files. External URLs, traversal, symlinks, undeclared files and extra path components are rejected. No network fetch is part of validation/reuse.

## Step 1 — Versioned records and provenance (S0001/S0002)

### Step 1a — Per-item provenance spike (gates the v2 writer)

The current conversion handoff carries only page-level `ocr_page_count` (`docling_adapter.py`, `ParseResult`), and a page count cannot populate a block origin. Before any v2 writer code, the AI engineer proves or disproves a per-item provenance hook on the pinned converter (Docling 2.126.0 under the F0005 lock):

- **Fixtures:** one native PDF, one fully scanned PDF, and one mixed page (native text layer plus an OCR'd image region), all synthetic and outside the frozen holdout.
- **Pass criteria (all required):** every native text item maps to `STATED` with an observed producer identity; every OCR'd item maps to `OCR` with engine name/version; on the mixed page, each item has exactly one observed origin, or the adapter returns `ORIGIN_UNAVAILABLE` for exactly the items it cannot attribute. No origin is derived from page OCR counts or from "not OCR".
- **Evidence:** a reproduction command, converter/package versions and per-item expected-versus-observed tables and, for each mixed fixture, the count of items returning `ORIGIN_UNAVAILABLE` (the expected per-document v1 fallback rate after activation), kept in the feature evidence package.
- **Exit decision:** the Architect records PASS or FAIL in the feature run's gate decisions before Step 1 item 1 starts.

**On PASS:** implement items 1–8 below and enable the v2 writer for new sources only after Step 4's consumer compatibility passes. The switch is the non-secret composition-root setting `content.v2_writer_enabled` in `config/local.yaml`, default `false`. After activation, a document with any `ORIGIN_UNAVAILABLE` item publishes through the per-document v1 fallback (Step 2 item 10).

**On FAIL (operator decision 2026-10-16):** new sources keep the existing v1 writer, v1 namespace and v1 identity derivation (`worker_cli.py`). The v2 readers, shared verifier, indexes for v2 records, date storage and legacy-read work still proceed. S0002's v2 origin criteria (AC2–AC4, AC6) cannot be signed off, and the feature returns to the operator for a scope decision. A v2 writer is never enabled with inferred origins.

### Step 1b — Versioned records

**New implementation files:** `engine/packages/brain-content/src/brain_content/records.py`, `validation.py`; `neuron/packages/brain-ingestion/src/brain_ingestion/content_projection.py`. Modify manifest.py, parsed_content.py, bundle_writer.py and the pinned extraction adapter's parse-result handoff.

All DTO fields/types are defined in the linked strict JSON Schemas; runtime Pydantic models must reject extras and match those schemas, including nullability. Do not maintain a permissive parallel payload shape. These are the planned Python interfaces:

```python
@dataclass(frozen=True)
class ArtifactKey:
    artifact_id: UUID
    tenant_id: UUID
    knowledge_base_id: UUID
    contract_version: Literal[1, 2]

@dataclass(frozen=True)
class VerifiedBundle:
    key: ArtifactKey
    manifest: ArtifactManifestV1 | ArtifactManifestV2
    manifest_bytes: bytes
    manifest_sha256: str
    files: Mapping[str, bytes]
    blocks: tuple[ContentBlockV2, ...]
    tables: tuple[ContentTableV2, ...]
    layout: tuple[ContentLayoutV2, ...]

def parse_manifest(raw: bytes) -> ArtifactManifestV1 | ArtifactManifestV2: ...
def verify_bundle(key: ArtifactKey, manifest_bytes: bytes,
                  files: Mapping[str, bytes]) -> VerifiedBundle: ...
def build_bundle_v2(parsed: ParseResult[DoclingDocument], *,
                    tenant_id: UUID, knowledge_base_id: UUID,
                    document_id: UUID, version_id: UUID, artifact_id: UUID,
                    source_bytes: bytes, recipe_sha256: str,
                    execution: ParserExecutionV2,
                    provenance: Mapping[str, tuple[BlockOriginInput, ...]],
                    retained_assets: Mapping[str, bytes]) -> tuple[ArtifactManifestV2, dict[str, bytes]]: ...
```

`ParserExecutionV2` exactly matches manifest `execution`. `ContentBlockV2`, `ContentTableV2`, `ContentLayoutV2` match the record schema definitions. `BlockOriginInput` has native_ref:str, text:str, text_origin:the four-value enum, producer:the record-schema Producer, origin_anchor:the schema union, confidence:float|None. The provenance map is keyed by native item reference, not by page-level OCR status.

1. Serialize native JSON with all needed assets retained, without lossy reconstruction from Markdown.
2. For each native text item, use its observed producer provenance. Preserve one origin per block; mixed-origin native items become separate attributable blocks only when actual subspans identify the split, otherwise return `ORIGIN_UNAVAILABLE`.
3. For a single origin, retain the stable native reference as the local block ID; if a proven split is necessary, append `:<origin>:<zero-based-segment>`. One block has a list of all genuine regions. Never duplicate block IDs per region.
4. Preserve actual reading order and section paths from the native document hierarchy, not a text-array assumption. If the pinned export returns `ORIGIN_UNAVAILABLE` for any item, abandon the v2 projection for that document and use the per-document v1 fallback (Step 2 item 10). Any other missing required provenance (for example, no observed producer identity) stops publication and retains the failed attempt diagnostics. Never infer STATED from “not OCR”.
5. Tables preserve cells, zero-based row/column and spans, header rows and explicit continuation links when present. Absent continuation information is null, not inferred from similar text. Each cell's block references point to stored blocks; merged-cell coverage is validated and repeated headers remain distinct.
6. Retain original block text; derive code-point regions from the native model with explicit bounds checks. Missing exact geometry/offsets is represented by nullable region fields or unresolved anchor, never a guessed location.
7. Validate schemas plus semantics: unique record IDs/paths, `0 <= start <= end <= len(text)`, monotonic transcript time, finite ordered bbox within actual canonical page dimensions, page count consistency, cell bounds/nonoverlap, header bounds, no continuation cycles, same-artifact references and native asset closure. Empty valid JSONL is allowed for absent blocks/tables; missing files are not.
8. Build v2 file/hash inventory, then call the common verifier before publication. Empty or failed source conversion cannot become a complete parse; partial has explicit diagnostics.

Items 1–4 and 8 (the v2 writer path) depend on a Step 1a PASS. The v2 record contracts, their validators (item 7) and the v2 reader are built either way.

**Checkpoint:** native and scanned fixtures have truthful origins; a multi-region item is one block; repeated amounts, merged cells, astral Unicode, rotated/missing geometry and mixed-origin rejection have persisted expected outcomes. TRANSCRIBED/DESCRIBED examples prove only shape/storage, not new engine execution or canonical authority.

## Step 2 — Persistence and fenced publication (S0001/S0002)

**New implementation files:** `engine/packages/brain-content/src/brain_content/service.py`, `engine/packages/brain-persistence/src/brain_persistence/content_models.py`, `content_repository.py`, and the next available Alembic revision after `0007` (currently proposed `0008_f0004_content_contract.py`), and `neuron/packages/brain-ingestion/src/brain_ingestion/integrity_sweep.py` with its operator CLI entry point. Update models imports, async/sync stores, worker registration and API composition.

The exact proposed columns/constraints are in [persistence design](persistence-design.sql). It is a design artifact, not an applied migration. `content_block`, `content_table`, `content_table_cell` and their block-link relation index immutable JSONL records; text/native bytes remain in the object store. Store exact record ordinal and SHA-256 so an index can be checked against retained bytes. Indexes never become a second text authority.

```python
class ArtifactRepository(Protocol):
    def find_source(self, tenant_id: UUID, knowledge_base_id: UUID,
                    source_sha256: str) -> tuple[UUID, tuple[ArtifactKey, ...]] | None: ...
    def get_key(self, artifact_id: UUID) -> ArtifactKey: ...
    def register_ready(self, bundle: VerifiedBundle, *, actor_id: UUID,
                       authorization_decision_id: UUID,
                       supersedes_artifact_id: UUID | None) -> None: ...

class VerifiedContentStore(Protocol):
    def publish(self, key: ArtifactKey, manifest_bytes: bytes,
                files: Mapping[str, bytes]) -> VerifiedBundle: ...
    def load_verified(self, key: ArtifactKey) -> VerifiedBundle: ...

def publish_ready(connection: Connection, *, lease: JobLease,
                  key: ArtifactKey, manifest_bytes: bytes,
                  files: Mapping[str, bytes], actor_id: UUID,
                  supersedes_artifact_id: UUID | None) -> VerifiedBundle: ...
```

Repository methods participate in the caller's existing unit of work and never commit independently. `publish_ready` is the expanded worker registration boundary, invoked through existing `queue.publish_transaction`; the engine application service owns the same semantics for non-worker callers. `ArtifactKey` comes from trusted resource/source metadata, never the request body.

1. Resolve source/version/accepted-artifact identity and resource restrictions through F0002. Reuse an existing supported accepted artifact before considering v2 conversion. Changed profile is always reinterpretation; changed parse recipe requires explicit governed replacement basis. Preserve old IDs, including recipe-derived legacy version IDs.
2. Acquire locks in the existing queue order: job-generation fence → current authority → source/version → artifact. `publish_transaction` acquires its fence before invoking the callback; do not claim the callback can acquire authority first. Close any preflight authorization transaction before entering the queue transaction. Non-worker callers omit the job lock and never acquire it after authority. Use the existing `SyncAuthorityStore`/`decide` within the transaction, with current `content_artifact:ingest` permission and provisioned pre-record resource scope. Use scoped source/version advisory transaction locks before creating first-time metadata, then an artifact-ID advisory transaction lock before object writes; external callers must use the same lock order.
3. Validate all bytes/records before exclusive file creation. V2 uses scoped keys; v1 uses its existing namespace. Same key/same bytes is idempotent. Same key/different bytes is `ARTIFACT_CONFLICT`; no overwrite. A prior complete marker must verify and match identity/content; preserve its original creation timestamp and raw bytes.
4. Write and verify files, then exclusively create the completion marker. Recheck current authority, fence and source ownership before registering database readiness. The local store is the only supported adapter; no cross-provider transaction guarantee is implied.
5. In the same DB transaction insert or verify source/version/artifact, all content indexes, resource ownership, and one `content_artifact_published` audit event carrying IDs/hash and authorization decision reference. Existing registration is extended rather than replaced. Indexed rows and the successful mutation event are idempotent on artifact identity; a failed transaction leaves neither.
6. Commit before extraction proceeds. If DB commit fails after marker creation, the marker is not advertised through a ready metadata row; retry under a new valid fence loads/verifies it and registers the same identity without conversion. If permission was revoked, registration is denied: the transaction rolls back, the denial decision is appended and committed on its own, and the worker writes nothing else. The orphan bytes are retained. The integrity sweep (item 9) records them as an `ORPHAN_MARKER` repair record for a later explicitly authorized repair. They are never automatically reparsed or deleted.
7. Readers authorize before opening bytes, then validate the bundle and verify DB manifest/content identity. For `ready` v2 rows this is the stored `manifest_sha256` and v2 bundle hash. For `legacy_unverified` and `ready` v1 rows it is the v1 bundle hash against `artifact_sha256`, recomputed on every read (operator decision 2026-10-16); a null `manifest_sha256` on a legacy row is expected and is not itself a failure. A missing/corrupt file beneath a marker returns `ARTIFACT_INTEGRITY`; never fall back to another key, recipe, or conversion. A marker without a row is inaccessible through normal APIs. `quarantined` rows always return 409 `ARTIFACT_INTEGRITY`.
8. **A read fails; it never writes state (operator decision 2026-10-16, re-review R-H1).** A definitive verification failure (hash mismatch, a declared file missing under a complete marker, an invalid manifest) raises `ArtifactIntegrityError` from the `load` callback. `AuthorizationExecution.read` already persists that read decision with outcome `failed`, and the route maps the error to 409 `ARTIFACT_INTEGRITY`. The read path writes nothing else: no state event, audit event or repair record. Every later read re-verifies and fails the same way, so blocking a corrupt artifact never depends on its quarantine. Transient storage errors (`CONTENT_UNAVAILABLE`, 503) are not definitive.
9. **Integrity sweep.** `brain-content-integrity-sweep` is a new operator CLI (`neuron/packages/brain-ingestion/src/brain_ingestion/integrity_sweep.py`, DevOps runbook). It runs as the ingestion ServicePrincipal on demand: after failed `content_artifact:read` decisions appear in audit, after a restore drill, and before writer activation. It is synchronous, so it authorizes the way Step 2 item 2 does, never through the async `AuthorizationExecution` and never through the worker's separate pre-step gate (`document_delivery.py`, which commits its decision before the job step). Each unit opens one session and transaction, calls `brain_security.execution.decide` over `SyncAuthorityStore` for the `CONTENT_ARTIFACT` key with current `content_artifact:ingest`. If allowed, it runs the effects below in that transaction, appends the decision once with outcome `succeeded` (as `mutate` does) and commits once. If denied, it appends and commits only the denial. Any failure rolls back, then appends a `failed` decision in a fresh transaction. This is the "in-transaction authorization" the backfill and repair also use. For each in-scope `legacy_unverified` or `ready` row, the unit:
   - locks the row and re-verifies the full bytes with the shared verifier;
   - on a definitive failure, inserts in foreign-key order: one `content_repair_record` (`INTEGRITY_FAILURE`), one `content_artifact_quarantined` audit event, one `content_artifact_state_event` (trigger `INTEGRITY_SWEEP`, actor = the ingestion ServicePrincipal, `authorization_decision_id` = this unit's decision, referencing both), then updates `publication_state`;
   - leaves a row that verifies unchanged;
   - reports transient errors without changing anything.

   Everything commits with the decision, or nothing does. The sweep also inventories complete markers that have no row. For each one, it appends an `ORPHAN_MARKER` repair record under in-transaction authorization on the marker's `CONTENT_ARTIFACT` key with `require_record=False`, using the provisioned pre-record scope (as the existing worker gate does). Leaving quarantine requires `AUTHORIZED_REPAIR` under the same in-transaction authorization: current `content_artifact:ingest`, full byte re-verification and audit.
10. **Per-document v1 fallback (operator decision 2026-10-16, re-review R-M1).** With `content.v2_writer_enabled=true`, if the Step 1b projection returns `ORIGIN_UNAVAILABLE` for any item, the publisher discards the v2 projection. It publishes that document as a v1 bundle, using the same fenced, authorized transaction as item 5. The source and document version keep the ADR-0073 §3 identity already resolved before conversion (`version_id = uuid5(document_id, 'source-v1:' + source_sha256)`); only the bundle falls back, to the v1 contract, the v1 namespace `bundles/{artifact_id}/` and `artifact_id = uuid5(version_id, 'content')`:
   - the row is inserted `ready` with `artifact_contract_version=1` and `writer_fallback_reason='ORIGIN_UNAVAILABLE'`;
   - `content_artifact_published` carries the reason and `unattributed_item_count`;
   - no v2 records or origins are written.

   Later runs reuse that accepted v1 artifact. Moving it to v2 needs a governed replacement, which adds a v2 artifact under the same document version. Every other v2 contract or validation failure still fails the publication.

| Failure point | Observable result / recovery |
|---|---|
| Before marker | No ready row; valid current publisher may resume identical files; conflicting partial bytes fail |
| After marker, before ready commit | Verified orphan marker; authorized fenced retry adopts it without parse |
| Stale generation/revoked permission | No ready/audit mutation commit; existing complete bundle stays unchanged |
| After ready commit, before worker acknowledgement | Idempotent lookup returns same artifact; no duplicate content event/indexes |
| Missing/corrupt bytes after readiness | Authorized read fails explicitly; repair/restore is governed, not a cache-miss retry |
| Partial parse, intact bundle | Ready content with quality `partial`; failed-page evidence cannot imply a negative fact |
| Definitive verification failure on read | The read decision is persisted `failed` and the read returns 409. The row is unchanged until the integrity sweep quarantines it (state event, audit, `INTEGRITY_FAILURE` repair record). There is no reparse. |
| Unattributable item with v2 enabled | The document publishes as v1 with `writer_fallback_reason=ORIGIN_UNAVAILABLE`, recorded in its audit; no v2 origins |

**Migration sequence:** deploy dual-version readers first; expand nullable metadata columns and new empty tables; inventory and verify legacy rows/bytes; backfill only observed manifest version/hash/recipe metadata, leaving unavailable origin/date data absent; reconcile the existing single-artifact uniqueness and replace it with v2 source-version/recipe uniqueness; enable v2 writers only after all consumers pass. The backfill runs as an operator-run migration job under the existing ingestion ServicePrincipal, using in-transaction authorization (item 9) with current `content_artifact:ingest`. Each row's decision, repair record, audit and state event commit in one transaction, in foreign-key order. Each verified legacy row moves `legacy_unverified → ready` with a `LEGACY_BACKFILL` state event. A row that fails verification moves to `quarantined`. Missing/ambiguous legacy metadata leaves the row `legacy_unverified` (still readable through the v1 verifier) and appends a `content_repair_record` (`LEGACY_BACKFILL_BLOCKED`, with the missing fields in `detail`). DevOps owns triage of repair records. Only operator-run jobs (the backfill and the integrity sweep) and authorized repair append them, always under in-transaction authorization. The restore drill runs against an isolated target and reports in its own evidence; production effects come from the integrity sweep run after the drill. No API route and no tenant or human grant reads or writes them. No source hash is used to infer a new owner. Do not edit migrations 0001–0007.

Downgrade is allowed only before any v2/date/index data exists. Otherwise refuse destructive downgrade and use forward repair. Original bundle/source/archive history must survive every migration test.

## Step 3 — Date candidates and explicit selection (S0003)

**New implementation files:** `engine/packages/brain-content/src/brain_content/dates.py`, `engine/packages/brain-persistence/src/brain_persistence/document_dates.py`; DTOs follow the date-record schema. No date route or UI is added.

```python
@dataclass(frozen=True)
class VerifiedHumanDateBasis:
    decision_id: UUID
    document_version_id: UUID
    actor_principal_id: UUID
    authorization_decision_id: UUID
    decided_at: datetime
    date_value: str
    precision: Literal['YEAR', 'MONTH', 'DAY']
    receipt_sha256: str

class HumanDateDecisionVerifier(Protocol):
    def verify(self, decision_id: UUID, *, document_version_id: UUID,
               date_value: str, precision: str) -> VerifiedHumanDateBasis: ...

class SourceMetadataDateVerifier(Protocol):
    def verify(self, *, document_version_id: UUID, system: str,
               record_id: str, field: str,
               date: DocumentDateValue) -> SourceMetadataDateBasis: ...

@dataclass(frozen=True)
class VerifiedHumanSelectionBasis:
    decision_id: UUID
    document_version_id: UUID
    candidate_id: UUID | None          # None = explicit clear
    expected_selection_id: UUID | None
    actor_principal_id: UUID           # the deciding human
    authorization_decision_id: UUID
    decided_at: datetime
    receipt_sha256: str

class HumanDateSelectionVerifier(Protocol):
    def verify_selection(self, decision_id: UUID, *, document_version_id: UUID,
                         candidate_id: UUID | None,
                         expected_selection_id: UUID | None) -> VerifiedHumanSelectionBasis: ...

class DocumentDateService(Protocol):
    async def append_candidate(self, principal: Principal, *, artifact_id: UUID,
                               date: DocumentDateValue, basis: DateBasisInput,
                               supersedes_id: UUID | None,
                               idempotency_key: str, trace_id: str) -> DocumentDateCandidate: ...
    async def select(self, principal: Principal, *, artifact_id: UUID,
                     candidate_id: UUID | None, expected_selection_id: UUID | None,
                     human_decision_id: UUID, reason: str, idempotency_key: str,
                     trace_id: str) -> DocumentDateSelection: ...
    async def read(self, principal: Principal, *, artifact_id: UUID,
                   selection_id: UUID | None,
                   trace_id: str) -> DocumentDateView: ...
```

`DocumentDateValue`, candidate and selection fields are exactly their schema definitions. `DateBasisInput` is CONTENT `{kind,artifact_id,block_id,record_ordinal,record_sha256,quote}`, SOURCE_METADATA input `{kind,system,record_id,field}`, or HUMAN `{kind,decision_id}`; every other HUMAN basis field is obtained from the trusted verifier, never accepted from this command. `SourceMetadataDateBasis` is the schema SOURCE_METADATA object; its source value and snapshot hash likewise come from the trusted metadata verifier. `DocumentDateView` contains document_version_id, candidates:tuple[DocumentDateCandidate,...], selection:DocumentDateSelection|None, selected_date:DocumentDateValue|None. This internal DTO is not a manifest field or public API response.

1. Use `AuthorizationExecution.mutate` on the trusted artifact with existing `ingest` authority for source metadata writes; `read` for queries. A ServicePrincipal with the existing grant records CONTENT/SOURCE_METADATA candidates. In v0.1 the same caller can invoke `select` only as the carrier of a verified human selection decision (operator decision 2026-10-16, BLUEPRINT §4.11 no-automated-decider guard); `ingest` alone never selects. No human gains this grant through the feature.
2. Hydrate the source version/tenant/KB from the artifact. Validate date/calendar precision and attributable basis. CONTENT resolves exact same-version source text and the original blocks.jsonl line by zero-based ordinal and SHA-256 (line bytes excluding LF/CRLF terminator), then checks block ID and exact quote. V1 can repeat block IDs and has no fabricated v2 indexes; v2 additionally matches its durable block index. Artifact/version/owner foreign keys apply to both versions; SOURCE_METADATA uses a configured trusted adapter to resolve the actual source record under the same owner and check that the field denotes the document’s own date. Its immutable basis retains system, record_id, field and original source_value; snapshot_sha256 is SHA-256 of those four fields serialized as sorted-key compact ASCII JSON. It is an integrity digest of the retained snapshot, not evidence that arbitrary caller text is authoritative. An absent/untrusted adapter fails `DATE_BASIS_INVALID`; controlled adapter fixtures prove the handoff. No new external source connector is introduced. Reject receipt/upload/extraction time fields as document-date sources. Conflicts are separate candidates, not rankable priorities.
3. HUMAN must resolve an exact verified human decision matching owner/version/value/precision and an allowed, non-stale human authority receipt. Default verifier raises `HUMAN_BASIS_UNAVAILABLE`. F0022 will implement that producer; controlled contract fixtures exercise positive storage and tamper rejection now. Neither fixture injection nor schema conformance is production authority.
4. Under a document-version row lock, enforce idempotency. Same request key and identical canonical command hash returns the original row; changed payload with that key raises `IDEMPOTENCY_CONFLICT`. Supersedes references must be same version/scope and cannot self-reference or cycle; append a new candidate, never change the old one.
5. Candidate creation does not automatically select it. Explicit `select` takes the latest selection ID expected by the caller, nullable only for the first selection; a mismatch returns `DATE_SELECTION_STALE`. Every select or clear first resolves `human_decision_id` through `HumanDateSelectionVerifier`; the verified basis must match document version, candidate (or clear) and expected selection, or the call fails `HUMAN_BASIS_UNAVAILABLE`/`DATE_BASIS_INVALID`. The default verifier rejects, so in production nothing selects until F0022 supplies the verifier. The selection row stores the calling principal as `actor_principal_id` and the verified human fields separately. A same-owner candidate can be selected, or null can explicitly clear the selected date. Append selection with consecutive per-version sequence and previous ID. Validate a HUMAN candidate's trusted basis again before selection; denied/revoked human authority cannot be newly selected. No source priority/default winner is inferred.
6. Append `document_date_candidate_recorded` or `document_date_selected` audit in the same transaction, with actor, owner, record IDs, predecessor and authorization decision reference; store the semantic `authorization_decision_id` separately from `authorization_audit_event_id` (the audit row primary key). Resolve the latter from the authorization-decision event in the same transaction and verify its decision ID, allowed outcome, actor, action and owner. Never assume these two UUIDs are equal; log no date quote/PII in routine telemetry. Failures retain authorization audit but create no successful mutation event.
7. Authorized read returns candidates and explicit selection, or one historical selection ID. A caller with no selection sees undated. F0016 consumers pin the exact selection ID in the run configuration/output v2 marker; newer selections never rewrite that basis. No scheduling or calendar resolution is triggered here.

**Checkpoint:** CONTENT/SOURCE_METADATA and controlled verified HUMAN cases round-trip; a select or clear without a verified human selection decision is rejected with no selection row and no success audit; undated stays absent; month/year values stay coarse; forged/missing/stale receipts fail; competing selections, exact retry, changed-payload retry and correction chains preserve history and bundle hashes. Production human authoring and selection remain disabled until the owning F0022 integration supplies its verifiers. The runtime producer of CONTENT/SOURCE_METADATA candidates is an open decision (BLUEPRINT §4.8); F0004 exercises the service with controlled fixtures only.

## Step 4 — Consumers, compatibility and recovery (S0004)

**Modified files:** both content stores; API content route, `engine/apps/api/src/brain_api/deps.py` and error mappings; worker publication/importer; `neuron/packages/brain-extraction/src/brain_extraction/docling_graph_pipeline.py`; ingestion worker/CLI; `scripts/ops/backup.sh`, `restore.sh`, `verify_citations.py`. The exact current adapter module is recorded in GETTING-STARTED. No frontend changes are required unless regression testing finds a contract violation that must be reconciled before build.

### Public read contracts

| Existing endpoint | 200 | Errors after applicable authentication/authorization | Enforcement |
|---|---|---|---|
| `GET /content/{artifactId}` | Exact persisted v1/v2 manifest JSON, including `legacy_unverified` v1 rows that pass the v1 verifier | 400 malformed input; 401 unverified credentials; 404 absent/denied/not-ready (no row); 409 unsupported version, corrupt/inconsistent or quarantined artifact; 503 authorization/storage unavailable | `AuthorizationExecution.read`, `content_artifact:read`; trusted ArtifactKey then verified load; decision audit committed before response |
| `GET /content/{artifactId}/files/{path}` | Exact declared, verified bytes with declared/derived safe media type | Same; traversal/undeclared file is 404 without alternate lookup; malformed input 400 | Same current restrictions, plus declared-path check; no direct/signed object URL |

ProblemDetails uses `application/problem+json`, stable `code`, `traceId`, no protected path or existence detail. An authorized corruption response uses `ARTIFACT_INTEGRITY`; unsupported version uses `ARTIFACT_VERSION_UNSUPPORTED`; transient storage uses `CONTENT_UNAVAILABLE`. Authentication/denial behavior retains the existing F0002 contract. New response contracts remain proposed until the feature implementation lands.

Internal mutations return typed errors rather than inventing HTTP endpoints. Schema/basis errors: `CONTENT_CONTRACT_INVALID`, `ORIGIN_UNAVAILABLE`, `DATE_BASIS_INVALID`, `HUMAN_BASIS_UNAVAILABLE`; conflicts: `ARTIFACT_CONFLICT`, `PARSER_MIGRATION_REQUIRED`, `IDEMPOTENCY_CONFLICT`, `DATE_SELECTION_STALE`; stale lease uses existing `LeaseLost`. A future UI/API owner must map these explicitly when it adds a route.

### Compatibility matrix

| Input/consumer | Required behavior |
|---|---|
| v1 bundle with or without original source | Readable in `legacy_unverified` and `ready` through the v1 verifier during and after migration; quarantined on definitive verification failure. Preserve bytes/IDs/hash algorithm. Return missing-origin/date explicitly in internal views; do not rewrite manifest or invent record-v2 data. Source-dependent operations fail if source is absent. |
| v2 bundle | Both async/sync stores validate the same strict schema, assets, records and hashes; existing PDF evidence translation keeps accepted BoxSelector precision. |
| v1 run output marker | Verify existing four files/hash map under current scope; no fabricated pipeline/date fields. |
| v2 run output marker | Also validate pipeline identity and exact nullable date-selection reference; result/provenance/graph/configuration stay outside parse inventory. |
| Unknown version | Explicit unsupported-version failure; no lenient fallback. |
| Existing source with a new profile or writer version | Reuse accepted supported artifact; no schema-upgrade conversion. |
| New source | v1 writer, namespace and identities while `content.v2_writer_enabled=false` (the default, and permanently so after a Step 1a FAIL). V2 only after a Step 1a PASS and Step 4 consumer compatibility. With v2 enabled, a document with an `ORIGIN_UNAVAILABLE` item publishes a v1 bundle under its ADR-0073 version identity with a recorded `writer_fallback_reason` (Step 2 item 10), never silently. Any other origin or contract failure fails that publication. |

`LocalContentArtifactStore` becomes an async adapter over the verified core, using `asyncio.to_thread` for filesystem work. Worker APIs stay synchronous. Common validation/serialization has no dependency on Docling, FastAPI or SQLAlchemy; the neuron adapter alone maps the pinned native model. No verification cache is introduced. The existing non-secret `config/local.yaml` remains the composition root.

### Restore boundary

Quiesce local ingestion/date writes for the backup window; record the selected database revision and content/run inventory, then capture database plus the complete configured content root and dependency/contract versions. Do not claim a consistent distributed snapshot. Restoration uses an isolated DB/content directory, verifies the backup inventory before use, and runs common verification for every referenced ready bundle and retained run marker, all normalized index hashes, date lineage and cross-owner constraints. Missing required bytes fail the drill. Unreferenced partial/orphan objects are reported separately and never promoted by restore. No automatic deletion or new retention period is introduced.

## Mutation and read traceability

| Entry / action | Service / carrier | Authority | Concurrency | Audit / proof |
|---|---|---|---|---|
| Existing ingestion callback → publish | `publish_ready`; manifest + source/artifact/index rows | Current `content_artifact:ingest`, inherited parent/source restrictions | Authority + job fence + artifact advisory lock; exclusive immutable writes | One publication event with decision ref; crash-point readback; no render-only closure |
| Existing content GET → reload | Verified store and trusted ArtifactKey | Current `content_artifact:read`, all F0002 restrictions | Read decision held/rechecked by facade; immutable content | Decision audit before bytes; corruption and revocation tests |
| Internal source-date handoff → append | `DocumentDateService.append_candidate`; date candidate | Existing scoped ingest plus provenance verification | Document-version lock; same-key payload check | Candidate event; persisted prior/new records and unchanged bundle hashes |
| Internal explicit date choice → select/clear | `DocumentDateService.select`; date selection | Ingest authority as carrier plus a verified human selection decision (always required in v0.1) | Expected previous selection ID + per-version sequence | Selection event; stale choice rejected; historical selection remains |
| Existing run publication → checkpoint | `CheckpointStore.publish_run`; separate output manifest | Current interpret authority + source restrictions | Existing run identity/fence/idempotency | Existing run/job event; separate output hashes and restart reuse |
| Local restore drill | Existing ops scripts plus verifier | Operator-isolated restore; application reads still use current grants | Quiesced snapshot; isolated target | Inventory/citation/ownership/date checks; no permission grant from backup |

## Validation and implementation handoff

Planning checks: strict schemas and [contract examples](contract-examples.json) via [validate-contract-examples.py](validate-contract-examples.py); OpenAPI validator; local feature readiness; KG compile/drift/reproducibility and the ordered G5 validators. These validate the proposed package only.

Planned runtime tests (create during the feature action):

| Story / criteria | Existing suites to extend; new suites | Required observations |
|---|---|---|
| S0001 AC1–AC6 | brain-content `test_store.py`, `test_checkpoints.py`; new `engine/tests/integration/test_content_publication_v2.py` | Missing/corrupt/source/native-asset checks, same/different concurrent publish, fence loss, four crash points, restart reuse, one mutation audit |
| Step 1a spike | new `neuron/packages/brain-ingestion/tests/spikes/test_item_provenance.py` (kept as a regression test on PASS) | Per-item origin on native, scanned and mixed fixtures under the pinned converter; recorded exit decision |
| S0002 AC1–AC7 | brain-ingestion `test_bundle_writer.py`, `test_docling_adapter.py`; new `test_content_projection_v2.py` | Actual native/scanned origins (requires Step 1a PASS); mixed-origin rejection; with v2 enabled, an `ORIGIN_UNAVAILABLE` item publishes a v1 bundle with `writer_fallback_reason` and audit under the ADR-0073 version ID, while a missing producer identity fails; multi-region IDs; cell/header/merge/continuation bounds; Unicode/rotation/unavailable geometry; durable indexes |
| S0003 AC1–AC6 | new brain-content `tests/test_document_dates.py`; new `engine/tests/integration/test_document_date_history.py` | Calendar/source/basis validation, all provenance kinds with controlled verifier, undated/conflict/clear/correction, concurrency/idempotency, denied receipt, select/clear without a verified human selection decision rejected (default verifier and forged receipt), persisted history/audit |
| S0004 AC1–AC6 | API `tests/test_content.py`; existing F0005 compatibility/recovery tests; new `engine/tests/integration/test_content_restore_v2.py`, `test_content_migration_states.py` | Cross-tenant/KB/source/revocation denial across routes and run output reads; Reviewer-only principal (no TenantMember grant) denied `content_artifact:read`; v1 reads before, during and after expand/backfill; a corrupt read returns 409 with a `failed` read decision and no state, audit or repair write; the integrity sweep (`neuron/packages/brain-ingestion/tests/test_content_integrity_sweep.py`) quarantines with its decision, repair record, audit and state event committed in one transaction (and none of them on a mid-unit failure), records orphan markers, and is denied without `content_artifact:ingest`; transient storage error not quarantined; backfill-blocked row stays readable with a repair record; `content_artifact_guard` rejects identity changes and state changes without an event; old/new version matrix; real DB+bytes restore; no fabricated legacy origin; no Graph activation claim |

Use PostgreSQL 18 for owner constraints, locking and migration proofs; SQLite cannot establish these guarantees. The four worked examples map to the corresponding rows. Structured planning examples remain synthetic and outside the frozen holdout. Actual converter/OCR entry points must be forbidden during both reuse calls; self-reported counters alone are insufficient. Run expected-vs-observed evidence with exact commands and environment versions.

Required feature-action reviewers for **all four stories**: Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect. Backend/AI engineers own their fast tests; QA owns independent expectations and integration evidence; Security judges resource/access and provenance authority; DevOps owns migration/restart/restore proof; Architect reviews contract/ADR reconciliation. Changed runtime scope requires at least 80% coverage. Performance budgets stay with F0005/F0026; no unmeasured latency target is asserted.

## Risks, activation and exclusions

1. Per-item producer/origin may be absent in the pinned converter result. Step 1a decides this before writer work. On FAIL, new sources stay on v1 and S0002's v2 origin criteria return to the operator; failing closed is the specified behavior, not permission to guess or activate a new model.
2. Manifest-last publication is not an atomic database/object-store transaction. The explicit orphan-marker recovery and current-authority fence are mandatory tests.
3. Date HUMAN handoff and human selection have no production producer in this scope. Both default verifiers deny, so production documents stay undated until F0022 lands and the candidate producer is assigned (BLUEPRINT §4.8). This is the approved storage/hook boundary, not a newly implemented reviewer workflow.
4. Legacy schema/source-name and duplicate-block behavior require explicit reader versions. Existing locators are never remapped to v2 IDs in place.
5. ADR-0073 remains Proposed until its proof gates pass. Phase B approval authorizes this design for a later feature action, not runtime deployment or acceptance of the broader Proposed ADRs.

No PRD requirement is silently changed. Exact storage/API decisions above refine its implementation. The operator approved the original architecture with `approve-phase-b` after all G4/G5 validation passed. Rework run `2026-10-16-fce2ff91` adds Step 1a, the legacy-read and quarantine state machine, repair records, human-only date selection and the matching tests, from four operator decisions recorded in that run's action context. The operator re-approved the reworked architecture with `approve-phase-b` after all G4/G5 validation passed. Rework run `2026-10-16-06e0131a` (re-review R-H1, R-M1, R-L1) moves quarantine out of the read path into the operator-run integrity sweep through `mutate`, adds the per-document v1 fallback, and stamps the state-event time in the database. The operator re-approved it with `approve-phase-b` after all G4/G5 validation passed. Rework run `2026-10-17-620b7618` fixes six full-review gaps: sync in-transaction authorization for the sweep, backfill and worker denial; fallback identity; insert order; the orphan authorization key; removal of the writerless restore-drill lifecycle values; and status lines. The operator re-approved it with `approve-phase-b` after all G4/G5 validation passed. The next action is feature implementation, starting with Step 1a.
