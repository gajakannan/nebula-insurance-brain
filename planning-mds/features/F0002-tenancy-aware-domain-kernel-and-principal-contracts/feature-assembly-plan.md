# F0002 — Feature assembly plan

**Author:** Architect
**Date:** 2026-09-25
**Status:** Approved design; Phase A and Phase B approved by user on 2026-09-25; runtime proof pending
**Plan run:** `2026-09-25-3c64470a`

## Overview and authority

Extend the existing Python kernel, preserving stable IDs and current pilot grants. Introduce structural ownership, complete current grant slices, typed resource restrictions and bounded delegation; integrate them with the existing content, review, commit and worker boundaries. The [PRD](PRD.md) remains the approved product scope. [ADR-0061](../../architecture/decisions/ADR-0061-tenant-identity-and-structural-ownership.md) and [ADR-0062](../../architecture/decisions/ADR-0062-current-authorization-and-durable-decisions.md) record the design, alternatives and acceptance requirements. Both remain Proposed until their stated approval/proof conditions are met.

This is an implementation specification, not implementation evidence. New paths below are planned files unless explicitly listed as existing. No runtime code, migrations, IdP settings or policy grants were changed by this plan.

## Build order and checkpoints

| Step / story | Deliverable and checkpoint | Owner |
|---|---|---|
| 1 / S0001 | Structural registry and compatible migration; invalid parent/backfill leaves no partial write; existing UUIDs retained | Backend + DevOps; QE |
| 2 / S0002 | Verified external identity aliases, concurrent resolution, explicit kinds and disablement; no protected lookup before verification | Backend; QE/Security |
| 3 / S0003 | Current complete grant slices, revision/expiry and narrowing filters; no role leakage between KBs | Backend; QE/Security |
| 4 / S0004 | Trusted resource hydration and conjunctive restrictions; independent parent/classification/source/dependency negative cases | Backend; QE/Security |
| 5 / S0005 | Explicit delegation and autonomous service paths; next operation denies after expiry/revocation | Backend; QE/Security |
| 6 / S0006 | All existing consumers adopt the shared contract; durable audit failure injection, regression and coverage proof | Backend + DevOps; QE/Security/Code Reviewer/Architect |

Dependencies are intentional security boundaries; each step must have an observable integration checkpoint, not only new dataclasses. Step 1 creates only the ownership/identity substrate and constraints needed for the existing semantic records. It does not implement F0003’s full table inventory or F0017’s matching/merge algorithm.

## Existing code and concrete gaps

| Existing file | Inspected state | Required change |
|---|---|---|
| `engine/packages/brain-domain/src/brain_domain/principal.py` | Principal has five fields; Membership has six, with revocation but no expiry | Retain Principal identity; add membership ID, validity, restriction slices and authority revision via the v1 carrier |
| `engine/packages/brain-security/src/brain_security/principals.py` | Find-then-create; new principal always USER | Unique insert-or-read; trusted kind selection; alias lookup; disabled identity rejection |
| `engine/packages/brain-security/src/brain_security/verification.py` | Signature/issuer/audience/time verification; PyJWKClient; returns VerifiedCredential | Require expected claim types and required claims; trusted issuer/client access-token profile; sanitized failures, controlled key refresh |
| `engine/packages/brain-security/src/brain_security/authorization.py` | Five-field ResourceRef with unused classification default; first matching membership only | Replace caller-supplied snapshots with trusted context/resource loading; shared pure evaluation over complete grant slices |
| `engine/packages/brain-security/src/brain_security/casbin_adapter.py` | Role/resource/action matcher, policy hash covers policy.csv only | Keep permissions/matcher; immutable release identity hashes model and policy plus kernel-contract version |
| `engine/packages/brain-security/src/brain_security/audit.py` | RepositoryAuditSink builds an event; no transaction ownership | Return decision reference; explicit read/deny durability and write-transaction participation |
| `engine/packages/brain-persistence/src/brain_persistence/models.py` | Tenant/KB on selected roots; descendants via joins; principal unique issuer/subject | Add ownership registries and composite FKs; preserve IDs and history; support new identity/grant/delegation/audit carriers |
| `engine/packages/brain-persistence/src/brain_persistence/repositories.py` | Principal create flushes; audit append flushes; content ownership via joins | Use atomic resolution and new transaction-aware adapters; ensure every affected insert carries explicit ownership |
| `engine/apps/api/src/brain_api/deps.py` | Verify → resolve → commit; membership loaded separately; session teardown does not commit read audit | Build verified identity only here; consumer unit of work reloads current authority and commits audit before response |
| `engine/apps/api/src/brain_api/routes/{content,facts,reviews}.py` | Protected reads, file bytes, review submission and commit; read audit lacks explicit commit | Use execution facade and trusted resource hydration; authorize before loading protected payload; no caller-assembled ResourceRef |
| `engine/packages/brain-temporal/src/brain_temporal/commit.py` | Commit locks slot, then authorizes with supplied memberships; state/audit/outbox share transaction | Reauthorize inside existing commit UoW using current context; preserve temporal concurrency semantics and idempotency |
| `engine/apps/worker/src/brain_worker/document_delivery.py` | F0005 DocumentJobAuthorization independently rereads grants and commits audit | Keep synchronous entry point and lease checks; adapt to the shared pure evaluator/current-repository contract; do not change candidate activation |
| `engine/packages/brain-jobs/src/brain_jobs/queue.py` and migration `0004_document_jobs.py` | Job/lease/outbox scope IDs stored as String(36) | Reconcile UUID ownership constraints and update affected writer paths; preserve leases, fencing, retries and outbox behavior |
| `scripts/dev/revoke_membership.py` | Existing revocation entry point | Use authority revision lock/change service and audit; retain CLI compatibility |

