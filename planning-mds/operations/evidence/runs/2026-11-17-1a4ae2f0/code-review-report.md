# Feature Code Review Report

Feature: F0008 — Bitemporal canonical facts (run `2026-11-17-1a4ae2f0`)

- Role: Code Reviewer
- Reviewer: Claude (Opus 5.5) / Code Reviewer
- Date: 2026-11-17
- Result: APPROVED
- Base: `origin/main` 2badb9a; head: working tree of `feature/F0008-bitemporal-canonical-facts`

## Summary

- Assessment: APPROVED
- Files reviewed: 12 production files (5 new: `brain_domain/temporal.py`, `brain_temporal/bounds.py`, `attestation.py`, `reader.py`, migration `0014`; 7 modified) and 21 test, fixture and CI files
- Issues found: Critical 0, High 0, Medium 0, Low 2 (both fixed in this cycle), Informational 3

## Vertical Slice Completeness

| Layer | Complete | Notes |
|---|---|---|
| Domain | Yes | `Granularity`, `EndState`, `StartBasis`, `TemporalKind`, `Bound`, `DocumentDate`, `TemporalProposal`, `VersionTemporal` and the ten reason codes, as in the plan's signatures |
| Application | Yes | Bounds/zone/truncation, attestation derivation and placement (D3/D4), the v1 commit path with guards and remainders (D5/D8), the legacy timestamp/review-linkage fix, and the D9 reader |
| Persistence | Yes | 16 columns, CHECKs, the insert guard, close-only, no-delete/no-truncate and change append-only triggers, preflight and downgrade guard; repository mapping and the new queries |
| API | Yes | Additive request block, read fields, the `FactValidityUnknown` variant, 422 codes and 409 `temporal_conflict`. No new route |
| Frontend / AI | N/A | Not in scope |
| Tests | Yes | 46/46 ACs mapped (`test-plan.md`). Unit, contract-example, PostgreSQL integration, concurrency and migration suites |
| Deployability | Yes | `deployability-check.md`; CI step added |

## Findings

- Critical: none
- High: none
- Medium: none
- Low:
  - **CR-L1 (fixed).** `brain_temporal/bounds.py` mapped a malformed or non-string bound instant, and extra bound keys, to `end_state_invalid`. That code describes end states, not a structural fault. These now raise the existing `InvalidRangeError`, which the API returns as a 400 `invalid_range` with a generic message and no echo of the input. A naive instant stays `time_zone_invalid` (S0001 AC1). New unit cases: `test_structurally_malformed_bounds_are_invalid_ranges_not_temporal_reasons`.
  - **CR-L2 (fixed, shared with Security SEC-F8-01).** The commit route's non-exclusion `IntegrityError` branch passed `str(exc)` into the 409 detail. With the new CHECKs and triggers, that text can quote the failing row. The detail is now omitted. Test: `test_other_integrity_errors_do_not_echo_database_text`.
- Informational:
  - **CR-I1.** `brain-api.yaml` `FactVersion` still describes `valid`/`recorded` range objects, while the runtime has returned `valid_start`/`valid_end`/`recorded_start`/`recorded_end` since F0001. This predates F0008 and is out of its scope; it is logged as a follow-up.
  - **CR-I2.** `ADR-0078 D4` wording "highest sequence that is not a clear" is implemented as "the highest sequence, where a clear leaves the document undated". This matches F0004's own read. Recommend the Architect align the ADR sentence at acceptance.
  - **CR-I3.** Python `zoneinfo` (tzdata 2026e) and PostgreSQL (2025b) differ. The database trigger is authoritative as D2 requires, and no fixture zone differs for the instants used. A future zone rule change could make the service accept a bound that the trigger refuses. That fails closed as a 409 `concurrent_commit` with nothing written, which is safe but not a 422 code. This is a deployment-hygiene follow-up: pin tzdata together.

## Pattern Compliance

- **Clean architecture:**
  - `brain_domain` has no I/O;
  - `brain_temporal` depends only on repository protocols;
  - `brain_persistence` implements them;
  - the API composes them inside `AuthorizationExecution.mutate`/`read`.
- **SOLID:**
  - the commit service splits the legacy and v1 paths into separate methods with shared helpers (`_remainder`, `_finish`);
  - the guards (`_guard`, `_is_end_revision`) and the remainder planning (`_remainders`) are small, pure-ish and unit-tested.
- **SOLUTION-PATTERNS:**
  - ProblemDetails with code-only 422s;
  - the same-UoW authorization facade;
  - append-only audit through the existing decision record;
  - composite ownership keys (the self-FK carries `tenant_id`/`knowledge_base_id`).
- **Immutability is in the database:** the D5 trigger compares `to_jsonb(NEW) - 'recorded'` with OLD, so a column added later is protected automatically. The tests probe 23 columns.
- **Trigger naming** keeps 0007's `owner_immutable` firing first; the existing ownership negatives are unchanged.

## Acceptance Criteria

- 46/46 ACs have observed passing tests (`test-execution-report.md`).
- Edge cases handled:
  - DST spring and fall;
  - the repeated fall-back hour;
  - `Etc/GMT+6`;
  - a cleared date selection;
  - an UNKNOWN end whose positive evidence postdates the ending document;
  - a right remainder clipping `validity_unknown_from`;
  - an end revision against a floored start;
  - a legacy predecessor on an identity-v1 slot, which keeps legacy remainders with lineage.
- Errors are covered by each refusal code; `23P01` → `temporal_conflict`; non-exclusion integrity errors return no detail.

## Recommendation

APPROVE. There is no blocking finding. Both Lows are fixed in this cycle and re-verified. The three informational items are follow-ups for the Architect (CR-I1, CR-I2) and DevOps (CR-I3) and do not block closeout.
