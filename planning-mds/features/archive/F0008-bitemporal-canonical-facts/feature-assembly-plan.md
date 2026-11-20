# Feature Assembly Plan — F0008: Bitemporal canonical facts

**Status:** Phase B design, approved by the operator at plan G5 on 2026-11-17 (`approve-phase-b`).
**Plan run:** `2026-11-16-208a1193` (A+B, new)
**Governing decisions:**
- Accepted: ADR-0007, ADR-0008, ADR-0077.
- Proposed with this plan: [ADR-0078](../../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md).
- Proposed, not accepted by this feature: ADR-0064 §5/§7 and ADR-0039 state supersession.

**Contracts:**
- New: [`fact-temporal-v1.schema.json`](../../../schemas/fact-temporal-v1.schema.json).
- Additive changes: [`canonical-commit-request.schema.json`](../../../schemas/canonical-commit-request.schema.json) gains a `temporal` block, and [`brain-api.yaml`](../../../api/brain-api.yaml) 0.5.0 gains the `FactVersion.temporal` block, the `FactValidityUnknown` variant and new reason codes.

## Overview and Scope

F0008 turns the F0001 bitemporal pilot into the canonical version contract for F0007 identity-v1 slots. The work covers:

- per-bound precision and zone;
- the `OPEN`/`BOUNDED`/`UNKNOWN` end states, with attestation bounds derived from F0004 date selections;
- the start basis and the two succession guards;
- close-only immutability, enforced by the database;
- remainder lineage;
- the envelope backstop;
- a two-coordinate reader that returns validity-unknown.

It adds no route, grant, UI, producer or model call. It covers seven stories and 46 ACs.

**Operator decisions in force:**

- G1 (2026-11-16):
  - store the start basis; a template field or human date is grade `A`, and grade `C` cannot close;
  - a `PRESENT` value closes only to `PRESENT` or `EXPLICIT_NEGATIVE`;
  - `START_UNATTESTED`;
  - the caller supplies the IANA zone.
- Phase B (2026-11-16):
  - before an attestation floor, a read is validity-unknown;
  - the internal reader exposes states; the GET changes are additive, and a no-version coordinate stays 404.

**Phase B clarification approved at G5 (2026-11-17):** an end revision is not a succession (ADR-0078 D8; S0005 AC3 note).

## Existing Code and Reconciliation

| Existing | Location | F0008 change |
|---|---|---|
| `canonical_fact_version`, two-range GiST exclusion | `engine/migrations/versions/0003_fact_slots_and_commits.py` | Kept. New columns, CHECKs and triggers in 0014. The exclusion DDL is unchanged. |
| Ownership composite keys, owner immutability | 0006, 0007 | Kept. The new triggers sit alongside them. |
| `TimeRange`, `split_remainder` | `engine/packages/brain-temporal/src/brain_temporal/ranges.py` | Extended to bounds with granularity and zone. `split_remainder` is kept for legacy rows. |
| `CanonicalCommitService.commit` | `brain_temporal/commit.py` | Branches on the slot's temporal contract. The v1 path validates, applies guards, writes remainders with predecessor lineage and records change rows to remainders. **Pilot defect fixed for v1 and legacy:** remainders take the predecessor's three source timestamps (`source_received_at`, `artifact_created_at`, `assertion_created_at`), not the proposal's, and the new `canonical_accepted_at` (S0003 AC3). |
| `FactCommitRepository` and `SqlAlchemyFactCommitRepository` | `brain_persistence/repositories.py` | `insert_version` takes a `VersionTemporal`. New methods: `evidence_document_dates`, `slot_temporal_contract`, `versions_visible_at`. `close_recorded` is unchanged and is the only UPDATE. |
| `resolve_at` | `brain_persistence/repositories.py` | Kept for the pilot. The new `TemporalFactReader` in `brain_temporal/reader.py` implements ADR-0078 D9. |
| `GET /facts/{id}`, `POST /facts/{id}/commits` | `engine/apps/api/src/brain_api/routes/facts.py`, `schemas/facts.py` | Additive `temporal` input and output. `FactValidityUnknown` variant. Exception mapping for the new 422 codes and 409 `temporal_conflict`. |
| F0007 `FactAnswerPolicy` | `brain_factslots` | Unchanged. It still validates and canonicalizes the envelope before the temporal checks. |
| F0004 date selection | `document_date_selection` | Read only, as the current selection per document version. |