The worker is an impacted F0005 consumer, not a prerequisite requiring acceptance of ADR-0060. Regression tests must keep its existing synthetic development behavior while leaving its production activation gates intact. Historical F0001 assembly-plan claims that runtime roots do not exist are not current design authority.

## New files by layer

| Planned file | Responsibility |
|---|---|
| `engine/packages/brain-domain/src/brain_domain/tenancy.py` | Tenant, Workspace, KnowledgeBase, tenant entity identity and KB association invariants |
| `engine/packages/brain-domain/src/brain_domain/authx.py` | Immutable ScopeSlice, ResourceEnvelope, RequestedScope, AuthorizationContext, Delegation and decision types matching the schema |
| `engine/packages/brain-security/src/brain_security/{scope,resources,delegation,evaluation,execution}.py` | Current-scope ports; resource hydration ports; delegation validation; shared pure decision function; transaction-aware execution facade |
| `engine/packages/brain-persistence/src/brain_persistence/{tenancy,identity,authx}.py` | SQLAlchemy repositories implementing the ports; async API and sync worker adapters with identical evaluation inputs |
| `engine/migrations/versions/0005_tenancy_authx_expand.py` | Additive schema and nullable ownership expansion, down_revision 0004 |
| `engine/migrations/versions/0006_tenancy_authx_constrain.py` | Check reviewed backfill, validate composite FKs and enforce non-null ownership; down_revision 0005 |
| `scripts/dev/reconcile_authx.py` | Inventory/dry-run/apply reviewed ownership, identity aliases and explicit restriction/grant mapping; no automatic grants |
| `scripts/dev/provision_delegation.py` | Trusted local provision/revoke CLI, no web endpoint or implicit role |
| `config/authx-identity-profile.yaml` | Non-secret allowed issuer/client/token-profile and explicit service/agent provisioning rules |
| `engine/tests/fixtures/authx/` | Reviewed synthetic migration mappings and executable case inputs; separate from frozen holdout |
| `engine/tests/contract/test_authx_kernel.py` | Schema/implementation equivalence and rejected malformed carriers |
| `engine/tests/integration/test_authx_migration.py` | Real PostgreSQL backfill, FK, atomicity and ID-preservation tests |
| `engine/tests/security/test_authx_{principals,scope,restrictions,delegation,audit,consumers}.py` | Independent security-case and existing-consumer integration proofs |

Unit tests are colocated with the changed packages. No frontend module or AI inference change is planned. A synchronous persistence adapter is necessary for the existing worker; do not call `asyncio.run` inside the worker’s callback or duplicate evaluation rules.

## Contract types and service signatures

[authx-kernel.schema.json](../../schemas/authx-kernel.schema.json) defines the exact serialized v1 fields, required/nullable values, enums and closed-object structure. Generate/validate matching frozen Python dataclasses or Pydantic boundary DTOs; domain types remain free of I/O. Structural validation cannot establish trust or relational consistency.

