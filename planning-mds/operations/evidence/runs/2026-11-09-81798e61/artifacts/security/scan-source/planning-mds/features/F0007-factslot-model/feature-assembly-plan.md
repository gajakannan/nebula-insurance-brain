# Feature Assembly Plan — F0007: FactSlot model

**Created:** 2026-11-09
**Author:** Architect
**Status:** In Progress — authorized review remediation run `2026-11-09-81798e61`. Phase B approval and completion run `2026-11-09-b94cfa12` are retained as history; fresh validation and signoff precede renewed closeout.
**Run:** `2026-11-09-60865e32` (A+B, new); Phase A approved with `approve-phase-a` on 2026-11-09.
**NEBULA_PRODUCT_ROOT:** `/home/gajap/uSandbox/repos/nebula/nebula-insurance-brain`

## Overview and Scope

This plan implements six stories and 39 acceptance criteria. The design is recorded in Proposed [ADR-0077](../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md), and this file is an implementation specification, not evidence of delivered code.

The feature delivers six things:

- deterministic, KB-owned slot identity with authoritative qualifier rows;
- SINGLE, MULTI and RELATIONSHIP cardinality, with MULTI members as child slot rows;
- the `fact-answer/v1` carrier: nine states, scoped absence, qualified money and scoped identifiers;
- the four system name predicates with a precedence-free display hook;
- additive ownership keys and triggers;
- an RLS inventory handed to F0018.

The feature does not add:

- a deployable, UI, HTTP route, permission grant or Casbin row;
- a producer activation, an ontology registry or RLS enablement;
- DDL on `canonical_fact_version`.

The pilot `GET /facts/{factSlotId}` and commit contracts keep their shapes. The commit route gains new 422 reason codes for identity-v1 slots only. The existing C4 context and container diagrams still apply, and the feature README carries the ER and component diagrams.

## Existing Code and Reconciliation

| Existing path | Current behaviour | Required change / boundary |
|---|---|---|
| `engine/migrations/versions/0003_fact_slots_and_commits.py` | Creates `fact_slot (id, entity_id, slot_type, tenant_id, knowledge_base_id, created_at)` and the version/commit/outbox tables | Unchanged; 0012 is additive |
| `engine/migrations/versions/0005…0007` | `uq_fact_slot_owner (id, tenant_id, knowledge_base_id)`, `fk_fact_slot_entity_owner`, owner-immutable trigger, `brain_append_only()` | Reuse the owner key as composite FK target and reuse `brain_append_only()` |
| `engine/migrations/versions/0011_f0006_assertion_semantics.py` | Current head at planning | New `0012_f0007_factslot_identity.py`, `down_revision="0011"`; recheck the head at feature G0 |
| `engine/packages/brain-domain/src/brain_domain/facts.py` | `FactSlot(id, entity_id, slot_type, tenant_id, knowledge_base_id)` | Keep the class unchanged; add identity carriers in new modules |
| `engine/packages/brain-persistence/src/brain_persistence/models.py` | `FactSlotRow` maps the six pilot columns | Add nullable mapped identity columns; the `FactSlotRow(...)` pilot constructor stays valid |
| `engine/packages/brain-temporal/src/brain_temporal/commit.py` | Locks slot, checks scope, splits, inserts versions | Add an optional `answer_policy` hook after the lock and before `register_commit`. A legacy slot bypasses it; the algorithm is otherwise unchanged |
| `engine/packages/brain-persistence/src/brain_persistence/repositories.py` | `lock_slot`, `current_versions`, `commit_source_keys`, `resolve_at` | Add `slot_identity(slot_id)`; extend `commit_source_keys` with the answer's scope artifact and name-evidence assertion source |
| `engine/apps/api/src/brain_api/routes/facts.py`, `errors.py` | Commit maps eligibility to 422 `ASSERTION_INELIGIBLE` | Map `FactAnswerRejected(reason)` to 422 with `code` = lowercase reason; GET unchanged |
| `engine/packages/brain-testing/src/brain_testing/fixtures.py` | `seed_fact_slot` writes legacy slots | Unchanged; add `seed_identity_slot` for v1 fixtures |
| `engine/packages/brain-persistence/src/brain_persistence/tenancy.py` | `_record_owner`, `provision_resource_access`, `record_operational_event` | Reuse for slot restriction provisioning and creation audit; no change to their contracts |

No earlier F0007 assembly plan exists. Every Phase A requirement maps to a step below, and none is changed.

## Build Order and Exact File Handoffs

Paths are relative to the product root. New runtime paths are proposed and are not KG bindings during plan.

