# F0010 — Change/retraction semantics

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Explicit change semantics distinguish a legitimate endorsement from a bad extraction correction (section 16).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0009](../../architecture/decisions/ADR-0009-explicit-change-semantics.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0008, F0009 (previously F0001).
- Carry ADR-0043 rule 2: source withdrawal, canonical retraction, access revocation and authorized deletion are four distinct event types with distinct effects. F0018 records them; F0026 proves deletion and restore.

## Shipped contract carry-in: ADR-0077/ADR-0078 (2026-11-21)

F0007 and F0008 shipped [ADR-0077](../../architecture/decisions/ADR-0077-factslot-identity-and-typed-answer-carriers.md) (FactSlot identity, `fact-answer/v1`) and [ADR-0078](../../architecture/decisions/ADR-0078-bitemporal-version-contract-and-close-only-immutability.md) (`fact-temporal/v1`, close-only versions). Both are Accepted. The handoffs below come from those records' Consequences sections. Bind Phase B to the as-built contract (master blueprint sections 13 and 14, "As built"), not to the original sketch. The feature status is unchanged.

- F0010 owns the change-reason vocabulary. F0008 kept the existing seven values (ADR-0078 consequences).
- Information-state guard (ADR-0078 D8): a `PRESENT` predecessor can be superseded only by `PRESENT` or `EXPLICIT_NEGATIVE`, and anything else is refused with `state_supersession_refused`. Phase B must decide how a retraction of a wrongly extracted value is represented under this guard, by ending its validity or by a governed exception, and record it as an ADR-0078 amendment if the guard changes.
- An end revision, meaning the same answer, start and basis with only the end changed, is not a succession. A retraction design must keep that distinction.

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0010.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