| Schema definition | Python representation | Domain constraint beyond JSON Schema |
|---|---|---|
| Principal | Existing Principal, UUID/PrincipalKind/PrincipalStatus/string fields | Existing ID survives aliases and migration; kind is trusted registry state |
| OwnedScope | `tenant_id`, `workspace_id`, `knowledge_base_id`: UUID | KB belongs to workspace and tenant |
| ScopeSlice | Membership UUID, OwnedScope, pilot role, UTC validity/revocation, positive revision, selector tuple, allowed classification/source labels | Whole slice must match action AND all restrictions; current at effect time |
| Selector | kind broker/account/policy, mode all/only, tuple of UUIDs | Exactly one selector of each kind per slice; all requires empty IDs; only+empty permits none for that kind |
| ResourceEnvelope | Key, OwnedScope, parent chain, classification/source requirements, dependencies, revisions | Hydrated only from authoritative rows; missing required metadata denies |
| RequestedScope | Optional KB IDs, selectors, optional UTC valid/known query times | null means no extra filter; empty IDs means no requested results; filters cannot grant |
| Delegation | ID, acting/executor/issuer IDs, validity/revocation/revision, exact resource/action ceilings, onward=false | Expiry greater than not_before; issuer authorized to bind acting authority; executor exact match |
| AuthorizationContext | Authenticated and acting Principal, optional Delegation, enforcement time, authority revision, policy release, slices, request filter, trace | Acting=authenticated unless verified delegation binds both; never accepted as public DTO |
| TenancyIdentity | Tenant ID, entity ID, KB scope associations, creation actor/time | Every KB association shares the entity’s tenant; does not grant access |
| Decision | Durable ID, actor/executor/delegation, current revisions, resource/action, outcome/reason and trace | Allow requires complete resolved scope and current policy; no raw token or protected payload |

All datetimes are timezone-aware UTC, UUIDs retain existing values, and collection order has no authorization meaning. Canonical schema files are planning contracts; F0011 owns the broader runtime schema distribution system.

```python
# Domain carriers are defined field-for-field by authx-kernel.schema.json.
# Methods below are the application ports (planned signatures, not installed code).
from collections.abc import Callable
from datetime import datetime
from typing import Protocol, TypeVar
from uuid import UUID

T = TypeVar("T")

class IdentityRepository(Protocol):
    async def resolve_or_create(self, issuer: str, subject: str,
                                kind: PrincipalKind) -> Principal: ...
    async def link_identity(self, principal_id: UUID, issuer: str, subject: str,
                            approval_ref: str, operator_id: UUID) -> None: ...

class ResourceScopeResolver(Protocol):
    async def resolve(self, principal_id: UUID, at: datetime,
                      requested: RequestedScope, *, lock: bool) -> tuple[ScopeSlice, ...]: ...

class ResourceRepository(Protocol):
    async def hydrate(self, key: ResourceKey, *, lock: bool) -> ResourceEnvelope | None: ...

class DelegationService(Protocol):
    async def resolve(self, delegation_id: UUID, executor_id: UUID,
                      at: datetime, *, lock: bool) -> Delegation: ...
    async def issue(self, delegation: Delegation, operator_id: UUID,
                    expected_authority_revision: int) -> UUID: ...
    async def revoke(self, delegation_id: UUID, operator_id: UUID,
                     expected_revision: int) -> None: ...

class PolicyEvaluator(Protocol):
    def permits(self, role: str, scope: OwnedScope,
                resource: ResourceKey, action: str) -> bool: ...

def evaluate(context: AuthorizationContext, resource: ResourceEnvelope,
             dependencies: tuple[ResourceEnvelope, ...], action: str,
             policy: PolicyEvaluator) -> Decision: ...

class AuthorizationExecution(Protocol):
    async def read(self, authenticated: Principal, key: ResourceKey, action: str,
                   requested: RequestedScope, trace_id: str,
                   delegation_id: UUID | None,
                   load: Callable[..., T]) -> T: ...
    async def mutate(self, authenticated: Principal, key: ResourceKey, action: str,
                     requested: RequestedScope, trace_id: str,
                     delegation_id: UUID | None,
                     operation: Callable[..., T]) -> T: ...
```

