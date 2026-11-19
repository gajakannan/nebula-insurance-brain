# Record valid-time precision and zone

**Story ID:** F0008-S0001
**Feature:** F0008 — Bitemporal canonical facts
**Title:** Record valid-time precision and zone
**Priority:** Critical
**Phase:** MVP
**Status:** Done

## User Story

**As a** Priya the GL Underwriter
**I want** each valid-time bound of a canonical fact to record its granularity and the time zone it was resolved in
**So that** an endorsement effective "June 1" is June 1 where the insured is, and storage, display and export can never disagree about the day.

## Context & Background

ADR-0064 §5 requires every bound to store its granularity and be truncated to it. G1 decision 4 (2026-11-16) settles where the zone comes from: the caller supplies the IANA zone and F0008 validates truncation in it. The policy-period convention ("12:01 a.m. standard time at the address of the named insured") is applied by the caller: the template route now, F0016 later. EX-SEM-003 is the worked example.

## Acceptance Criteria

- [x] **AC1:** Every valid-time bound on an identity-v1 commit carries a granularity in {`YEAR`, `QUARTER`, `MONTH`, `DAY`, `HOUR`, `MINUTE`, `SECOND`} and an IANA zone name. A missing or unknown granularity is rejected with `GRANULARITY_INVALID`, and a missing or unknown zone with `TIME_ZONE_INVALID`. In both cases nothing is written.
- [x] **AC2:** A bound that is not truncated to its granularity in its zone is rejected with `BOUND_NOT_TRUNCATED`, and nothing is written. For example, a `DAY` bound of 2026-06-01T05:00Z with zone `America/Chicago` is accepted (CDT midnight). The same instant with zone `UTC` is rejected.
- [x] **AC3:** EX-SEM-003: a `MINUTE` start at 12:01 a.m. on 2026-07-01, standard time at an insured address in Chicago, commits and reads back with the identical instant, granularity and zone. Standard time stays at UTC-6 even in July, so the caller passes the fixed-offset IANA zone `Etc/GMT+6`, not `America/Chicago` (which would mean CDT), and the instant is 2026-07-01T06:01Z.
- [x] **AC4:** A `DAY` start of 2026-06-01 in `America/Chicago` reads back as 2026-06-01 in that zone, never 2026-05-31. A round trip through commit and read preserves the instant, granularity and zone exactly, for every granularity.
- [x] **AC5:** The start and the end of one version may have different granularities. Each is validated against its own granularity and zone.
- [x] **AC6:** The version-row design can represent a point (`EVENT`) and no valid time (`ETERNAL`) without further DDL. Until F0012/F0013 declare `temporal_kind`, every slot is treated as `STATE` (Assumption A2).

## Interaction Contract

| Surface / Entry Point | User Action | Editable State | Save / Mutation Result | Reload / Persistence Evidence | Roles / Status Constraints |
|---|---|---|---|---|---|
| Existing canonical commit boundary (`POST /facts/{factSlotId}/commits` and internal commit service) | Submit a version with bounds, granularities and zones | New versions only; existing versions are never edited | Version stored with each bound's instant, granularity and zone; refusal codes write nothing | `GET /facts/{factSlotId}?validAsOf&knownAsOf` returns the same instant, granularity and zone | Existing commit authority; identity-v1 slots require the fields; legacy slots per S0007 |

No new screen or route. F0020/F0023 own display.

## Data Requirements

Per bound: instant (`timestamptz`), granularity enum, IANA zone name. The zone database version used for validation is recorded in the feature run evidence.

## Role-Based Visibility

No new visibility. Bounds are returned only to principals with existing read authorization for the slot. Commits require the caller's existing canonical-commit authorization over the slot's knowledge base, evaluated in the F0002 unit of work before any validation result is returned. An unauthorized caller is denied without learning whether the slot exists.

## Non-Functional Expectations

Validation is deterministic and happens at the boundary before any write. The same input always gives the same result for a given zone database version.

## Dependencies

F0007 identity-v1 slots; the F0001 commit path; F0003 range types.

## Out of Scope

Interpreting time mentions, applying document conventions, fiscal or 52/53-week calendars (F0016, ADR-0064 §§2–3), and `temporal_kind` declaration (F0012/F0013).

## Questions & Assumptions

Phase B decides the physical columns, and whether truncation is also checked by a database constraint.

## Definition of Done

- [x] Six ACs pass, with positive and negative fixtures for each granularity, including a DST boundary.
- [x] The feature action records tests, coverage and the required signoffs.
