# ADR-0012: Flexible Authoring, Normalized Runtime

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

**Decision:** YAML/JSONL/OKF/OWL are authoring/interchange; compile into normalized PostgreSQL runtime structures.

**Use case:** Domain expert reviews an ontology YAML pull request without editing DB rows.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0012` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
