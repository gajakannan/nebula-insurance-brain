# F0008 — Bitemporal canonical facts

**Feature ID:** F0008
**Feature Name:** Bitemporal canonical facts
**Priority:** Critical
**Phase:** MVP — v0.1A
**Status:** Planned — Phase A approved 2026-11-16 (`approve-phase-a`); Phase B approved 2026-11-17 (`approve-phase-b`)
**Plan Run:** `2026-11-16-208a1193` (A+B, new)

## Feature Statement

**As a** persistence engineer, business reviewer and GL underwriter
**I want** every canonical fact version to record when it held in the business world and when the Brain accepted it, at a stated precision, with an end that can be open, bounded or unknown
**So that** "what was true on June 5" and "what did the Brain know on June 5" each have exactly one answer, retroactive endorsements and corrections never erase earlier beliefs, and an unknown end is never read as "still holds".

## Business Objective

- **Goal:** turn the F0001 bitemporal pilot into the full canonical version contract. It covers ADR-0007 and ADR-0008 over the F0007 slot identity, the ADR-0064 storage fields (per-bound precision, `valid_to_state`, attestation bounds, start basis), and the master blueprint §109.2 mutation algorithm. The algorithm makes an explicit, database-enforced decision about recorded-time updates.
- **Baseline:** the pilot `canonical_fact_version` row holds two `tstzrange` columns under the two-range GiST exclusion, plus four separate timestamps. The pilot commit splits and closes intervals under a slot lock. It does not have:
  - valid-time precision or time zone;
  - an end state (`NULL` upper bound means open);
  - attestation bounds;
  - a start basis or succession guard;
  - a rule for superseding an information state;
  - a database backstop for the F0007 answer envelope;
  - a database rule that the recorded close is the only permitted update.
  Split remainders take the new proposal's receipt timestamps rather than their predecessor's.
- **Target:**
  - all 46 story acceptance criteria pass;
  - the four §115.4 bitemporal proof cases pass on PostgreSQL under the new contract: retroactive change, concurrent change, interval splitting, and distinct received and accepted times;
  - every pilot version reads back unchanged.
- **Evidence:** the later feature run produces real PostgreSQL commits, reads at the coordinate grid, concurrency races, a negative fixture for each refusal code, and migration up/down/up on seeded pilot data. Planning checks do not establish runtime delivery.

## Problem Statement

An endorsement effective June 1, issued June 10, received June 12 and accepted after review on June 14 is the core v0.1 temporal case (§87). Each kind of time answers a different question. If they are merged, an underwriter is told the Brain knew the $5M limit before it did. If they are kept apart without precision, a date-only "June 1" becomes a UTC midnight that falls on May 31 in Chicago. Three further failures are possible:

- A policy that "ended at some point before this letter" can be stored as open-ended, so the Brain asserts that the policy still holds.
- A model-guessed date can close a known value.
- A scoped "not found on pages 1–3" can overwrite a known limit.

Each of these is cheap to prevent in the version row now and expensive to retrofit after F0009, F0010 and F0018 build on it (BLUEPRINT §4.11).

## Scope & Boundaries

**In Scope (Must, MVP):**

