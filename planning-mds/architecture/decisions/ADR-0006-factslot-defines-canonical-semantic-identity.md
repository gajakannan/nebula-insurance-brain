# ADR-0006: FactSlot Defines Canonical Semantic Identity

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

**Decision:** Use first-class FactSlot.

**Use case:** EachOccurrence and GeneralAggregate limits are distinct semantic slots.

```text
Coverage
   │
   ├── FactSlot: EachOccurrence
   │        └── fact versions
   │
   └── FactSlot: GeneralAggregate
            └── fact versions
```

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0006` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
