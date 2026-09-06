# ADR-0036: Nebula Keeps a Native Semantic UX; Onyx Is a Reference Implementation

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

**Decision:** Keep the planned native React/TypeScript Nebula frontend. Study Onyx's Chat implementation for conversation mechanics, but do not adopt Onyx as the Brain frontend or backend.

**Rationale:** Onyx's mature chat mechanics are useful, but its application contracts are coupled to its own retrieval, document, session, persona, and backend models. Nebula's product is semantic-first rather than chat-first.

**Use case:** Account 360 can expose a Chat panel using Onyx-inspired message branching and citations while remaining integrated with Nebula-native graph, temporal, evidence, and entity views.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0036` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
