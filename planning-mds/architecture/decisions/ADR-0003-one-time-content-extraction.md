# ADR-0003: One-Time Content Extraction

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

**Decision:** Each document version is physically parsed once. Persist canonical content artifacts. Future learning operates on persisted content.

**Use case:** Add `AttorneyRepresentation` six months later without reparsing 4,000 casualty loss-run PDFs.

```text
PDF
 │
 ▼
Parse Once
 │
 ▼
Canonical Content
 │
 ├── interpretation v1
 ├── interpretation v2
 ├── conversation learning
 └── future enrichment
```

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0003` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