| Step | New files | Modified files | Stories / checkpoint |
|---|---|---|---|
| 0: baseline | `engine/tests/fixtures/factslots/pilot-before.json` (captured slot/version/evidence snapshot and schema hash) | None | S0006 AC1/AC6 |
| 1: pure domain | `engine/packages/brain-domain/src/brain_domain/{fact_slots,fact_values,fact_answers}.py`; `engine/packages/brain-domain/src/brain_domain/data/iso4217-2026-01.txt` | Package data declaration | S0001/S0003/S0004: canonicalization, carriers, reason precedence; no I/O |
| 2: application package | `engine/packages/brain-factslots/pyproject.toml`; `src/brain_factslots/{__init__,ports,predicates,resolution,answers,names,service}.py`; `src/brain_factslots/py.typed` | `engine/pyproject.toml` workspace dependency | S0001/S0002/S0005: registry, resolver, answer policy, name reader |
| 3: persistence | `engine/migrations/versions/0012_f0007_factslot_identity.py`; `engine/packages/brain-persistence/src/brain_persistence/{fact_slot_models,fact_slots}.py` | `models.py` (columns); `repositories.py` (`slot_identity`, `commit_source_keys`) | S0001/S0002/S0006: real PostgreSQL migration, keys, triggers |
| 4: commit integration | None | `brain_temporal/commit.py`; `brain_api/routes/facts.py`; `brain_api/errors.py`; API composition wiring the policy | S0003/S0004/S0005: 422 reasons; legacy unchanged |
| 5: proof | `engine/packages/brain-factslots/tests/test_{canonical,predicates,answers,names}.py`; `engine/tests/integration/test_factslot_{migration,resolution,ownership,answers,names}.py`; `engine/tests/fixtures/factslots/*.json` | `brain_testing/fixtures.py` (`seed_identity_slot`); existing commit/review/assertion suites run unchanged | All 39 ACs; ≥80% changed-code coverage |

Ownership split:

- **Backend:** domain, application, persistence, authorization integration and migration.
- **QE:** independent expectations and runtime evidence.
- **Security:** non-disclosure, derived restrictions and ownership negatives.
- **DevOps:** the migration cycle on the existing Compose stack.
- **Architect:** signs off identity, compatibility and the RLS handoff.
- **Not involved:** Frontend and AI have no scope. F0007 adds no model, prompt or producer.

## Contracts and Carriers

Design schemas live in `planning-mds/schemas/`:

- `fact-slot-key-v1.schema.json`: the resolution request;
- `fact-answer-v1.schema.json`: the stored answer envelope;
- `fact-slot-resolution-result-v1.schema.json`: the server outcome.

`contract-examples.json` holds 26 positive and negative cases, and `worked-examples.md` traces EX-OWN-003, EX-SEM-008 and the §109.1 fixtures. These are internal contracts, not HTTP payloads. Runtime schema publication is F0011.

### Signatures (Python 3.13, frozen dataclasses; design, not code)