## Build Order and Exact File Handoffs

Every step is backend-developer work unless marked otherwise. Tests use real PostgreSQL 18 (`brain-postgres:18-pgvector-age`).

| Step | Story | Work | Files (proposed) |
|---|---|---|---|
| 1 | S0007, S0003, S0004 | Migration 0014: columns, CHECKs, insert/update/delete/truncate triggers, preflight, guarded downgrade | `engine/migrations/versions/0014_f0008_bitemporal_contract.py` |
| 2 | S0001, S0002 | Domain types `Granularity`, `Bound`, `EndState`, `StartBasis`, `DocumentDate`, `VersionTemporal`, `TemporalProposal`, reason codes; zone/truncation validator | `brain_domain/temporal.py`, `brain_temporal/bounds.py` |
| 3 | S0002 | Attestation derivation from evidence → document version → current date selection; floor and unknown-end placement | `brain_temporal/attestation.py`, `brain_persistence/repositories.py` (`evidence_document_dates`) |
| 4 | S0003, S0005 | v1 commit path: guards, end revision, remainders with lineage, change rows to remainders; legacy path timestamp fix | `brain_temporal/commit.py`, `brain_temporal/ranges.py` |
| 5 | S0006 | `TemporalFactReader` resolution order (D9) | `brain_temporal/reader.py` |
| 6 | S0001, S0002, S0006, S0007 | API models and route mapping; attestation documents added to GET `additional_reads` | `brain_api/schemas/facts.py`, `brain_api/routes/facts.py`, `brain_api/errors.py` |
| 7 | All | Contract examples check against the schemas | `engine/packages/brain-temporal/tests/test_contract_examples.py` (reads `planning-mds/features/F0008-*/contract-examples.json`) |
| 8 | All | Tests (see the validation matrix) | `engine/packages/brain-temporal/tests/test_bounds.py`, `engine/tests/integration/test_temporal_v1_commit.py`, `test_temporal_immutability.py`, `test_temporal_concurrency.py`, `test_temporal_reads.py`, `test_temporal_migration.py` |

## Contracts and Signatures

These signatures are a design, not code (Python 3.13, frozen dataclasses).

```python
# brain_domain/temporal.py
class Granularity(StrEnum): YEAR, QUARTER, MONTH, DAY, HOUR, MINUTE, SECOND
class EndState(StrEnum): OPEN, BOUNDED, UNKNOWN
class StartBasis(StrEnum): TEMPLATE_FIELD, HUMAN, MENTION_A, MENTION_B, MENTION_C, ATTESTATION_FLOOR
class TemporalKind(StrEnum): STATE, EVENT, ETERNAL

@dataclass(frozen=True, slots=True)
class Bound: instant: datetime; granularity: Granularity; zone: str

@dataclass(frozen=True, slots=True)
class DocumentDate: value: str; precision: Literal["YEAR", "MONTH", "DAY"]
    # period_start(zone) -> datetime ; period_end(zone) -> datetime  (exclusive)

@dataclass(frozen=True, slots=True)
class TemporalProposal:            # parsed fact-temporal/v1 commit block
    valid_from: Bound | None; valid_from_basis: StartBasis | None
    valid_to_state: EndState; valid_to: Bound | None
    attestation_zone: str | None; ending_evidence_refs: tuple[UUID, ...]
    expected_attestation: ExpectedAttestation | None

@dataclass(frozen=True, slots=True)
class VersionTemporal:             # stored per v1 row
    kind: TemporalKind; valid_from: Bound | None; valid_from_basis: StartBasis | None
    valid_to_state: EndState; valid_to: Bound | None
    attested_from: DocumentDate | None; attested_through: DocumentDate | None
    attested_to: DocumentDate | None; validity_unknown_from: datetime | None
    split_of_version_id: UUID | None

class TemporalRejected(Exception): code: TemporalReason   # 10 reason codes below

# brain_temporal/reader.py
@dataclass(frozen=True, slots=True)
class Resolved: version: FactVersion
@dataclass(frozen=True, slots=True)
class ValidityUnknown: version_id: UUID; reason: Literal["UNKNOWN_END_WINDOW", "BEFORE_ATTESTATION_FLOOR"]; temporal: VersionTemporal
@dataclass(frozen=True, slots=True)
class NotProcessed: pass
Resolution = Resolved | ValidityUnknown | NotProcessed | None   # None: legacy slot, no version

class TemporalFactReader:
    async def resolve(self, slot_id: UUID, *, valid_at: datetime, known_at: datetime) -> Resolution: ...
```

