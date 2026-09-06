# ADR-0035: Interpretation Basis Is First-Class

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

**Decision:** Preserve `EXPLICIT`, `INFERRED`, and `AMBIGUOUS` interpretation basis independently from `ASSERTED`, `OBSERVED`, and `DERIVED` fact modes.

**Rationale:** Fact mode answers what kind of knowledge is represented. Interpretation basis answers how directly the evidence supports that interpretation.

**Use case:** A relationship between a claim and a recurring plumbing issue is inferred from several passages rather than explicitly written in one sentence.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0035` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