```python
# brain_domain/fact_slots.py
class Cardinality(StrEnum): SINGLE = "SINGLE"; MULTI = "MULTI"; RELATIONSHIP = "RELATIONSHIP"
class SlotRole(StrEnum): SLOT = "SLOT"; MEMBER = "MEMBER"          # NULL identity_version => legacy

@dataclass(frozen=True, slots=True)
class PredicateKey:
    namespace: str; local_name: str; major: int                      # parse("sys:hasLegalName@v1")
    @classmethod
    def parse(cls, raw: str) -> "PredicateKey": ...                  # PREDICATE_KEY_INVALID

@dataclass(frozen=True, slots=True)
class QualifierSpec:
    name: str; value_type: ValueType; required: bool

@dataclass(frozen=True, slots=True)
class PredicateContract:
    key: PredicateKey; release_ref: str; cardinality: Cardinality; value_type: ValueType
    qualifiers: tuple[QualifierSpec, ...]; member_key_source: Literal["value", "entity"] | None
    basis_required: bool

@dataclass(frozen=True, slots=True)
class CanonicalQualifier:
    name: str; value_type: ValueType; canonical: str                 # canonical JSON text

@dataclass(frozen=True, slots=True)
class SlotIdentity:
    tenant_id: UUID; knowledge_base_id: UUID; subject_entity_id: UUID
    predicate_key: PredicateKey; qualifiers: tuple[CanonicalQualifier, ...]   # sorted by name
    object_entity_id: UUID | None; parent_slot_id: UUID | None; member_key: str | None
    def document(self) -> dict[str, Json]: ...                       # JCS input, includes fp_version=1
    def fingerprint(self) -> str: ...                                # sha256 hex of JCS bytes

class SlotRejected(Exception):
    reason: SlotReason                                               # enum = resolution-result reasons

# brain_domain/fact_values.py
def canonical_decimal(raw: object) -> str: ...                       # DECIMAL_INVALID / MONEY_FLOAT_REJECTED
def canonical_money(raw: Mapping[str, object], *, basis_required: bool) -> Money: ...
def canonical_identifier(raw: Mapping[str, object]) -> ScopedIdentifier: ...
def normalize_name(verbatim: str) -> str: ...                        # NFC -> casefold -> collapse ws -> strip
IDENTIFIER_NORMALIZATION_VERSION = 1   # {"fein": digits-only, len 9; default: NFC}
ISO4217_LIST_VERSION = "2026-01"

# brain_domain/fact_answers.py
class InformationState(StrEnum): PRESENT, NOT_PROCESSED, NOT_FOUND, NOT_STATED, ILLEGIBLE, \
    AMBIGUOUS, CONFLICTING, EXPLICIT_NEGATIVE, NOT_APPLICABLE
@dataclass(frozen=True, slots=True)
class AbsenceScope:
    content_artifact_id: UUID; profile_release_ref: str
    pages: tuple[int, ...]; block_ids: tuple[UUID, ...]
@dataclass(frozen=True, slots=True)
class FactAnswer:
    state: InformationState; value: TypedValue | None; scope: AbsenceScope | None
    def to_json(self) -> dict[str, Json]: ...                        # canonical stored envelope
class FactAnswerRejected(Exception):
    reason: AnswerReason

# brain_factslots/ports.py
class PredicateContractRegistry(Protocol):
    def contract(self, key: PredicateKey, release_ref: str) -> PredicateContract: ...   # PREDICATE_UNREGISTERED
class FactSlotStore(Protocol):
    async def subject_in_kb(self, tenant_id: UUID, kb_id: UUID, entity_id: UUID) -> bool: ...
    async def insert_or_get(self, identity: SlotIdentity, contract: PredicateContract,
                            actor_id: UUID, at: datetime) -> tuple[StoredSlot, bool]: ...
    async def qualifiers(self, slot_id: UUID) -> tuple[CanonicalQualifier, ...]: ...
    async def artifact_owner(self, artifact_id: UUID) -> tuple[UUID, UUID] | None: ...
    async def name_evidence_owner(self, assertion_id: UUID, document_version_id: UUID
                                  ) -> tuple[UUID, UUID] | None: ...
    async def current_name_facts(self, tenant_id: UUID, kb_id: UUID, entity_id: UUID,
                                 valid_at: datetime, known_at: datetime) -> list[NameFact]: ...

# brain_factslots/service.py
class FactSlotResolver:
    async def resolve(self, key: FactSlotKey, *, authorized_scope: tuple[UUID, UUID],
                      source_keys: Sequence[ResourceKey], actor_id: UUID) -> ResolutionResult: ...
class FactAnswerPolicy:          # injected into CanonicalCommitService
    async def validate(self, slot: StoredSlot, value: Mapping[str, Json]) -> Mapping[str, Json]: ...
class FactAnswerReader:
    async def read(self, slot_id: UUID, *, valid_at: datetime, known_at: datetime) -> FactAnswer: ...
class NameFactReader:
    async def current_names(self, *, authorized_scope: tuple[UUID, UUID], entity_id: UUID,
                            valid_at: datetime, known_at: datetime) -> list[NameFact]: ...
```

`FactSlotResolver.resolve` is always called as the `operation` of `AuthorizationExecution.mutate(principal, source_keys, Action.INTERPRET, ...)`, where `source_keys` are the CONTENT_ARTIFACT keys of the evidence that motivates the slot. `authorized_scope` comes from that decision, never from the payload.

## Data Model and Database Integrity

| Table | Columns and constraints |
|---|---|
| `fact_slot`: existing columns unchanged | Add nullable columns:<br>• `identity_version SMALLINT CHECK (identity_version = 1)`<br>• `slot_role TEXT`<br>• `predicate_key TEXT`<br>• `predicate_release_ref TEXT`<br>• `cardinality TEXT`<br>• `object_entity_id UUID`<br>• `parent_slot_id UUID`<br>• `member_key TEXT`<br>• `fingerprint_version SMALLINT`<br>• `identity_fingerprint CHAR(64)`<br>• `created_by UUID → principal`<br>• generated `subject_kb_entity_id UUID` (= `entity_id` when `identity_version IS NOT NULL`, else NULL) |
| `fact_slot_qualifier`: new | Columns, all NOT NULL:<br>• `slot_id UUID`<br>• `tenant_id UUID`<br>• `knowledge_base_id UUID`<br>• `qualifier_name TEXT`<br>• `value_type TEXT`<br>• `canonical_value TEXT`<br>• `created_at TIMESTAMPTZ`<br>Keys:<br>• PK `(slot_id, qualifier_name)`<br>• composite FK `(slot_id, tenant_id, knowledge_base_id) → fact_slot (id, tenant_id, knowledge_base_id)` |