**Reason codes.** The wire forms are lowercase and returned as 422 problem `code` with no detail text. The stories use the uppercase forms.

| Code | Story |
|---|---|
| `temporal_fields_required` | S0007 AC3 |
| `granularity_invalid` | S0001 AC1 |
| `time_zone_invalid` | S0001 AC1 |
| `bound_not_truncated` | S0001 AC2 |
| `end_state_invalid` | S0002 AC1 |
| `start_unattested` | S0002 AC5 |
| `attestation_mismatch` | S0002 AC6 |
| `start_basis_invalid` | S0005 AC1 |
| `succession_start_unanchored` | S0005 AC3 |
| `state_supersession_refused` | S0005 AC5 |

There are two 409 conflicts: `temporal_conflict` (exclusion `23P01`) and the existing `stale_version`.

**Where the request schema can't check it.** JSON Schema checks structure only. These checks run in the service:

- the zone exists and the bound is truncated;
- the BOUNDED end comes after the start;
- the echoed attestation matches the derived values;
- a pilot-shaped request was sent to an identity-v1 slot.

The service checks run after F0002 authorization and after the F0007 envelope validation, and before any effect.

## Data Model and Database Integrity

### Migration `0014_f0008_bitemporal_contract.py`

0014 is the next free revision after 0013. The F0011 lane runs in parallel; whichever feature merges second rebases its `down_revision` and revision number before merge.

```sql
ALTER TABLE canonical_fact_version
  ADD COLUMN temporal_contract smallint NULL CHECK (temporal_contract IS NULL OR temporal_contract = 1),
  ADD COLUMN temporal_kind text NULL CHECK (temporal_kind IN ('STATE','EVENT','ETERNAL')),
  ADD COLUMN valid_from_granularity text NULL, ADD COLUMN valid_from_zone text NULL,
  ADD COLUMN valid_from_basis text NULL CHECK (valid_from_basis IN
      ('TEMPLATE_FIELD','HUMAN','MENTION_A','MENTION_B','MENTION_C','ATTESTATION_FLOOR')),
  ADD COLUMN valid_to_state text NULL CHECK (valid_to_state IN ('OPEN','BOUNDED','UNKNOWN')),
  ADD COLUMN valid_to_granularity text NULL, ADD COLUMN valid_to_zone text NULL,
  ADD COLUMN attested_from_value varchar(10) NULL, ADD COLUMN attested_from_precision text NULL,
  ADD COLUMN attested_through_value varchar(10) NULL, ADD COLUMN attested_through_precision text NULL,
  ADD COLUMN attested_to_value varchar(10) NULL, ADD COLUMN attested_to_precision text NULL,
  ADD COLUMN validity_unknown_from timestamptz NULL,
  ADD COLUMN split_of_version_id uuid NULL;
-- composite self-FK keeps ownership: (split_of_version_id, tenant_id, knowledge_base_id)
--   -> canonical_fact_version (id, tenant_id, knowledge_base_id)
-- granularity CHECKs: IN ('YEAR','QUARTER','MONTH','DAY','HOUR','MINUTE','SECOND')
-- precision CHECKs: IN ('YEAR','MONTH','DAY'); value pairs both-null-or-both-set
CHECK ( temporal_contract IS NULL AND temporal_kind IS NULL AND valid_to_state IS NULL
        AND valid_from_basis IS NULL /* …all v1 columns NULL… */
     OR temporal_contract = 1 AND temporal_kind IS NOT NULL AND valid_to_state IS NOT NULL )
CHECK ( temporal_contract IS NULL OR temporal_kind = 'ETERNAL'
        OR (NOT lower_inf(valid) AND valid_from_granularity IS NOT NULL
            AND valid_from_zone IS NOT NULL AND valid_from_basis IS NOT NULL) )        -- never widen a start
CHECK ( temporal_contract IS NULL OR temporal_kind = 'ETERNAL'
        OR (valid_to_state = 'OPEN'    AND upper_inf(valid) AND valid_to_granularity IS NULL)
        OR (valid_to_state = 'BOUNDED' AND NOT upper_inf(valid) AND valid_to_granularity IS NOT NULL
                                       AND attested_to_value IS NULL)
        OR (valid_to_state = 'UNKNOWN' AND NOT upper_inf(valid) AND attested_to_value IS NOT NULL
            AND validity_unknown_from IS NOT NULL AND validity_unknown_from < upper(valid)) )
CHECK ( valid_from_basis IS DISTINCT FROM 'ATTESTATION_FLOOR' OR attested_from_value IS NOT NULL )
CHECK ( temporal_contract IS NULL OR (value->>'answer_contract' = 'fact-answer/v1'
        AND ((value->>'state') = 'PRESENT') = (value ? 'value')) )                      -- D7
```