`load` and `operation` are bound application callbacks invoked with the facade’s existing UoW and decision ID; async adapters await them, sync worker adapters use sync callbacks. They never open an independent canonical-write transaction. Refine typing with `Awaitable[T]` for async implementations. Persisted decision ID is passed into review/canonical mutation audit, rather than trusting a client-supplied reference.

## Step 1 — Ownership, identity substrate and migration (S0001)

New registry shapes (UUID IDs; timestamps UTC):

| Table | Required columns and key constraints |
|---|---|
| tenant | id PK, created_at, created_by operational principal |
| workspace | id PK, tenant_id FK, created_at, created_by; unique(id,tenant_id) |
| knowledge_base | id PK, workspace_id, tenant_id, created_at, created_by; composite workspace FK; unique(id,tenant_id) |
| entity_identity | id and tenant_id composite PK, created_at, created_by; tenant FK |
| entity_knowledge_base | entity_id, tenant_id, knowledge_base_id composite PK; composite entity and KB FKs |
| external_identity | issuer+subject PK, principal_id FK, linked_at, linked_by nullable only for first verified self-provision, approval_ref nullable only for first self-provision |
| principal_authority | principal_id PK/FK, revision positive integer |
| resource_access | resource_type+resource_id PK, tenant_id, knowledge_base_id, parent_chain JSONB, classifications JSONB, source_acl_ids JSONB, dependency_keys JSONB, revision positive, created_at, created_by |
| delegation | Fields in schema Delegation plus created_at; acting/executor/issued_by principal FKs; positive revision; expires_at > not_before |

Resource access records are security control metadata for an existing semantic record, not alternate semantic truth. Their resource registry association must be checked by resource-type-specific repository adapters; use transactional insert and ownership verification, and reconcile missing/orphan metadata before enabling a consumer. No default `internal` value may silently imply enforcement. Classification/source values are opaque exact labels, not an invented hierarchy. Label wildcard is explicit trusted grant data; empty required source list means the trusted resource declares no source ACL, not that hydration failed.

Representative migration SQL, adapted in the named Alembic revisions:

```sql
ALTER TABLE workspace ADD CONSTRAINT uq_workspace_owner UNIQUE (id, tenant_id);
ALTER TABLE knowledge_base ADD CONSTRAINT uq_kb_owner UNIQUE (id, tenant_id);
ALTER TABLE knowledge_base ADD CONSTRAINT fk_kb_workspace_owner
  FOREIGN KEY (workspace_id, tenant_id) REFERENCES workspace(id, tenant_id);
ALTER TABLE entity_knowledge_base ADD CONSTRAINT fk_entity_kb_owner
  FOREIGN KEY (knowledge_base_id, tenant_id) REFERENCES knowledge_base(id, tenant_id);
ALTER TABLE entity_knowledge_base ADD CONSTRAINT fk_entity_kb_identity
  FOREIGN KEY (entity_id, tenant_id) REFERENCES entity_identity(id, tenant_id);
ALTER TABLE source_document ADD CONSTRAINT uq_source_owner
  UNIQUE (id, tenant_id, knowledge_base_id);
ALTER TABLE document_version ADD CONSTRAINT fk_version_source_owner
  FOREIGN KEY (source_document_id, tenant_id, knowledge_base_id)
  REFERENCES source_document(id, tenant_id, knowledge_base_id) NOT VALID;
ALTER TABLE document_version VALIDATE CONSTRAINT fk_version_source_owner;
ALTER TABLE fact_slot ADD CONSTRAINT fk_slot_entity_owner
  FOREIGN KEY (entity_id, tenant_id) REFERENCES entity_identity(id, tenant_id) NOT VALID;
CREATE UNIQUE INDEX uq_external_identity ON external_identity(issuer, subject);
```

Apply the same unique(id,tenant_id,knowledge_base_id) parent key and composite child FK along source_document → document_version → content_artifact → semantic_interpretation_run → assertion → assertion_evidence, review_item → review_decision, fact_slot → canonical_fact_version → canonical_fact_change. Assertion corrections inherit ownership from original_assertion; if both original/run exist their owners must agree. Evidence’s assertion and artifact owners must agree. Review items agree with assertion and batch; review batches are single-KB in v1. An existing mixed-KB batch blocks backfill, not silently splits history. A change’s from/to versions, when present, share scope. Link commit outbox ownership to its commit’s tenant/KB through an explicit commit ownership registry, preserving existing outbox IDs and payloads.