### Migration SQL and guards (`0012_f0007_factslot_identity.py`)

```sql
ALTER TABLE fact_slot
  ADD COLUMN identity_version smallint, ADD COLUMN slot_role text, ADD COLUMN predicate_key text,
  ADD COLUMN predicate_release_ref text, ADD COLUMN cardinality text, ADD COLUMN object_entity_id uuid,
  ADD COLUMN parent_slot_id uuid, ADD COLUMN member_key text, ADD COLUMN fingerprint_version smallint,
  ADD COLUMN identity_fingerprint char(64), ADD COLUMN created_by uuid REFERENCES principal(id),
  ADD COLUMN subject_kb_entity_id uuid
    GENERATED ALWAYS AS (CASE WHEN identity_version IS NOT NULL THEN entity_id END) STORED;

-- Desired invariant; shipped 0012 stays immutable. Follow-up 0013 installs this guard.
ALTER TABLE fact_slot ADD CONSTRAINT ck_fact_slot_identity CHECK ((
  (identity_version IS NULL AND slot_role IS NULL AND predicate_key IS NULL
     AND predicate_release_ref IS NULL AND cardinality IS NULL AND object_entity_id IS NULL
     AND parent_slot_id IS NULL AND member_key IS NULL AND fingerprint_version IS NULL
     AND identity_fingerprint IS NULL AND created_by IS NULL)
  OR (identity_version IS NOT NULL AND identity_version = 1
     AND fingerprint_version IS NOT NULL AND fingerprint_version = 1
     AND created_by IS NOT NULL AND slot_role IS NOT NULL
     AND identity_fingerprint IS NOT NULL AND identity_fingerprint ~ '^[0-9a-f]{64}$'
     AND predicate_key IS NOT NULL
     AND predicate_key ~ '^[a-z][a-z0-9-]{0,31}:[A-Za-z][A-Za-z0-9]{0,63}@v[1-9][0-9]{0,3}$'
     AND predicate_release_ref IS NOT NULL AND length(predicate_release_ref) > 0
     AND slot_type = predicate_key AND cardinality IS NOT NULL
     AND cardinality IN ('SINGLE','MULTI','RELATIONSHIP')
     AND ((slot_role = 'SLOT' AND parent_slot_id IS NULL AND member_key IS NULL
            AND ((cardinality = 'RELATIONSHIP') = (object_entity_id IS NOT NULL)))
       OR (slot_role = 'MEMBER' AND cardinality = 'MULTI' AND parent_slot_id IS NOT NULL
            AND member_key IS NOT NULL AND length(member_key) > 0 AND object_entity_id IS NULL)))
) IS TRUE);

CREATE UNIQUE INDEX uq_fact_slot_identity ON fact_slot (tenant_id, knowledge_base_id, identity_fingerprint)
  WHERE identity_version IS NOT NULL;
ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_parent_owner FOREIGN KEY
  (parent_slot_id, tenant_id, knowledge_base_id) REFERENCES fact_slot (id, tenant_id, knowledge_base_id);
ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_subject_kb FOREIGN KEY
  (subject_kb_entity_id, tenant_id, knowledge_base_id)
  REFERENCES entity_knowledge_base (entity_id, tenant_id, knowledge_base_id);
ALTER TABLE fact_slot ADD CONSTRAINT fk_fact_slot_object_kb FOREIGN KEY
  (object_entity_id, tenant_id, knowledge_base_id)
  REFERENCES entity_knowledge_base (entity_id, tenant_id, knowledge_base_id);

CREATE TABLE fact_slot_qualifier ( … as above …,
  CONSTRAINT ck_fact_slot_qualifier_type CHECK (value_type IN
    ('text','code','decimal','date','boolean','entity_ref','money','identifier')),
  CONSTRAINT ck_fact_slot_qualifier_name CHECK (qualifier_name ~ '^[a-z][a-z0-9_]{0,63}$') );
CREATE INDEX ix_fact_slot_parent ON fact_slot (parent_slot_id) WHERE parent_slot_id IS NOT NULL;
```

The migration also adds triggers:

- **`brain_forbid_slot_identity_change()`:** BEFORE UPDATE on `fact_slot`. It rejects any change to `entity_id`, `slot_type`, `identity_version` or any identity column, including NULL to value, with `check_violation`. A legacy row therefore can never acquire an identity.
- **`trg_fact_slot_qualifier_append_only`:** BEFORE UPDATE OR DELETE. It reuses `brain_append_only()`.
- **Constraint trigger (DEFERRABLE INITIALLY DEFERRED):** fires on `fact_slot` and `fact_slot_qualifier` inserts. At transaction end it checks that a member's parent is an identity-v1 `MULTI` `SLOT` row, and that a qualifier's slot is an identity-v1 row, not legacy.

