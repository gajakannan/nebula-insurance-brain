# ADR-0004: Source, Content Artifact, and Interpretation Are Separately Versioned

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

**Decision:** Treat source version, parsed artifact version, and semantic interpretation run as separate identities.

**Use case:** Parser migration changes table coordinates while source remains unchanged.

```text
Source v1
   │
   ├── Content Artifact v1
   │      ├── Semantic Run A
   │      └── Semantic Run B
   │
   └── Content Artifact v2
          └── Semantic Run C
```

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0004` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