Inventory `document_job`, `document_artifact_lease`, `document_job_event` and `document_job_outbox` from 0004 as well. Convert validated UUID text columns to UUID in the PostgreSQL migration and update queue metadata/writers together; events inherit job scope; outbox and lease composite references must agree with job/artifact ownership. Invalid UUID text or conflicting scope fails preflight. SQLite test adapters can retain their portable representation but are not ownership proof.

Membership adds `valid_from`, `expires_at`, restriction selectors, classification/source allowance and stable row ID in the domain view. Initialize authority revision to at least one for every existing principal; preserve membership IDs and recorded revisions, then advance the principal revision for future changes. Existing known roles remain unchanged. Resource metadata, workspace mapping and any explicit unrestricted selectors come only from a reviewed reconciliation input; missing entries halt activation. No automatic broadening of an existing grant to meet a new fixture.

`reconcile_authx.py --dry-run --mapping <file>` emits counts, orphan/conflict IDs and proposed ownership/alias/restriction changes without content or tokens. `--apply` requires the same input digest plus operational actor and approval reference and writes one transactional, audited batch with expected revisions. Validate every parent and row count before constraints; keep ID/ownership checksums before/after. Do not apply 0006 until its preflight passes. There is no automatic data deletion or online reassignment.

## Step 2 — Verified principal resolution (S0002)

1. Extract bearer; constrain algorithm, issuer, audience, required claims and access-token profile from trusted non-secret configuration. Missing/invalid claim types are sanitized CredentialError outcomes, never uncaught KeyError/500.
2. Verify signature, exp and nbf before any identity/membership/protected-resource lookup. JWKS fetch/cache is verification metadata, not protected business storage. Test controlled refresh for key rotation and reject unknown keys when refresh fails.
3. Resolve exact case-sensitive `(issuer, subject)` alias. Do not normalize subjects or infer identity from email. Existing canonical issuer/subject fields remain for compatibility; alias table is authoritative for additional approved identities.
4. For a trusted human-client profile, first sight creates USER with no grants using a database unique insert-or-read. Service/agent identities require explicit provisioning to their kind; an unknown nonhuman client cannot fall through to USER creation. If a concurrent alias insert wins, roll back the provisional principal with its savepoint and return the winner. No orphan principal rows.
5. Reject disabled principal, including when reached by an alias. Linking a new alias requires operational approval_ref and operator_id, locks the principal, and rejects a pair already linked elsewhere. Never merge two principal histories automatically.
6. Commit identity-resolution audit and mapping before continuing. Neither successful provisioning nor an alias adds membership. Tests preserve previous actor UUIDs in audit and review history.

Invalid verification records an append-only authentication event through a write-only durable sink with unresolved principal and sanitized route template. It never performs identity/resource lookup to enrich logs. If that sink fails, return sanitized 503 and emit minimal local infrastructure diagnostics without credentials; no protected operation occurs. Valid but disabled principals use the same externally generic 401.

## Steps 3–4 — Scope and resource evaluation (S0003/S0004)

1. Establish a database UoW. Lock the current policy-release pointer and participating principal_authority rows in deterministic ID order; load current active principal status and memberships valid at server UTC now. Grant changes/disablement/revocation update these same revisions under exclusive locks.
2. Hydrate only security metadata for the requested resource using its typed repository. Do not load content bytes, fact value, reviewer comment or evidence payload before authorization. Unresolved resource produces indistinguishable 404 with minimal audit; trusted scope fields remain null rather than fabricated.
3. Resolve actual parent chain, classification/source restrictions and complete dependency metadata. Lock resource-access rows in deterministic key order and reread their revisions. Unknown/missing metadata denies. Cross-tenant dependency or malformed cycle denies; v1 maximum dependency traversal is 64 resources and depth 8. Above either bound returns sanitized unavailable/missing-attributes outcome rather than partial evaluation; production-sized traversal is a later feature decision.
4. For each current grant slice in the resource’s exact tenant/KB, evaluate role/resource/action through the unchanged Casbin policy. Then require every relevant broker/account/policy parent ID to be admitted by that same slice, all required classification labels admitted, and all required source ACL labels admitted. One slice must pass the whole conjunction; do not borrow role from slice A and labels from slice B. Multiple fully valid slices form the permitted union.
5. Apply RequestedScope as another conjunction. A requested unknown/ungranted KB/account cannot widen scope. Omitted filters mean no additional narrowing; explicitly empty scope means none. Broker IDs are never tenant IDs. A role in sibling KB A2 is irrelevant to KB A1.
6. Check each evidence dependency’s current visibility restrictions. This is an internal requirement on the requested operation, not a new standalone content read permission. Actual `/content/...` calls still require content_artifact:read; a Reviewer-only principal cannot gain it through review_task:annotate. A derived fixture with any denied evidence path denies the result. No declassification exception.
7. Apply delegation (Step 5), recheck validity/expiry immediately before executing the operation, and produce the immutable policy release plus current revisions in the decision. Do not cache grants or use business valid/known coordinates for authorization.

