# ADR-0037: Human Corrections Append; They Do Not Rewrite Evidence

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

**Decision:** A correction produces a durable review decision and, when appropriate, a new assertion or canonical version linked to the prior assertion. Original source artifacts and original machine interpretations remain historically inspectable.

**Use case:** A model reads `$20M`; a reviewer corrects it to `$2M`. The Brain can reconstruct both the original interpretation and the human correction.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0037` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