Preflight and downgrade behaviour:

- **Preflight:** report `uq_fact_slot_owner` presence and the legacy row count, and fail if the head is not 0011.
- **Downgrade:** refuse when any `identity_version IS NOT NULL` or qualifier row exists, then drop in reverse order.

The pilot `fk_fact_slot_entity_owner` and owner-immutable trigger stay as they are. MATCH SIMPLE leaves legacy rows (NULL generated column) unchecked by the subject-KB key.

### Fingerprint document (version 1)

```json
{"fp_version":1,"tenant_id":"…","knowledge_base_id":"…","subject_entity_id":"…",
 "predicate_key":"test:hasLimitAmount@v1",
 "qualifiers":[["basis","code","\"EachOccurrence\""],["currency","code","\"USD\""]],
 "object_entity_id":null,"parent_slot_id":null,"member_key":null}
```

The fingerprint is the RFC 8785 serialization hashed with SHA-256 and written as lowercase hex. Each qualifier's `canonical` is the JCS text of its canonical value object. The release reference and cardinality are deliberately excluded.

## Resolution Logic and Outcomes

1. **Authorization:** handled by `AuthorizationExecution.mutate` over the source artifacts with INTERPRET. A denial means zero effects and the facade's non-disclosing error.
2. **Predicate key:** parse it, or return `PREDICATE_KEY_INVALID`. Load the contract, or return `PREDICATE_UNREGISTERED`. Then check the shape: a contract cardinality outside the enum is `CARDINALITY_INVALID`; a member on a non-MULTI predicate is `MEMBER_NOT_ALLOWED`; a MULTI predicate without a member is `MEMBER_KEY_REQUIRED`; a RELATIONSHIP predicate without an object is `RELATIONSHIP_OBJECT_REQUIRED`; a non-RELATIONSHIP predicate with an object is `RELATIONSHIP_OBJECT_NOT_ALLOWED`.
3. **Qualifiers:** canonicalize them against the contract (D3 reasons), then build the member key from the canonical member value or entity.
4. **Subject and object scope:**
   - The subject must be associated with the authorized KB, or the result is `SUBJECT_NOT_FOUND`. The same reason covers a subject that does not exist and one that is out of scope.
   - The object must be associated with the authorized KB, or the result is `RELATIONSHIP_OBJECT_OUT_OF_SCOPE`.
5. **Header:** `insert_or_get(header identity)` performs `INSERT … ON CONFLICT ON (tenant_id, knowledge_base_id, identity_fingerprint) WHERE identity_version IS NOT NULL DO NOTHING RETURNING id`, then `SELECT … FOR SHARE` on conflict. It compares subject, predicate, object, parent/member and qualifier rows. A mismatch is `FINGERPRINT_COLLISION`, and a cardinality mismatch is `CARDINALITY_CONFLICT`. On a new row it inserts qualifier rows and provisions `resource_access` in the same unit of work. Classifications and source ACLs are the union of the source artifacts'; `parent_chain` and `dependency_keys` are the sources. It then appends `fact_slot_created`.
6. **MULTI member:** repeat step 5 for the member identity (`parent_slot_id`, `member_key`). The member inherits the header's restrictions plus the current sources', and creation appends `fact_slot_member_created`.
7. **Result:** return `fact-slot-resolution-result-v1`. A rejection after any insert rolls back the savepoint; the caller sees zero rows.

`SELECT … FOR SHARE` after the conflict serializes the read against a concurrent inserter that has not yet committed. The PostgreSQL unique index is the backstop. The test runs two sessions behind a barrier and asserts one slot and one qualifier set.

## Answer Validation at the Existing Commit

`CanonicalCommitService.commit` gets this order:

1. Lock the slot.
2. `slot_identity(slot_id)`.
3. If the slot is identity-v1, run `answer_policy.validate`, which returns the canonical envelope used as the inserted value.
4. Continue the existing algorithm.

For identity-v1 slots, `commit_source_keys` also returns:

- the scope's content artifact (READ);
- the name evidence's source artifact, resolved through `assertion_evidence` (READ).

So an unauthorized scope or evidence is denied before any reason detail (S0003 AC6, S0004 AC7).

Validation rules:

- **Contract and state:** a missing or unknown `answer_contract` is `ANSWER_CONTRACT_UNSUPPORTED`. An unknown state is `INFORMATION_STATE_INVALID`, and a state/value mismatch is `STATE_VALUE_MISMATCH`.
- **Absence scope:**
  - A missing or empty scope is `ABSENCE_SCOPE_REQUIRED`.
  - A scope artifact owned by a different tenant/KB than the slot is `ABSENCE_SCOPE_OUT_OF_SCOPE`. That is reachable only when the caller can read the artifact.
  - A MULTI header is `MULTI_SLOT_REQUIRES_MEMBER`.