Policy release: hash exact model bytes, policy bytes and contract version with unambiguous length-prefixed encoding; store immutable release ID and SHA-256. Switching the current release uses the same lock protocol as evaluation. Audit retains legacy F0001 hashes unchanged and records new release identity on new decisions. No existing CSV row or Casbin rule is broadened by this plan.

## Step 5 — Delegation and service execution (S0005)

Trusted operational issue/revoke commands call DelegationService with an explicit operational actor, approval reference and expected revision. The issuing operator must be authorized to provision that acting principal; OS/database access is the existing trusted operational control, not a new pilot business role. Issuance cannot exceed the actor’s current authority. Each ceiling names an exact tenant/KB/resource and finite action set; no wildcard resource, implicit renewal, chained delegation or delegation beyond its expiry.

For delegated calls, independently authenticate the executor; resolve the trusted delegation ID, executor match, actor status, current actor grants and current delegation revision. The envelope’s acting user is loaded from the delegation, not from the job/model payload. Check the requested operation against both current actor authority and ceiling. Executor disablement denies. Autonomous SERVICE uses itself as acting principal, null delegation and its own current memberships; AGENT without delegation has no implied grant. A trusted fixture may give an autonomous agent explicit existing-role grants, but none are introduced by F0002.

Existing worker `DocumentJobAuthorization.for_job(lease)` remains a callable checking lease tenant/KB/artifact and action. A durable job stores trusted executor/acting/delegation references created by its trusted submitter, never a serialized allow result. Its sync adapter reloads authority and invokes the same pure evaluator before each sensitive operation. Publication and import retain lease/fencing and transaction invariants; no stale context can authorize the next job operation. Add a bounded test consumer for delegated reads; no MCP/A2A/chat transport is introduced.

## Step 6 — Transaction and audit contract (S0006)

| Outcome | Transaction and external behavior |
|---|---|
| Allowed read | Evaluate/lock → load permitted payload → append decision → commit audit/UoW → return payload. On any failure before durable audit, release no payload |
| Denied read / nonexistent resource | Append minimal denial with current known context → commit → generic 404. Null unknown ownership; do not hydrate a denied payload |
| Allowed annotation/commit/provisioning | Authorization decision and business change share one UoW; append mutation event and existing outbox where applicable → commit → receipt. Failures roll back all successful-effect records |
| Denied/failed write | Roll back all business changes; append attempted decision/outcome in a fresh audit-only transaction, including original revision/time and failure outcome. Do not reclassify an attempted allow as a successful mutation |
| Audit or current-authority storage unavailable | Abort operation; generic 503 ProblemDetails, no success/no protected data. Minimal process diagnostics contain no content/token |
| Invalid credential | Separate authentication-event sink, no principal/resource read; generic 401, or 503 if required audit cannot persist |

Append-only decision records distinguish `operation_outcome` attempted/succeeded/denied/failed; permission allow is not a successful business commit. Decision IDs correlate attempt and terminal outcome events. Existing audit rows are not rewritten; use a v1 JSON payload/new event columns for richer actor kind, scope, release, delegation and resource revisions. Authorization grant revision denotes the monotonic principal-authority revision; individual matched membership IDs and their revisions remain in the context snapshot. Avoid fabricated grant revision zero for a verified principal that now has no memberships.

Lock order: policy pointer, authority rows by principal ID, delegation row, resource access rows by typed key, then semantic/slot rows by ID. Grant and restriction editors follow compatible ordering. Batch review resolves and locks every item before any mutation. Existing `CanonicalCommitService` uses the same UoW and does not commit internally; slot lock and GiST conflicts retain existing behavior. Read completion linearizes before lock release; a revocation already committed before a new operation must be observed. Already emitted/downloaded bytes cannot be recalled. Never retain a context across job steps or HTTP requests.

