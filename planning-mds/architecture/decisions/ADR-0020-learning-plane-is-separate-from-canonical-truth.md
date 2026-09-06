# ADR-0020: Learning Plane Is Separate From Canonical Truth

## Status

- [ ] Proposed
- [x] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline; the original decision is undated)
**Deciders:** Architecture baseline (master blueprint)
**Source:** `planning-mds/architecture/master-blueprint.md` section 76

## Context

Baseline architecture decision carried verbatim from the master blueprint. The surrounding design and the use case that motivated it are in the master blueprint sections referenced from `planning-mds/BLUEPRINT.md`; this record is the working copy that later ADRs supersede or refine.

## Decision

**Decision:** The Brain may learn autonomously, but promotion to authoritative knowledge is governed.

**Use case:** Repeated conversations suggest `BrokerSubmissionQuality` as a new abstraction.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0020` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
