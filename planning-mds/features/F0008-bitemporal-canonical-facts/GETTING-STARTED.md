# F0008 — Getting Started

This page is for the feature-action developer and reviewers who implement and review the [assembly plan](feature-assembly-plan.md). The design is [ADR-0078](../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md) (Proposed).

## Prerequisites

- Local stack per F0001: `docker compose up -d` with `brain-postgres:18-pgvector-age`. `btree_gist` is already installed.
- `cd engine && uv sync`. The existing suites `tests/integration/test_bitemporal_commit.py` and the F0007 factslot suites must pass before you start.
- Once per clone: `git config core.hooksPath .githooks`.

## Read First

1. [PRD](PRD.md): the G1 decisions, assumptions A1–A4, and the Phase B read clarifications.
2. ADR-0078, D1–D10.
3. The pilot code:
   - `engine/packages/brain-temporal/src/brain_temporal/commit.py` and `ranges.py`;
   - `brain_persistence/repositories.py` (`close_recorded`, `resolve_at`);
   - migration `0003`.
4. [Contract examples](contract-examples.json): 20 structural cases.

## Where Things Go

| Concern | File |
|---|---|
| Temporal domain types and reason codes | `brain_domain/temporal.py` |
| Bound validation (zone, truncation) | `brain_temporal/bounds.py` |
| Attestation derivation | `brain_temporal/attestation.py` |
| v1 commit path and guards | `brain_temporal/commit.py` |
| Two-coordinate reader | `brain_temporal/reader.py` |
| Migration | `engine/migrations/versions/0014_f0008_bitemporal_contract.py` |
| API models and routes | `brain_api/schemas/facts.py`, `brain_api/routes/facts.py` |

## Gotchas

- **Zone ≠ convention.** "Standard time" means a fixed offset (`Etc/GMT+6` for Chicago), not `America/Chicago`. The caller picks the zone, and F0008 only checks truncation in it.
- **Two tzdata databases.** Python `zoneinfo` gives early errors, and the PostgreSQL trigger is authoritative. Record both versions in the run evidence. A disagreement is a defect to report, never something to paper over.
- **Close-only.** After 0014, the only UPDATE allowed on `canonical_fact_version` sets the finite recorded upper bound of an open row. Test fixtures that "fix up" rows with UPDATE will fail; build state through commits.
- **Remainder timestamps.** A remainder copies its predecessor's four timestamps and evidence. The pilot copied the proposal's; that defect is fixed on both paths.
- **End revision vs succession.** Restating the same answer with the same start and attestation and only a new end is an end revision. It is not blocked by the start-basis guard (ADR-0078 D8).
- **UNKNOWN end bound.** The stored upper bound is the *exclusive end* of the `attested_to` period, so for a `DAY` date it is midnight the next day in `attestation_zone`. Reads in `[validity_unknown_from, upper)` return validity-unknown.
- **Before the floor.** No row exists before an attestation floor. The reader derives validity-unknown from the next later version's `ATTESTATION_FLOOR` basis.
- **GET stays 404 when no version exists.** `NOT_PROCESSED` comes only from the internal reader (F0020 owns HTTP states). `FactValidityUnknown` is a 200 variant for identity-v1 slots only.
- **Legacy rows on identity-v1 slots.** F0007-era versions have `temporal_contract NULL`. A remainder split from one stays legacy (`split_of_version_id` set). New commits to the slot must still send the `temporal` block.
- **Migration numbering.** F0011 runs in parallel. Whichever lands second rebases its revision to follow the other.
- **Document dates are rare in v0.1.** Most fixtures need a controlled F0004 human selection (the verifier fixture used by the F0004 tests) to produce attestation.

## Proving It

See the validation matrix in the assembly plan. The ADR-0078 proof gates map one-to-one onto `test_temporal_*` modules. Keep the synthetic fixtures (EX-GL-001, §87, EX-SEM-003/004, EX-PC-006/014, EX-OWN-003) outside the frozen holdout.

## RLS and Security Notes

There are no new tables. The new triggers run as `SECURITY INVOKER`, and F0018 must confirm that they behave under the application and worker roles it introduces. The attestation documents join the GET's `additional_reads` (T-08), and refusals are audited with no detail text.