## Endpoints and error compatibility

OpenAPI is [brain-api.yaml](../../api/brain-api.yaml), design version 0.2.0. Existing payloads and successful receipts remain unchanged; no public endpoint accepts the internal schema. New documented file operation already exists in code. All affected protected operations add sanitized 503 availability behavior. 403 remains a reserved shared catalog entry, not the denial response on these routes.

| Entry point | Required existing action | Success | Failures |
|---|---|---|---|
| GET /content/{artifactId} | content_artifact:read | 200 manifest | 400 invalid input, 401 unauthenticated, 404 missing/denied, 503 unavailable |
| GET /content/{artifactId}/files/{path} | content_artifact:read | 200 exact manifest-declared bytes | Same; traversal/undeclared file yields 404; never open bytes before allow |
| GET /reviews/{reviewItemId} | review_task:read | 200 existing review DTO | 400/401/404/503 |
| POST /reviews/batches/{reviewBatchId}/decisions | review_task:annotate per item | 200 existing receipt | 400 malformed, 401, 404 inaccessible item/batch, 422 invalid or stale business decision as existing contract, 503 |
| GET /facts/{factSlotId} | fact_slot:read | 200 fact at valid/known coordinate | 400/401/404/503; historical coordinate never changes grants |
| POST /facts/{factSlotId}/commits | fact_slot:commit | 201 existing commit receipt | 400/401/404, existing 409 concurrency/422 validation, 503 |
| Worker ingest / interpret | content_artifact:ingest or interpret | Existing job/publication behavior | PermissionError for deny; bounded retry of availability failure under existing job policy, always reauthorize |

Authorization precedes parent/batch membership errors that would disclose an inaccessible item. Once independently authorized, a wrong batch reference may use the existing sanitized 422. Do not return tenant/KB/reason-code details to callers. Preserve existing stale-version and duplicate-submission semantics; batch failure rolls back all new decisions, then durably audits the failure.

No new route registration is needed except keeping the already implemented catch-all documented. FastAPI route handlers delegate to the execution facade; `get_authorization_service` composes the shared evaluator, repositories, clock, policy-release provider and UoW instead of injecting an unchecked membership snapshot. Authentication stays ahead of all protected storage use.

## Mutation traceability

| Story / entry | Command/service | Carrier and concurrency | Validation failure | Durable evidence / test |
|---|---|---|---|---|
| S0001 operational reconciliation | reconcile_authx.apply → tenancy repository | Ownership mapping digest + expected revisions; atomic batch | OwnerConflict, invalid UUID, missing parent → no changes | ScopeReconciled event; fresh-query ownership/ID checks |
| S0002 first verified resolution/link | IdentityRepository.resolve_or_create / link_identity | Unique issuer/subject; savepoint/upsert; existing principal lock | Invalid credential, disabled principal, AliasConflict | PrincipalResolved/IdentityLinked; concurrent replay yields one ID, audit actors retained |
| S0003 grant change/revoke | authority repository + revoke_membership CLI | Membership expected revision, principal_authority exclusive lock | RevisionConflict or invalid scope | MembershipChanged/Revoked + monotonic revision; next request denies |
| S0004 review submission | AuthorizationExecution.mutate → ReviewDecisionService.submit | Item/batch/resource revisions; existing assertion version and event hash | 404 scope deny; 422 authorized invalid decision | Decision + existing review mutation audit; reload annotation, no canonical change |
| S0005 issue/revoke and job | DelegationService.issue/revoke; worker adapter | Expected authority/delegation revision, finite expiry, executor binding, lease fence | Missing/expired/forged/wider ceiling → no effect | DelegationIssued/Revoked, executor+actor decision; next job step denied |
| S0006 existing canonical commit | AuthorizationExecution.mutate → CanonicalCommitService.commit | Current authority + slot lock + existing temporal constraints | 404 authorization; 409 stale/concurrent; 422 invalid | Decision, canonical change, outbox atomic; denial/audit-failure leaves no change |

Operational event payload: event_id, event_type, occurred_at, operational actor, affected IDs, before/after revision, approval_ref and input digest; no tokens/content. Description templates are `<event_type> for <resource_type>/<id> by <actor_id>`; internal audit only, no new UI timeline. Repeat apply with the same accepted digest is a no-op receipt, not a second grant. All timestamps come from the injected trusted clock, never request text.

