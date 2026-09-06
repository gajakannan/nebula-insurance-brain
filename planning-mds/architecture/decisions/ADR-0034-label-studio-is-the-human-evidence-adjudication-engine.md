# ADR-0034: Label Studio Is the Human Evidence-Adjudication Engine

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

**Decision:** Use Label Studio directly for evidence-oriented annotation, review, and correction rather than rebuilding that specialist UX in Nebula.

**Boundary:** Label Studio owns task presentation and annotation workflow. Nebula owns `ReviewItem`, `ReviewDecision`, provenance, audit, semantic commits, and canonical truth.

**Use case:** A casualty loss-run entity was extracted from page 7 with 0.61 confidence. The reviewer sees the exact source region and predicted entity in Label Studio, corrects it, and Nebula records the correction without mutating the original content artifact or original machine assertion.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0034` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