- **Value type:** a value whose type differs from the contract is `VALUE_TYPE_MISMATCH`.
- **Member identity:** after authorization and evidence/ownership checks, a PRESENT answer addressed to a MEMBER row must derive exactly its stored `member_key` under the pinned predicate contract. Otherwise reject `MEMBER_VALUE_MISMATCH` with zero fact versions, commits or outbox rows. Canonically equivalent inputs remain valid; a different member resolves a different row.
- **Numeric bounds:** input and canonical output both have a maximum of 64 total characters, including minus sign and decimal point, matching the design schema. Compute canonical length from digits/exponent before constructing zero padding. Oversized canonical outputs reject `DECIMAL_INVALID`, including short exponent inputs. Accepted values must satisfy `canonical_decimal(canonical_decimal(x)) == canonical_decimal(x)` and schema validation on reload.
- **Value detail:**
  - Money and identifier reasons follow D5.
  - A name value with no admitted, eligible, same-owner F0006 v2 assertion is `NAME_EVIDENCE_REQUIRED`. Eligibility reuses the F0006 guard.
- **API mapping:** the reason surfaces as 422 ProblemDetails, `code` is the lowercase reason, and the response has no detail text. The legacy-slot path, the remainder-split value copy, the exclusion constraint and the outbox are unchanged.

`FactAnswerReader.read` returns the stored envelope as a domain `FactAnswer`. If no version exists at the coordinates of an identity-v1 slot, it returns `FactAnswer(NOT_PROCESSED)`. A legacy slot returns its raw value labelled `legacy`, or `None` → `NOT_PROCESSED`. Read authorization is the existing `fact_slot:read` through `execution.read`.

## Mutation Traceability

F0007 adds no screen or user-editable state. Two internal mutations and one changed route path exist:

| Entry point | Action | Service | Carrier / tables | Authorization | Concurrency | Validation failure | Audit | Test |
|---|---|---|---|---|---|---|---|---|
| Trusted engine caller (fixtures now; F0016/F0018 later) | Resolve or create slot | `FactSlotResolver.resolve` | `fact_slot`, `fact_slot_qualifier`, `resource_access` | `mutate(source artifacts, INTERPRET)` | Partial unique index + `FOR SHARE` re-read | Resolution reasons, zero rows | `fact_slot_created` + authorization decisions | `test_factslot_resolution.py` |
| Same | Create MULTI member | `FactSlotResolver.resolve` (member) | `fact_slot` member row, `resource_access` | Same | Same index on member fingerprint | `MEMBER_*` reasons | `fact_slot_member_created` | Same |
| `POST /facts/{factSlotId}/commits` (existing) | Commit answer | `CanonicalCommitService.commit` + `FactAnswerPolicy` | `canonical_fact_version.value` envelope | Existing `fact_slot:commit` + additional READ | Existing row lock + ADR-0008 exclusion | 422 lowercase reason, zero versions | Existing commit audit | `test_factslot_answers.py`, `test_facts.py` |

## Validation Matrix and Completion Gates

| Story criteria | Required implementation verification |
|---|---|
| S0001 AC1–AC7 | Two-session barrier resolve; reordered and differently encoded qualifiers; forced collision through an injected fingerprint function in a test-only composition; omitted-vs-null fixtures; KB A/KB B slots and KB-B-only principal denial equal to not-found; malformed key / missing release zero rows; creation audit row; identity UPDATE rejected by trigger |
| S0002 AC1–AC6 | Cardinality conflict; SINGLE overlap still raises the exclusion (pilot regression); two insured members coexist, duplicate resolves to one; relationship object variations and out-of-scope object; member A close references no member B row; named rejections, member audit and unauthorized denial |
| S0003 AC1–AC7 | All nine states; mismatch; scope required/empty/out-of-scope; unread slot `NOT_PROCESSED`; EX-OWN-003 three answers via `POST …/commits` and reload; scope artifact without READ returns non-disclosing denial; rejected carrier writes no version |
| S0004 AC1–AC7 | Float/unknown currency/missing basis/converted; `1000000`/`1000000.00`/`1E+6` equality; PostgreSQL round trips of `0.01`, `999999999999999.99`, `9007199254740993`; two-carrier `GL-1001`; FEIN forms equal and cross-scheme unequal; money qualifier identity; denial before detail |
| S0005 AC1–AC5 | Four system predicates and cardinality conflict; EX-SEM-008 same slot; name without evidence; KB A trade name invisible in KB B through resolve, read and display hook; hook order documented and no alias rows |
| S0006 AC1–AC7 | `pilot-before.json` byte-equal after upgrade; legacy rows with NULL identity and no fabricated qualifier; existing suites unchanged; composite FK/trigger negatives with direct SQL as the service role; RLS inventory present in GETTING-STARTED; up/down/up with seeded pilot rows; downgrade refusal with v1 rows |

