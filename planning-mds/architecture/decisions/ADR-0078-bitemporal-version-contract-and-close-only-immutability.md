# ADR-0078: Bitemporal Version Contract and Close-Only Immutability

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-11-16
**Owner:** Architect
**Design review:** F0008 Phase B, plan run `2026-11-16-208a1193`. Approved by the operator token `approve-phase-b` on 2026-11-17, including the D8 end-revision clarification. The ADR stays Proposed.
**Formal acceptance:** requires the PostgreSQL proofs listed under [Proof gates](#proof-gates-before-acceptance), run in the F0008 feature action. Plan approval alone is not runtime acceptance. Feature run `2026-11-17-1a4ae2f0` (2026-11-18) met all six proof gates ([architect review](../../operations/evidence/runs/2026-11-17-1a4ae2f0/architect-implementation-review.md)); acceptance remains an operator decision.
**Refines:**
- [ADR-0007](ADR-0007-full-bitemporality.md) and [ADR-0008](ADR-0008-database-level-temporal-integrity.md), both Accepted. This ADR keeps the two-range exclusion and settles the §109.2 open questions.
- [ADR-0064](ADR-0064-time-interpretation-and-valid-time-precision.md) §5 and §7, Proposed. This ADR implements their F0008 storage share and adopts ADR-0064's recommended representation of an unknown end.
- [ADR-0039](ADR-0039-typed-insurance-values-and-completeness.md), Proposed: supersession of information states.
- [ADR-0077](ADR-0077-factslot-identity-and-typed-answer-carriers.md), Accepted: the database backstop for the envelope that ADR-0077 handed off.

This ADR does not accept ADR-0064 or ADR-0039.

## Context

The F0001 pilot `canonical_fact_version` stores:

- `valid` and `recorded` as `tstzrange` columns under `EXCLUDE USING gist (slot_id WITH =, valid WITH &&, recorded WITH &&)`;
- the four §109.2 timestamps;
- a JSONB value and evidence.

The pilot `CanonicalCommitService` locks the slot, closes the recorded upper bound of every overlapping current version, and inserts split remainders and the new version in one transaction.

Gaps against the master blueprint and ADR-0064:

- Valid-time bounds have no precision or zone.
- `NULL` is the only end state.
- There are no attestation bounds or start basis.
- Remainders take the new proposal's receipt timestamps.
- Nothing stops an UPDATE of a historical payload. §109.2 explicitly asks to "decide whether closing a recorded interval is the only permitted update".
- The ADR-0077 envelope is checked only by the service.

The F0008 G1 decisions (2026-11-16) set the business rules:

1. Store the start basis. A template field or a human date is grade `A`, and grade `C` cannot close.
2. A `PRESENT` value closes only to `PRESENT` or `EXPLICIT_NEGATIVE`.
3. An unknown start with undated evidence is refused.
4. The caller supplies an IANA zone for each bound.

Two Phase B operator decisions apply to reads:

- Before an attestation-floor start, a read is validity-unknown (EX-PC-014-B).
- Information states are exposed by the internal reader. The GET changes only additively, and F0020 keeps HTTP exposure of `NOT_PROCESSED`.

## Decision

### D1. A versioned temporal contract on the existing row; legacy stays legacy

`canonical_fact_version` gains `temporal_contract smallint NULL`:

- `NULL` marks a legacy version, from the pilot or from F0007 before F0008.
- `1` marks `fact-temporal/v1`.

The legacy columns are not backfilled. A `BEFORE INSERT` trigger binds the contract to the slot:

- A row for an identity-v1 slot must carry `temporal_contract = 1`. The one exception is a split remainder (`split_of_version_id` set) whose predecessor is itself legacy; it stays legacy.
- A row for a legacy pilot slot must carry `temporal_contract IS NULL`.

The commit request carries a `temporal` block (`fact-temporal-v1.schema.json#/$defs/commit_temporal`):

- It is required for identity-v1 slots. Without it the request is refused with `temporal_fields_required`.
- It is forbidden alongside the pilot `valid_from`/`valid_to`.

### D2. Per-bound precision and zone

The table adds these columns:

- `valid_from_granularity` and `valid_to_granularity`, each in `YEAR`…`SECOND`;
- `valid_from_zone` and `valid_to_zone`, each an IANA name.

Instants stay in the `valid` range, lower bound inclusive and upper bound exclusive.

A bound is accepted only if `date_trunc(<granularity>, instant, zone) = instant`. `QUARTER` maps to `quarter`. The check runs in two places:

- in the service (Python `zoneinfo`) to return early reason codes (`granularity_invalid`, `time_zone_invalid`, `bound_not_truncated`);
- in the `BEFORE INSERT` trigger, where the zone is checked against `pg_timezone_names` and the PostgreSQL check is authoritative.

The tzdata versions of both runtimes are recorded in the feature run's evidence. Document conventions, for example "12:01 a.m. standard time" mapped to `Etc/GMT+6`, belong to the caller.

### D3. End states, and an unknown end inside the exclusion

`valid_to_state` takes one of three values:

| State | Stored upper bound | End columns |
|---|---|---|
| `OPEN` | `upper_inf(valid)` | NULL |
| `BOUNDED` | The caller's `valid_to` instant | Set |
| `UNKNOWN` | The exclusive end of the `attested_to` period in `attestation_zone`, with granularity equal to `attested_to`'s precision. This follows ADR-0064's recommended option: an unknown end closes the integrity range at its attestation. | Set from `attested_to` |

An `UNKNOWN` version also stores `validity_unknown_from`. Its value is the greater of:

- the exclusive end of the start bound's granularity period;
- the exclusive end of the `attested_through` period, when the version has dated positive evidence.

Valid-time reads in `[validity_unknown_from, upper)` return validity-unknown (D9). If `validity_unknown_from >= upper`, the latest positive evidence postdates the ending document, and the commit is refused with `end_state_invalid`.

The exclusion constraint's DDL is unchanged. EX-SEM-004 and EX-PC-014 follow from these rules.

### D4. Attestation from F0004 date selections, never from clocks

The attestation dates are derived from the evidence:

- **Source of dates:** evidence assertion → content artifact → document version → the current F0004 `document_date_selection`, meaning the highest sequence. If that selection is a clear, the document is undated, as in the F0004 read; an earlier date is never resurrected.
- **Stored form:** each date is stored as `(value varchar(10), precision YEAR|MONTH|DAY)` in `attested_from`, `attested_through` and `attested_to`.
- **`attested_from`:** the earliest period start among the positive evidence.
- **`attested_through`:** the latest period end among the positive evidence.
- **`attested_to`:** the earliest selected date among `ending_evidence_refs`.

If the caller echoes values in `expected_attestation` and they differ from the derived ones, the commit is refused with `attestation_mismatch`.

An unknown start (`valid_from` null) works as follows:

- The start is floored at the start of the `attested_from` period in `attestation_zone`, with granularity equal to that date's precision.
- `valid_from_basis` is set to `ATTESTATION_FLOOR`, which only the server assigns.
- If no evidence document has a selected date, the commit is refused with `start_unattested`.

Upload, receipt, artifact, assertion and acceptance times are never consulted.

The ending evidence joins the existing F0006 same-unit-of-work source READ checks. On read, the attesting document versions join the GET's `additional_reads` (the F0007 SEC-F7-02 pattern). A principal who cannot read them receives the non-disclosing 404 and does not get a redacted answer.

### D5. The §109.2 algorithm with close-only immutability

Inside the existing unit of work and slot lock, the commit service runs these steps:

1. Validate the temporal block (D2–D4) and the F0007 envelope.
2. Load the current versions, those with recorded `upper_inf`.
3. Apply the guards (D8).
4. For each current version whose valid range overlaps the new one:
   - close its recorded interval at `canonical_accepted_at`;
   - insert 0–2 remainders.
5. Insert the new version.
6. Insert the change rows, the commit row, the audit event and the outbox event.

Each remainder:

- copies the predecessor's value, evidence, review linkage, the three source timestamps (`source_received_at`, `artifact_created_at`, `assertion_created_at`), `temporal_kind`, start basis and attestation, and its uncut bound;
- takes the cut bound from the successor's corresponding bound (instant, granularity and zone);
- sets `split_of_version_id`;
- takes the new `canonical_accepted_at`, where its own recorded interval starts.

A BEFORE INSERT trigger added by migration 0015 (remediation run `2026-11-18-bce4909b`) also requires `split_of_version_id` to name a version in the same slot.

A remainder that ends at the successor's start is `BOUNDED`. A remainder after a `BOUNDED` successor keeps the predecessor's end state and attestation, and its `validity_unknown_from` is clipped to its own range. Change rows link each closed version to the new version, with the proposal's reason, and to each of its remainders, with reason `split`.

**Immutability, enforced by the database.** A `BEFORE UPDATE` trigger on `canonical_fact_version` permits exactly one change: setting the finite upper bound of a recorded interval that is currently `upper_inf`. The lower bound must stay the same, the new upper must be greater than it, and every other column must be `IS NOT DISTINCT FROM` its old value. `BEFORE DELETE` and `TRUNCATE` triggers refuse. `canonical_fact_change` is append-only in the same way, and the 0007 owner-immutability triggers stay in place.

**Alternative rejected:** an append-only close-event table from which recorded intervals are derived. A GiST exclusion cannot run over derived ranges, the change would rewrite the pilot reads, and every read would gain a join. The single permitted close is already an append-like monotone transition, and the trigger makes it auditable.

### D6. Concurrency and relationships

- **Lock order.** The existing `SELECT … FOR UPDATE` on `fact_slot` serializes writers per slot (or per member) under READ COMMITTED. The exclusion constraint is the backstop. `23P01` maps to HTTP 409 `temporal_conflict` and a stale `expected_current_version_id` maps to 409 `stale_version`. Neither writes any row, audit or outbox entry.
- **MULTI members.** Members are child slots (ADR-0077 D4), so locks, exclusion and guards apply to each member independently.
- **RELATIONSHIP slots** are versioned in `canonical_fact_version` like any other slot. The `canonical_relationship_version` table named in master blueprint §78 is **not created**; with ADR-0077 RELATIONSHIP slots it is a logical name, and the glossary and data model record this. F0034 projects relationship versions from these rows.

### D7. Envelope backstop

Two checks back the envelope:

- A table CHECK: `temporal_contract IS NULL OR (value->>'answer_contract' = 'fact-answer/v1' AND ((value->>'state') = 'PRESENT') = (value ? 'value'))`.
- In the insert trigger, the same predicate for every row of an identity-v1 slot, legacy remainders included.

Migration preflight refuses the upgrade if an existing identity-v1 version violates the predicate. It reports a count and a limited list of version ids, and it repairs nothing (the 0013 pattern). Scope rules (`NOT_FOUND`/`NOT_STATED`) and money rules stay in the F0007 service validator.

### D8. Guards: start basis and information state

These guards run in the service after the lock and before any effect, against overlapping current versions. They cannot be expressed in the database without cross-row triggers.

- **Start basis.** If the proposal's basis is `MENTION_C` or `ATTESTATION_FLOOR`, any overlap is refused with `succession_start_unanchored`. Every other basis may close. No confidence value is input.
- **End revision is not succession.** A proposal that matches exactly one overlapping current version on all of the following is an end revision:
  - the same canonical answer (value and state);
  - the same start bound (instant, granularity and zone);
  - the same start basis;
  - the same `attested_from`.

  An end revision changes only the end, for example `OPEN` → `UNKNOWN` (EX-PC-014) or `OPEN` → `BOUNDED`. It closes and replaces that version without the start-basis guard, because its start closes nothing. Any other difference makes it a succession, and the guard applies.
- **Information state.** If a predecessor's envelope state is `PRESENT`, the successor's state must be `PRESENT` or `EXPLICIT_NEGATIVE`; otherwise the commit is refused with `state_supersession_refused`. A predecessor that is not `PRESENT` may be closed by any state.

Each refusal is audited as a commit refusal and writes no fact row. F0018 later routes refusals to review and adds §54 source authority.

*Feature G0 note (run `2026-11-17-1a4ae2f0`, 2026-11-17):* the refusal is audited through the existing F0002 durable decision, with `operation_outcome = failed`, and its reason code is returned as the 422 problem `code`. The AuthX decision record has no business-reason field, so durable persistence of the reason code per refusal moves to F0018 together with review routing.

### D9. Reads

`TemporalFactReader.resolve(slot, valid_at t, known_at k)` resolves in this order:

1. If a version has `valid @> t` and `recorded @> k`:
   - if it is `UNKNOWN` and `t >= validity_unknown_from`, return `VALIDITY_UNKNOWN(UNKNOWN_END_WINDOW)`;
   - otherwise return the version.
2. If no version contains `t`, take the version visible at `k` with the smallest `lower(valid) > t`. If its basis is `ATTESTATION_FLOOR`, return `VALIDITY_UNKNOWN(BEFORE_ATTESTATION_FLOOR)`.
3. Otherwise, for an identity-v1 slot, return `NOT_PROCESSED`. For a legacy slot, return none.

On the existing `GET /facts/{factSlotId}`:

- `FactVersion` gains an optional `temporal` block.
- `FactValidityUnknown` is an additive 200 variant for identity-v1 slots. It carries no value.
- A coordinate with no version keeps the pilot 404.

Authorization always uses current grants (ADR-0053).

### D10. Temporal kind is reserved, not activated

`temporal_kind` is `STATE`, `EVENT` or `ETERNAL`, and is `NOT NULL` for v1 rows. CHECK constraints reserve the shapes:

- `EVENT`: `BOUNDED`, one granularity period.
- `ETERNAL`: valid `(,)` with the bound columns NULL. This is the only case in which an infinite lower bound is allowed.

F0008 writes `STATE` only. F0012/F0013 predicate contracts activate the other kinds without DDL.

## Alternatives Considered

| Alternative | Why not |
|---|---|
| Store `UNKNOWN` ends as `upper_inf` with a state flag | The exclusion would treat an ended fact as current and block a legitimate successor. Reads would have to special-case every query. |
| UTC-only truncation | A Chicago-midnight effective date lands on the previous UTC day (G1 decision 4). |
| Close-event table with derived recorded intervals | No GiST exclusion over derived ranges; pilot reads rewritten (D5). |
| Separate `canonical_relationship_version` table | Duplicates the exclusion and the guards. ADR-0077 RELATIONSHIP slots already carry the object in their identity. |
| Redact attestation dates the reader cannot see | A partial answer could reveal that restricted evidence exists. F0007 chose whole-read denial (SEC-F7-02). |
| Database-enforced guards | Cross-row triggers on every insert duplicate the service logic under the same lock and add little. The structural invariants (D2, D3, D5, D7) are what the database enforces. |

## Consequences

- **F0009**: provenance lineage reads the remainder `split_of_version_id` and the change rows.
- **F0010**: owns the change-reason vocabulary; F0008 keeps the existing seven values.
- **F0016**: sends `MENTION_A/B/C` bases and document time context.
- **F0018**: routes refusals to review and adds source authority. No new table needs RLS; `canonical_fact_version` and `canonical_fact_change` are already in the inventory.
- **F0019 and F0025**: use `TEMPLATE_FIELD`.
- **F0020**: exposes states over HTTP.
- **F0022**: supplies the human date selections that unlock attestation.
- **F0012/F0013**: activate `temporal_kind`.
- **Commit cost**: one indexed lookup per evidence document for its current date selection, and a trigger per inserted version row. §114.2 budgets are measured later.
- **Trade-offs**:
  - Guards are service-enforced (D8).
  - The tzdata versions of PostgreSQL and Python can drift; the database is authoritative, and the run records both.
  - Legacy versions on identity-v1 slots get no temporal fields until superseded.

## Proof Gates Before Acceptance

All of these run on PostgreSQL 18 in the F0008 feature action.

1. **§115.4 bitemporal proof under v1:**
   - retroactive endorsement, then correction;
   - a race of eight or more concurrent commits, checked on a coordinate grid;
   - distinct received and accepted times;
   - remainder lineage.
2. **Immutability negatives:** UPDATE of every non-recorded column, reopening a closed recorded interval, DELETE and TRUNCATE are all refused. The single permitted close succeeds.
3. **Zone and precision fixtures:** every granularity, a DST transition, and `Etc/GMT+6`. Both tzdata versions are recorded.
4. **EX-SEM-004 and EX-PC-014 A–D reads:** unknown-end windows and the before-floor validity-unknown.
5. **Envelope backstop and guards:** direct-insert negatives, the basis and state refusals, and per-member independence.
6. **Migration:** the pilot and F0007 snapshot is byte-identical across upgrade, downgrade and upgrade, and the downgrade guard reports blocking rows.

## References

- Master blueprint §§14, 15, 16, 78, 87, 107.4, 109.2, 115.4.
- [F0008 assembly plan](../../features/archive/F0008-bitemporal-canonical-facts/feature-assembly-plan.md).
- [`fact-temporal-v1.schema.json`](../../schemas/fact-temporal-v1.schema.json).
- Examples: [EX-SEM-003/004](../../examples/statements-time-and-governance.md#time-interpretation), [EX-PC-006/014](../../examples/commercial-pc-account/cases.md#ex-pc-014--unknown-start-and-unknown-end).