**Triggers.** All are `SECURITY INVOKER`, are owned by the migration role, and use `search_path`-pinned function names.

- `canonical_fact_version_v1_insert` (BEFORE INSERT):
  - binds the temporal contract to the slot's `identity_version` (D1);
  - applies the envelope predicate to every row of an identity-v1 slot;
  - checks that each zone exists in `pg_timezone_names`;
  - checks `date_trunc(lower(gran), bound, zone) = bound` for each non-infinite bound (D2).
- `canonical_fact_version_close_only` (BEFORE UPDATE): permits only a single close of an open recorded upper bound. Any other change raises `restrict_violation` with message `canonical_fact_version is close-only` (D5).
- `canonical_fact_version_no_delete` (BEFORE DELETE) and `canonical_fact_version_no_truncate` (BEFORE TRUNCATE, statement level): both refuse.
- `canonical_fact_change_append_only`: BEFORE UPDATE, DELETE and TRUNCATE all refuse.

**Preflight (upgrade):**

- Lock `canonical_fact_version` in SHARE ROW EXCLUSIVE mode.
- Refuse the upgrade if any version of an identity-v1 slot fails the envelope predicate, reporting a count and the first 10 ids. Nothing is repaired.
- Snapshot nothing in SQL; the feature tests take the snapshot.

**Downgrade:**

- Refuse when any row has `temporal_contract = 1` or a non-null `split_of_version_id`. The refusal reports a count and ids.
- Otherwise drop the triggers, functions, CHECKs, the self-FK and the columns, in reverse order.
- The legacy pilot behaviour is restored exactly, and no row is rewritten.

### Indexes

`(slot_id, lower(valid)) WHERE temporal_contract = 1` supports the D9 "nearest later version" lookup. The GiST exclusion index already serves point lookups.

### Row-level security

There are no new tables. `canonical_fact_version` and `canonical_fact_change` are already in the F0018 RLS inventory. The new triggers must run under the application role that F0018 introduces.

## Commit Algorithm (v1 path)

Inside the unit of work run by `AuthorizationExecution.mutate`:

1. **Lock and branch.** Lock the slot, and confirm it is in the authorized scope. If the slot is legacy, run the pilot path with the remainder timestamp fix and stop.
2. **Contract checks.** Refuse a pilot-shaped request with `temporal_fields_required`. Run the F0007 `FactAnswerPolicy`, which canonicalizes the envelope.
3. **Parse and validate bounds.** Parse the `temporal` block, then validate granularity, zone and truncation (S0001).
4. **Source checks.** Run `require_commit_sources` over `evidence_refs ∪ ending_evidence_refs`. This is the existing same-UoW READ check.
5. **Derive attestation.** Read the current date selections. Compute `attested_from` and `attested_through` from the positive evidence and `attested_to` from the ending evidence. Compare them with any echoed values (S0002 AC6).
6. **Place an unknown start.** For an unknown start, floor it at `attested_from` with basis `ATTESTATION_FLOOR`, or refuse with `start_unattested`.
7. **Place an unknown end.** For an `UNKNOWN` end, set the upper bound at the end of the `attested_to` period and compute `validity_unknown_from`. If the window is empty, refuse with `end_state_invalid`.
8. **Load current versions.** Check `expected_current_version_id`, which may refuse with `stale_version`.
9. **Guards (D8).**
   - For each overlapping current version, classify the proposal as an end revision or a succession.
   - Apply the start-basis guard to successions only.
   - Apply the state guard to every overlap.
   - A refusal writes a commit-refusal audit event and no other row.