## Reconciliation and scope matrix

The approved PRD explicitly resolves the old §116.1 wording: F0002 proves authorization on review and commit independently; it never automatically turns an annotation into canonical truth. F0018 owns that broader orchestration, F0022 its review surface. ADR-0062 and gate-decisions.md record this reconciliation. There was no existing F0002 assembly plan to overwrite.

| Master blueprint §121.2 category | F0002 proof | Remaining owner |
|---|---|---|
| Credentials/principals | Invalid credentials/claim types, service audience, key refresh, disabled principals, aliases, concurrency | Production IdP migration rollout: F0026 |
| Scope | Two tenants, sibling workspaces/KBs, broker/account/policy restrictions, mixed roles, expired grants, filters | Actual downstream search/query adapters: owning feature |
| Parent/classification | All independent conjuncts, file bytes, bounded dependency fixture | Declassification and full review assembly: F0022/F0026 |
| Projection leakage | Kernel boundary and existing consumers; no payload read before allow | Search/vector/graph/count/export implementations: F0033–F0035/F0046 |
| Conversation/session/continuity | No new transport/UI; typed contract only | F0021/F0037–F0040 |
| Review authority | Authenticated annotation, batch recheck, independent commit authority | F0018/F0022 |
| Delegation | Actor/executor ceiling, expiry, revocation, autonomous service; bounded consumer | MCP/general execution: F0047/F0059 |
| Policy parity | Same Python evaluator in sync/async consumers; exact pilot matrix | Python/.NET runtime parity: F0026 |
| Temporal separation | Current grants override past business coordinates | Broader history/derivative surfaces: F0020/F0026 |

## Verification and handoff

Planned implementation commands (not run during this plan):

```bash
uv run --project engine pytest engine/tests/contract/test_authx_kernel.py
uv run --project engine pytest engine/tests/integration/test_authx_migration.py
uv run --project engine pytest engine/tests/security
uv run --project engine pytest engine/packages/brain-security/tests engine/packages/brain-persistence/tests engine/packages/brain-jobs/tests
uv run --project engine pytest engine/tests engine/packages/brain-security/tests --cov=brain_security --cov=brain_domain --cov-report=json --cov-report=term --cov-fail-under=80
```

QE must execute the real PostgreSQL migration, constraint, concurrency and transaction-failure cases; skipped database tests are not a pass. Map every story AC to exact test IDs and actual evidence, including all 18 EX-AUTHX cases and extra no-mixed-slice/expiry/audit cases. Preserve existing F0001 API/commit/review and F0005 worker tests. Verify invalid credentials perform no protected lookup with instrumented repositories; verify bytes are never opened before authorization. Failure injection must include audit insert/commit errors, grant read failure, replay, concurrent revoke/commit, job restart and partial batch failure.

Minimum changed-kernel line coverage is 80%; additionally retain the product’s 80% workspace requirement where applicable. Negative authorization cases must all pass; coverage percentage never substitutes for their outcomes. Measure local p50/p95 decision latency and fixture sizes, without inventing a production SLO. No authorization grant cache; bounded dependency traversal prevents unbounded work. Authentication/JWKS availability failure must deny without fallback.

Required story-level signoffs: Quality Engineer, Code Reviewer, Security Reviewer, DevOps and Architect. Security owns independent threat/access review and Phase C evidence; this architecture document is not a security role report. DevOps verifies migrations, rollback/restore and non-secret configuration. No frontend/AI implementation is required, but worker integration must not expose identity to the model or permit neuron-owned canonical SQL.

Future consumers use engine application ports or protected APIs; identity or delegation is never an unrestricted Neuron database credential. No A2A/MCP protocol, prompt, tool catalog or conversation store is added. Existing deployment/container topology and C4 L1/L2 remain applicable; the feature README supplies ERD and component views.

## Plan exit evidence

G4 compiles authored KG shards and checks drift. G5 validates stories, regenerates STORY-INDEX, validates trackers without feature evidence, refreshes coverage, checks drift/reproducibility and validates framework templates in that order. Structural schema/example and API checks are additional planning checks. All must be green before requesting `approve-phase-b`. No runtime readiness or acceptance of Proposed ADRs is implied by those checks.
