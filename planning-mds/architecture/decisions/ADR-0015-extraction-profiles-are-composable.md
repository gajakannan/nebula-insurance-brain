# ADR-0015: Extraction Profiles Are Composable

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

**Decision:** Compose shared base modules with LOB/product-specific extensions.

**Use case:** `LossRunBase + PropertyExtension` versus `LossRunBase + CasualtyExtension`.

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0015` in their kg-source shards.

## References

- `planning-mds/architecture/master-blueprint.md` section 76

## Refinement — 2026-09-15

[ADR-0060](ADR-0060-docling-graph-document-pipeline-orchestration.md) proposes Docling-Graph document pipeline orchestration. F0015 compiles released Nebula profiles into trusted Docling-Graph Pydantic templates and pipeline configuration, with stable schema/configuration hashes and explicit unsupported-mapping failures. Nebula retains profile and ontology semantics.