10. **Write.** Register the commit. For each overlapping version:
    - close its recorded interval at `now`;
    - insert its remainders, with predecessor lineage and the successor's cut bound;
    - insert a change row (predecessor → remainder, `split`).
    Then insert the new version, insert a change row (predecessor → new, with the proposal's reason or `superseded`), and write the outbox event.
11. **Return.** Return the `commit_id`, all version ids and `canonical_accepted_at`.

**Exclusion conflict.** A `23P01` violation from step 10 rolls back the whole unit of work, and the API returns 409 `temporal_conflict`.

## Read Algorithm

`TemporalFactReader` implements ADR-0078 D9. Given the request:

1. `GET` resolves `validAsOf` and `knownAsOf`, defaulting each to now.
2. The reader returns `Resolution`.
3. The route maps the result:

| Resolution | HTTP response |
|---|---|
| `Resolved` | 200 `FactVersion` (+`temporal`) |
| `ValidityUnknown` | 200 `FactValidityUnknown` (identity-v1 slots only) |
| `NotProcessed` or `None` | 404 (unchanged) |

Authorization uses current grants. `additional_reads` covers the payload scope (F0007) and the document versions behind the attestation dates. Half-open semantics: the read at `lower` returns the version, and the read at `upper` returns the next result.

## Worked Examples

`contract-examples.json` holds the schema cases. The runtime fixtures are:

- **§87 and S0003 AC1.** $2M, then a $5M endorsement effective 2026-06-01 `DAY` `America/Chicago`, basis `TEMPLATE_FIELD`, received 2026-06-12, accepted 2026-06-14. The grid reads $2M, $5M, $2M and $5M. A correction to 2026-06-03 adds remainders that carry the original timestamps.
- **EX-SEM-004.** The prior carrier is attested by a document dated 2026-06-01 (`DAY`), so `attested_through` = 2026-06-01. The end revision to `UNKNOWN` has ending evidence dated 2026-08-02, with zone `America/Chicago`:
  - upper bound = 2026-08-03T00:00 CDT;
  - `validity_unknown_from` = 2026-06-02T00:00 CDT.
  The fact reads `UNKNOWN` at 07-15 and as the carrier at 05-15.
- **EX-PC-014.** The yard fact has a null start and is floored at 2025-12-15. It reads `BEFORE_ATTESTATION_FLOOR` in March 2025. The end revision to `UNKNOWN` uses the 2026-05-15 broker request:
  - (014-A) March 2026, known April 1: the open version;
  - (014-C) March 2026, known July 11: `UNKNOWN_END_WINDOW`;
  - (014-D) July 2026, known July 11: absent (`NotProcessed`, 404).
- **EX-OWN-003.** `NOT_PROCESSED` → `NOT_STATED` → `EXPLICIT_NEGATIVE` supersede one another in turn. `NOT_FOUND` against a $5M `PRESENT` value is refused.
- **EX-SEM-003.** `MINUTE`, `Etc/GMT+6`, 2026-07-01T06:01Z, round-trips exactly.

## Validation Matrix and Completion Gates

| Story | Tests (proposed) | ACs |
|---|---|---|
| S0001 | `test_bounds.py` (unit: every granularity, DST spring/fall in `America/Chicago`, `Etc/GMT+6`, unknown zone), `test_temporal_v1_commit.py::bounds_*` (PostgreSQL trigger agrees) | AC1–AC6 |
| S0002 | `test_temporal_v1_commit.py::attestation_*`, `test_temporal_reads.py::ex_sem_004`, `::ex_pc_014_*` | AC1–AC7 |
| S0003 | `test_temporal_v1_commit.py::retroactive_*`, `::correction_*`, `::remainder_lineage`, `test_temporal_immutability.py` (every column, reopen, delete, truncate), fault injection before the outbox | AC1–AC7 |
| S0004 | `test_temporal_concurrency.py` (8–16 tasks, grid of at least 200 coordinates), direct-insert overlap and envelope negatives, member independence, cross-scope rows | AC1–AC6 |
| S0005 | `test_temporal_v1_commit.py::guard_*` (each basis, end revision, each state pair, member isolation) | AC1–AC7 |
| S0006 | `test_temporal_reads.py` (§87 grid, half-open, validity-unknown variants, revoked grant), API tests in `engine/apps/api/tests/test_facts.py` | AC1–AC7 |
| S0007 | `test_temporal_migration.py` (snapshot of pilot plus F0007 v1 rows, upgrade/downgrade/upgrade, downgrade refusal), existing `test_bitemporal_commit.py` and F0007 suites unchanged | AC1–AC6 |

**Completion gates:**

- All 46 ACs have observed evidence.
- Changed-code coverage is at least 80%.
- The full engine suite passes.
- `ruff` and `mypy` are clean.
- Migration up/down/up is logged.
- The tzdata versions of PostgreSQL and Python are recorded.
- The ADR-0078 proof gates are mapped to the tests.

```bash
# cwd: engine
uv run pytest packages/brain-temporal/tests tests/integration/test_temporal_*.py apps/api/tests/test_facts.py
uv run pytest            # full engine regression
uv run alembic -c migrations/alembic.ini upgrade head && uv run alembic -c migrations/alembic.ini downgrade 0013 && uv run alembic -c migrations/alembic.ini upgrade head
```

## Required Roles

| Role | Why |
|---|---|
| Quality Engineer | 46 ACs; concurrency grid, zone and DST fixtures, immutability negatives |
| Code Reviewer | Commit-service rewrite of the v1 path, the migration, new domain types |
| Security Reviewer | Attestation-date disclosure (T-08), immutability triggers under app roles, refusal non-disclosure, revoked-grant historical reads |
| DevOps | Migration 0014 up/down/up on seeded data; revision coordination with F0011 |
| Architect | ADR-0078 proof gates; KG reconciliation at G7 |

## Rollout, Rollback and Caching

- No feature flag is needed. Identity-v1 slots have no producer in v0.1 until F0018 and F0019, so the v1 path is exercised by tests and internal callers only.
- **Rollback:** a downgrade is possible only while no v1 rows exist. Once they exist, roll forward.
- **Caching:** none. The reads are point lookups under current authorization.

## Dependencies, Future Handoffs and Approval

- **Delivered dependencies:** F0001 (pilot), F0002, F0003, F0004 and F0007. Their evidence references are in the plan run's `artifact-trace.md`.
- **Handoffs:**
  - F0009: lineage through `split_of_version_id` and change rows.
  - F0010: change-reason vocabulary.
  - F0016: `MENTION_*` bases and time context.
  - F0018: review routing for refusals, source authority, and RLS for the existing tables under the new triggers.
  - F0019 and F0025: endorsements with `TEMPLATE_FIELD`.
  - F0020: HTTP information states and range queries.
  - F0022: date selections that unlock attestation.
  - F0012/F0013: activate `temporal_kind`.
- **Approval:** operator token `approve-phase-b` at plan G5. Implementation runs in the F0008 feature action, whose G0 consumes this plan.

## Feature-Action G0 Reconciliation (run `2026-11-17-1a4ae2f0`, 2026-11-17)

The Architect recorded these implementation details at feature G0. None changes a reason code, schema field meaning, route, grant or story outcome.

1. **Owned test databases.** The new F0008 integration suites use the F0006/F0007 owned-database harness (`BRAIN_MIGRATION_ADMIN_URL`, one database per test, migrated to head). They never touch the shared development database.
2. **Shared-database cleanup.** Three existing cleanup fixtures `TRUNCATE canonical_fact_version` and `canonical_fact_change`, which the new D5 truncate triggers refuse. Those fixtures now run `SET LOCAL session_replication_role = replica` before the truncate. Only a superuser can set it, so the application role cannot use it. Test bodies are unchanged.
3. **F0007 harness request shape (S0007 AC3 vs AC5).** AC3 refuses a pilot-shaped request to an identity-v1 slot, and the F0007 harness `commit` helper sends exactly that shape. The helper now sends a `fact-temporal/v1` block (a `DAY`/`UTC` start with basis `TEMPLATE_FIELD`, end `OPEN`). F0007 test bodies and expectations stay unchanged. AC5 is read as "behaviour unchanged", since the literal reading contradicts AC3. This is logged as a `plan-story-reconcile` decision.
4. **Trigger names and firing order.** PostgreSQL fires BEFORE triggers in name order. The new triggers are named `trg_canonical_fact_version_v1_insert`, `trg_canonical_fact_version_v1_close_only`, `trg_canonical_fact_version_v1_no_delete`, `trg_canonical_fact_version_v1_no_truncate`, `trg_canonical_fact_change_v1_append_only` and `trg_canonical_fact_change_v1_no_truncate` (a row trigger and a statement trigger cannot share one definition), so the 0007 `..._owner_immutable` trigger still fires first and existing ownership negatives keep their error. The functions are `brain_cfv_v1_insert_guard()`, `brain_cfv_close_only()` and `brain_refuse_mutation()`.
5. **Refusal audit (D8).** A guard or temporal refusal raises inside the `mutate` operation. The existing F0002 path rolls back and durably records the commit decision with `operation_outcome = failed`, which is the same mechanism as F0007 answer rejections. The reason code is returned as the 422 problem `code`. The AuthX decision record has no field for a business reason, and adding one would change the F0002 AuthX contract. Durable per-refusal reason persistence therefore moves to F0018, which routes refusals to review. ADR-0078 D8 gets a note to this effect.
6. **Read timestamps (S0006 AC5).** `FactVersion` gains optional `review_decision_id`, `source_received_at`, `artifact_created_at` and `assertion_created_at`, and the optional `temporal` block. `brain-api.yaml` `FactVersion` lists the four as optional properties. The runtime pilot field names (`valid_start`, `valid_end`, `recorded_start`, `recorded_end`) are kept. The existing contract drift, where `brain-api.yaml` describes `valid`/`recorded` objects, predates F0008 and is out of scope; it is logged as a follow-up.
7. **Remainder review linkage (S0003 AC3).** The pilot wrote `review_decision_id = NULL` on remainders. Both the v1 and legacy paths now copy the predecessor's `review_decision_id`, together with its three source timestamps; `canonical_accepted_at` is the new acceptance.
8. **Fault injection (S0003 AC7).** The test wraps the repository so `write_outbox` raises after the fact rows are flushed, then counts rows from that commit in every table.
9. **Migration lineage.** The sole head is `0013`, and no remote branch carries a `0014` (F0011 is still Planned). `0014_f0008_bitemporal_contract.py` takes `down_revision = "0013"`.
10. **CI.** A new `ci-gates.yml` step runs the F0008 suites against owned databases with a coverage floor on `brain_temporal`.

## Review Remediation (run `2026-11-18-bce4909b`, 2026-11-18)

Independent feature review `2026-11-18-d34a095e` returned NOT DONE, and closeout audit `2026-11-18-a3709ba0` raised overlapping findings. The operator authorized targeted remediation on 2026-11-18 and made three decisions:

| Finding | Decision | Change |
|---|---|---|
| CR-F8-01 (Critical): the commit response lacked S0002 AC7 metadata | Implement in the response | `CommitResult.version_temporals`; `CommitResponseOut.versions[]` with each written version's `temporal` block in `fact_version_ids` order; `canonical-commit-response.schema.json` gains optional `versions`; S0007 AC6 amended to admit additive commit-response fields. A legacy pilot response is unchanged. |
| QE-M1: S0004 AC1 said losers write "no audit row" | Amend the AC, keep the F0002 audit | AC1 now says losers write no fact, change, commit or outbox row and no successful commit audit, and that the `failed` authorization decision is recorded. The test asserts the failed count equals the losers. |
| FR-ARCH-L2: the lineage FK lacked a same-slot binding | Fix now | Migration `0015_f0008_split_lineage_same_slot.py`: a BEFORE INSERT trigger requires the split predecessor to be in the same slot, with a preflight that refuses existing crossings. F0011 renumbers after 0015. |

Also in this run:

- FR-ARCH-M1: a legacy read omits `temporal` instead of returning `null`.
- FR-ARCH-L1: the ADR-0078 D4/D5 prose now matches the clear semantics and the three copied source timestamps.
- PM-M1: the F0018 handoffs are recorded in F0018's README and KG shard, and S0005 notes the deferral.
- The prior run's evidence labels (PM-L1, PM-L2, SEC-L1, QE-L1) are corrected through errata in this run. The superseded evidence is not rewritten.

No route, grant, table or UI is added.

## Second Remediation (run `2026-11-19-8cfcd0ff`, 2026-11-19)

Review `2026-11-19-b21ec2de` found SEC-F8-NEW-01 (High). Remainders repeat their predecessor's attestation dates, and the new commit response returns them, but no READ check covered the predecessor's documents. Operator decision (2026-11-19): refuse the whole commit with the non-disclosing 404.

- **Up front:** the commit route adds, to the same-UoW READ checks, the documents behind the dates of every current temporal-v1 version that the proposal could split (`current_attesting_artifact_keys`, over a conservative valid-time window). An unreadable one denies the commit (404) before any effect.
- **After the slot lock:** the service passes the predecessors whose dates the response would return to a `disclosure_check`. A document that escaped the up-front check (a version committed concurrently in between) refuses the commit with the retryable 409 `stale_version`.
- **Lows:** the plan and docstring wording on remainder timestamps (R2-ARCH-L1); the STATUS and BLUEPRINT pointers (PM2-L2); NUL-safe changed-path inventory (PM2-L1); runtime preflight recorded before the regression (QE2-L1).

## Knowledge-Graph Binding Plan

The Architect owns this plan. G4 compiles it.

- **Feature shard `kg-source/features/F0008.yaml`:**
  - remove `coverage_excluded`;
  - set `affects`: `capability:bitemporal-canonical-commit`, `capability:temporal-fact-resolution` (new), `entity:canonical-fact-version`, `endpoint:fact-commit`, `endpoint:fact-get`;
  - set `governed_by`: ADR-0007, ADR-0008, ADR-0064, ADR-0039, ADR-0077, ADR-0078;
  - set `uses_schema`: `fact-temporal-v1` (new), `canonical-commit-request`, `canonical-commit-response`, `fact-answer-v1`, `problem-details`;
  - set `uses_api_contract`: `api:brain-api`;
  - add seven `story_mappings`.
- **Node shards:**
  - a new capability `temporal-fact-resolution`;
  - an updated `bitemporal-canonical-commit` note;
  - an `adr:0078` entry;
  - a `schema:fact-temporal-v1` entry;
  - updated `entity:canonical-fact-version` notes.
- **Bindings `kg-source/bindings/f0008-planning.yaml`:** architecture and schema paths only. Code paths are bound at feature G7.