Planning validation consists of:

- the offline schema check of the 26 contract cases (run folder `artifacts/validation/validate-contract-examples.py`);
- plan-readiness and the story/tracker validators;
- G4 compile/drift and the G5 exit sequence.

None of these establishes runtime behaviour.

Proposed implementation commands (not run at plan):

```bash
# cwd: engine/migrations
uv run --project .. alembic upgrade head
# remaining commands: cwd product root
uv run --project engine pytest engine/packages/brain-factslots/tests engine/tests/integration/test_factslot_migration.py engine/tests/integration/test_factslot_resolution.py engine/tests/integration/test_factslot_ownership.py engine/tests/integration/test_factslot_answers.py engine/tests/integration/test_factslot_names.py
uv run --project engine pytest engine/tests/integration/test_bitemporal_commit.py engine/tests/integration/test_commit_concurrency.py engine/tests/integration/test_assertion_consumers.py engine/apps/api/tests/test_facts.py engine/apps/api/tests/test_reviews.py
```

Implementation NFRs:

- at least 80% changed-code coverage;
- zero duplicate slots, zero cross-tenant/KB rows or disclosures, and zero precision loss;
- no new grants, routes or model calls.

Latency is observed and recorded, not given a target.

## Rollout, Rollback and Caching

1. Preserve the committed pilot snapshot and schema hash. Confirm the single migration lineage `0011 → 0012 → 0013`; shipped0012 remains immutable. Inventory existing identities, numeric carriers and member answers before deployment; detected corruption requires explicit governed resolution, not automatic repair.
2. Apply follow-up0013 under its refusal-only preflight, then deploy the corrected domain, application policy and protected-read code. No producer calls the resolver until F0016/F0018 adopt it, and the `test` namespace registry is wired only in test composition.
3. Rollback:
   - stop resolver callers;
   - identity-v1 slots and versions stay readable by the deployed binary, and no binary without the answer policy may commit to them;
   - downgrade0013 restores the exact0012 guard without rewriting data; downgrading below0012 refuses while v1 or qualifier rows exist, and evidence is never deleted to make a downgrade pass.
4. Caching: no result, slot or authorization cache. Only the immutable predicate registry, the ISO 4217 list and the normalization tables are process-cached, and each is versioned.

## RLS Inventory Handoff (F0018)

| Table | Owner columns | Notes for F0018 |
|---|---|---|
| `fact_slot` | `tenant_id`, `knowledge_base_id` | Existing pilot table; identity-v1 headers and members; subject/object KB keys |
| `fact_slot_qualifier` | `tenant_id`, `knowledge_base_id` | New; append-only; composite FK to slot |

F0007 enables no RLS policy and adds no `BYPASSRLS` role, superuser path or `SECURITY DEFINER` function. The deferred constraint trigger and immutability trigger functions run with invoker rights. F0026 proves isolation.

## Dependencies, Future Handoffs and Approval

Delivered prerequisite approvals (F0001, F0002, F0003 and F0006) are referenced in the run's `artifact-trace.md`.

Handoffs:

- **F0008:** per-member temporal close, state supersession, and a database backstop for the envelope.
- **F0011:** runtime schema publication.
- **F0012/F0013:** the predicate registry and any explicit legacy `slot_type` mapping.
- **F0014:** completeness.
- **F0016:** producing absence scopes and adopting the resolver.
- **F0017/F0023:** display precedence and the alias projection.
- **F0018:** RLS, SourceAuthorityPolicy on `predicate_key`, and restriction re-derivation.
- **F0020:** HTTP return of states.
- **F0026:** isolation.

No reverse dependency is introduced.

G4 compiles the authored shards and checks drift. G5 runs every exit operation in order before operator Phase B approval. After approval, the approval metadata is updated, the checkpoint attested, and G5 re-run. No planning edit follows that final refresh. All stories stay Not Started until the feature action.

## Feature-Action G0 Reconciliation (run `2026-11-09-b94cfa12`)

The Architect re-validated this plan at feature G0 on 2026-11-09. The migration head is still `0011` (`artifacts/test-results/g0-migration-lineage.json` in the run folder). Every story requirement stays as approved. Six implementation details are settled here, and none changes a contract, reason code or story outcome:

1. **Commit hook shape.** `brain_temporal.commit` declares a `CommitAnswerPolicy` protocol, `canonical_value(slot_id, value, *, authorized_scope) -> Mapping | None`. `None` means a legacy slot, and the proposal value is then used unchanged. `FactAnswerPolicy` loads the slot identity through its own store, so `brain-temporal` gains no dependency on `brain-factslots`. The hook runs after the slot lock and the range check, before source checks and `register_commit`.
2. **Source-access proof isolation.** The answer's scope artifact and name-evidence artifacts join the commit's `additional_reads`. The F0006 `SourceAccessProof` is issued only from the READ decisions for evidence-derived keys, so the F0006 exact-set rule in `require_commit_sources` still holds when an answer adds reads.
3. **Owned test databases.** The F0007 PostgreSQL suites create a database per test through `BRAIN_MIGRATION_ADMIN_URL`, as the F0006 harness does, and never truncate the shared development database. `pilot-before.json` is generated from deterministic pilot rows seeded at revision `0011`, so it is reproducible and byte-comparable.
4. **Unregistered predicate at commit.** If the deployed registry has no contract for an identity-v1 slot's predicate (for example a `test:` slot reached from production composition), the commit is rejected with `ANSWER_CONTRACT_UNSUPPORTED`.
5. **Name-evidence eligibility.** The evidence assertion must be semantic contract v2, its semantics row must name the supplied `document_version_id`, its tenant and KB must equal the slot's, and the F0006 `evaluate_eligibility` result must not block `CREATE`.
6. **CI wiring.** DevOps adds the F0007 PostgreSQL suites to the `runtime-stack` job and a `brain_factslots` coverage gate to the runtime suites.

## Knowledge-Graph Binding Plan (Feature Action G0)

Planned semantic nodes:

- `capability:factslot-identity-resolution`
- `capability:typed-fact-answer`
- `entity:fact-slot` (refined)
- `entity:fact-slot-qualifier`
- the three schema nodes
- `adr:0077`

At G7 the Architect compares the as-built code with these expected surfaces:

| Semantic surface | Expected binding paths (product-relative) |
|---|---|
| Identity domain and resolver | `engine/packages/brain-domain/src/brain_domain/fact_slots.py`, `engine/packages/brain-factslots/src/brain_factslots/**` |
| Typed values and answers | `engine/packages/brain-domain/src/brain_domain/{fact_values,fact_answers}.py` |
| Persistence | `engine/packages/brain-persistence/src/brain_persistence/{fact_slot_models,fact_slots}.py`, `engine/migrations/versions/0012_f0007_factslot_identity.py` |
| Commit integration | existing globs for `brain_temporal/commit.py`, `repositories.py`, `brain_api/routes/facts.py`; extend only missing coverage |

G7 authors binding shards under `kg-source/**` and recompiles. Generated YAML is never hand-edited.

## Authorized Review Remediation — run 2026-11-09-81798e61

The operator authorized all seven findings from audits 2026-11-09-7c8e8461 and 2026-11-09-8b8456df. This amendment corrects the existing invariants; it introduces no new producer, route, permission, currency semantics or ontology behavior.

- Backend owns member-key equality, named zero-write rejection, a single 64-character numeric input/canonical bound and preallocation validation. QE tests entity/name/identifier mismatches, normalized equivalents, positive/negative decimal limits, canonical/schema round trips and extreme exponents.
- Backend/DevOps add migration 0013 after immutable0012. Under an ACCESS EXCLUSIVE fact_slot lock, inventory rows for which the complete identity expression is not TRUE; report counts and limited slot IDs only and refuse the migration without changing evidence. Existing malformed identities require explicit governed repair. Replace the CHECK atomically; downgrade restores the exact0012 guard without rewriting rows. QE proves up/down/up, NULL mandatory fields, partial legacy and occupied malformed-data refusal on owned databases.
- Protected reads extend AuthorizationExecution.read with an optional `additional_reads(payload)` callback. Authorize/lock the primary resource, load the selected payload exactly once into private memory, derive the actual payload's scope keys, authorize them under the same current-authority unit of work, recheck all decisions, audit all and commit once before returning. Do not prequery a possibly different answer. Denied scope returns the established non-disclosing denial; legacy values do not gain carrier parsing. QE verifies revocation interleavings and selection/denial behavior at the real facade and HTTP boundary.
- PM reconciles final and inherited post-CI changed-file inventory and removes stale Not Started entry statuses. Architect reconciles bindings for0013 and protected-read semantics. Original approved reports remain history; a new evidence run owns current proofs and fresh reviews.
- Runtime remains the product's CI-equivalent locked engine Python environment plus Compose PostgreSQL; all destructive migration/rollback tests use owned databases. Inspect shared data read-only for rollout readiness; never repair it automatically.

Required remediation roles: Backend Developer, Architect, QE, Code Reviewer, Security Reviewer and DevOps. No frontend or AI behavior changes. Re-review plan readiness and completed/candidate feature after regression evidence. No acceptance of Proposed ADRs is implied.