1. **Precision and zone (ADR-0064 §5, G1 decision 4).** Each valid-time bound carries its granularity (`YEAR`, `QUARTER`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`) and the IANA time zone it was resolved in. A bound must be truncated to its granularity in that zone. The caller (the template route now, F0016 later) applies document conventions such as "12:01 a.m. standard time at the insured's address". F0008 validates the result and stores it.
2. **End state and attestation (ADR-0064 §5, G1 decision 3).**
   - The end state is `valid_to_state` ∈ {`OPEN`, `BOUNDED`, `UNKNOWN`}.
   - An `UNKNOWN` end requires `attested_to`: the date of the document that says the fact ended.
   - `attested_from` is the earliest dated evidence document.
   - A start is never widened to minus infinity. An unknown start with dated evidence is floored at `attested_from` and marked as such (EX-SEM-004). With no dated evidence it is refused with `START_UNATTESTED`.
3. **Mutation algorithm (§109.2 steps 3–7).**
   - Validate ranges and conventions.
   - Split affected valid-time intervals, close the recorded visibility of superseded beliefs, and insert the new recorded view.
   - Preserve the payloads, evidence and timestamps of unaffected intervals.
   - Commit fact rows, change rows, review linkage, audit and outbox in one transaction.
   - The explicit §109.2 decision: closing the recorded upper bound of a current version is the only permitted update to a historical version, and the database enforces it.
4. **Integrity under concurrency (ADR-0008, §15).**
   - The two-range exclusion holds per F0007 slot, and per member for MULTI members.
   - Concurrent commits produce exactly one accepted state at every coordinate.
   - The database rejects a fact-answer envelope whose state and value disagree (the F0007 handoff).
5. **Succession guard (ADR-0064 §7, G1 decision 1).**
   - Each version records how its start was obtained: `TEMPLATE_FIELD` or `HUMAN` (both grade `A`), or a time-mention grade `A`, `B` or `C`.
   - A proposal whose start basis is grade `C` cannot close or split an existing version and is refused with `SUCCESSION_START_UNANCHORED`.
   - Succession never reads model confidence.
   - Routing the refused proposal to review belongs to F0018.
6. **Information-state supersession (ADR-0039, 2026-11-08 amendment, G1 decision 2).**
   - The state is versioned like a value. A later state supersedes an earlier stored state without erasing it.
   - A `PRESENT` value can be closed only by another `PRESENT` value or by `EXPLICIT_NEGATIVE`. Every other state proposed against a `PRESENT` predecessor is refused with `STATE_SUPERSESSION_REFUSED`.
   - Removing a value is an F0010 correction or retraction.
7. **Two-coordinate reads.**
   - A read at (valid time, known time) returns exactly one version. When nothing is recorded, the internal reader returns `NOT_PROCESSED`.
   - Inside an unknown-end window, or before an attestation-floor start (EX-PC-014-B), the read returns a validity-unknown result, never the value and never absence.
   - *(Phase B clarification, operator-approved 2026-11-16: the existing GET keeps its pilot 404 when no version exists, and F0020 owns HTTP exposure of information states.)*
   - The existing `GET /facts/{factSlotId}?validAsOf&knownAsOf` keeps its pilot behaviour and adds the temporal fields. The full temporal query API is F0020's.
8. **Pilot compatibility.** Pilot versions and legacy slots are preserved and are never given fabricated precision, zone or basis. The migration is additive and survives up/down/up on seeded pilot data.

**Out of Scope:**

- Time-mention extraction, document time context, grade computation and re-resolution when an anchor arrives (F0016; ADR-0064 §§1–4). Replacing template effective dates with resolved mentions (after ADR-0064 acceptance, qualified by F0026).
- Change-type vocabulary and business meaning, for example `SUPERSEDED_BY_ENDORSEMENT` versus `RETRACTED_AS_ERRONEOUS_EXTRACTION` (F0010, ADR-0009). Provenance and correction lineage (F0009).
- Full commit orchestration, SourceAuthorityPolicy, review routing of refused successions, and row-level security enablement (F0018). Endorsement supersession on a real policy change (F0019). The temporal query and graph API (F0020).
- Declaring `temporal_kind` on ontology properties (F0012/F0013). F0008 stores `STATE` intervals; the version-row design must also hold `EVENT` points and `ETERNAL` facts without later DDL.
- Selecting document dates (F0004 service; human selection F0022). Projection lag and graph or vector projections (F0018, F0034).
- New UI, new permission grants, broker or MGA access.

## Personas

See [personas.md](personas.md). These are the existing personas Ingrid, Rosa, Priya and Mateo. They are not new access roles.

## Acceptance Criteria Overview

- Every bound states its precision and zone. A mis-truncated or zone-less bound is refused before any write. Date-only values round-trip without day drift.
- Ends are `OPEN`, `BOUNDED` or `UNKNOWN`. An unknown end never reads as current. A start never widens to minus infinity.
- A retroactive change splits intervals. Superseded beliefs stay readable at their recorded coordinates. A remainder keeps its predecessor's value, evidence and timestamps. Only the recorded close can update a historical row.
- Concurrent commits leave one accepted state at every coordinate. The database rejects overlaps and envelope state/value mismatches.
- An unanchored start never closes a value. A scoped absence never closes a known value.
- The §87 coordinates answer $2M, $5M, $2M and $5M. Pilot versions are unchanged.

The [acceptance checklist](acceptance-criteria-checklist.md) maps each criterion to its story and the runtime evidence it requires.

## UX / Screens

No new or materially changed UI. The surface is the existing canonical commit boundary and the existing fact read. F0020 owns the temporal query API, and F0022/F0023 own reviewer and user display.

## Screen Layouts (ASCII)

No UI: this feature changes version storage, the commit algorithm and the read contract only. It introduces no screen, zone or user editing flow.

## Data Requirements

- **Valid time:** start and end instants, the granularity of each bound, the IANA zone of each bound, `valid_to_state` (`OPEN`, `BOUNDED`, `UNKNOWN`), `attested_from`, `attested_to`, the latest positive attestation needed for the unknown-end window, and the start basis (`TEMPLATE_FIELD`, `HUMAN`, `MENTION_A`, `MENTION_B`, `MENTION_C`).
- **Recorded time:** `[canonical_accepted_at, closed_at)`. `source_received_at`, `artifact_created_at` and `assertion_created_at` are stored separately, and recorded time equals `canonical_accepted_at` (F0001-S0005).
- **Change linkage:** every superseded, split or closed version links to its successor through a change row with a reason. F0010 owns the reason vocabulary.
- **Answer:** `fact-answer/v1` for identity-v1 slots (F0007), with a database check that only `PRESENT` carries a value.
- **Ownership:** every row carries `tenant_id`, `knowledge_base_id` and the audit fields, bound to its slot's ownership through composite keys.
- **Legacy:** pilot versions keep their stored values. Legacy status is explicit, and the new columns are not backfilled with invented values.

## Role-Based Access

Commits keep the existing canonical-commit authority and the F0002 unit-of-work authorization. Reads keep the existing fact-read authority. Historical reads are authorized against current grants and cannot reinstate revoked access (ADR-0053). A cross-tenant or cross-KB slot, member or evidence reference is denied with zero rows written, and the denial does not reveal whether the target exists. Each accepted commit and each refusal is audited under the existing commit audit. No new grant, role or route is introduced.

## Success Criteria

- The later feature run passes all 46 ACs with observed evidence.
- Zero ambiguous coordinates in the concurrency fixture. Zero rows written by any refused proposal. Zero changed bytes in pilot versions after upgrade/downgrade/upgrade.
- At least 80% changed-code coverage, with real PostgreSQL tests as well as unit tests. No latency threshold is invented here; §114.2 budgets are measured later.

## Risks & Assumptions

- ADR-0007 and ADR-0008 are Accepted. ADR-0064 and ADR-0039 are Proposed with operator direction. F0008 implements their v0.1 storage and contract portions and does not formally accept them.
- **G1 decisions (2026-11-16):**
  1. Store the start basis. A template field or a human date is grade `A`, and grade `C` cannot close.
  2. A `PRESENT` value closes only to `PRESENT` or `EXPLICIT_NEGATIVE`.
  3. An unknown start with no dated evidence is refused with `START_UNATTESTED`.
  4. The caller supplies the IANA zone, and F0008 validates truncation in that zone.
- **Assumption A1:** identity-v1 slots require the new temporal fields on commit. Legacy pilot slots keep the pilot request shape and are labelled legacy, with no fabricated values (the F0007 pattern).
- **Assumption A2:** until F0012/F0013 declare `temporal_kind`, every slot is treated as `STATE`.
- **Assumption A3:** a commit is a full version write, with no partial bound updates. Changing only an end is a new version that closes the old one.
- **Assumption A4:** if a start is unknown but the evidence is dated, the start is floored at `attested_from` and marked as an attestation floor (EX-SEM-004). It is not a resolved start, so like grade `C` it cannot close or split a predecessor.
- **Risk:** in v0.1 most documents are undated, so unknown-start commits will usually be refused. That is the intended safe behaviour. F0022's human date selection and F0016's candidates relieve it later.
- **Phase B owns:**
  - the physical unknown-end representation inside the exclusion constraint (ADR-0064 recommends closing at `attested_to`);
  - the immutability trigger;
  - the envelope backstop;
  - the request and response contract changes;
  - the reconciliation of `canonical_relationship_version` (master blueprint §78) with F0007's RELATIONSHIP slots;
  - migration and rollback.

## Dependencies

Direct dependencies, both delivered:

- [F0003](../archive/F0003-postgresql-persistence/README.md): PostgreSQL, range types, table ownership and safe migrations.
- [F0007](../archive/F0007-factslot-model/README.md): slot identity, MULTI member slots and the answer envelope.

The F0001 pilot supplies the existing version table, commit service and read route. F0002 supplies authorization and audit, and F0004 supplies document-date candidates and selection.

Downstream consumers: F0009, F0010, F0018 and F0020 (direct `depends_on`), and then F0019, F0025 and F0065. Their undelivered implementations do not block F0008. Dependency evidence and audit-pending notes are in the plan run's `artifact-trace.md`.

## Related Stories

| Story | Outcome | ACs |
|---|---|---|
| [F0008-S0001](F0008-S0001-record-valid-time-precision-and-zone.md) | Each bound states its granularity and zone, and dates never drift | 6 |
| [F0008-S0002](F0008-S0002-distinguish-open-bounded-and-unknown-ends.md) | Open, bounded and unknown ends are kept distinct, with attestation bounds | 7 |
| [F0008-S0003](F0008-S0003-split-intervals-and-close-recorded-time.md) | Retroactive changes split intervals, and the recorded close is the only update | 7 |
| [F0008-S0004](F0008-S0004-enforce-temporal-integrity-under-concurrency.md) | One accepted state at every coordinate, with database backstops | 6 |
| [F0008-S0005](F0008-S0005-guard-succession-by-start-basis-and-state.md) | Unanchored starts and scoped absences never close a known value | 7 |
| [F0008-S0006](F0008-S0006-resolve-facts-at-a-valid-and-recorded-coordinate.md) | One answer per (valid, known) coordinate, including validity-unknown | 7 |
| [F0008-S0007](F0008-S0007-preserve-pilot-versions-through-migration.md) | Pilot versions are unchanged, and the migration is reversible | 6 |

## Rollout & Enablement

Before implementation, Phase B must specify:

- the additive migration and the immutability trigger;
- the unknown-end representation;
- the commit request and response changes;
- the read-contract additions;
- legacy handling and rollback.

No producer is activated and no route is added. Reuse the synthetic EX-GL-001 endorsement case, the §87 coordinates and EX-SEM-003/004, and keep development fixtures outside the frozen holdout.

## Source Traceability

- [BLUEPRINT](../../BLUEPRINT.md) §§1.4, 4.11, 4.14.
- [Master blueprint](../../architecture/master-blueprint.md) §§14, 15, 16, 87, 107.4, 109.2, 115.4.
- Accepted: [ADR-0007](../../architecture/decisions/ADR-0007-full-bitemporality.md), [ADR-0008](../../architecture/decisions/ADR-0008-database-level-temporal-integrity.md), [ADR-0077](../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md).
- Proposed: [ADR-0064](../../architecture/decisions/ADR-0064-time-interpretation-and-valid-time-precision.md), and [ADR-0039](../../architecture/decisions/ADR-0039-typed-insurance-values-and-completeness.md) with its decisions recorded.
- The dated amendments in the [README](README.md).
- Examples: [EX-SEM-003 and EX-SEM-004](../../examples/statements-time-and-governance.md#time-interpretation).

No external business authority or new insurance rule is asserted.
