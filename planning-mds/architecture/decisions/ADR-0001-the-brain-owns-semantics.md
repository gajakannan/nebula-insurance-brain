# ADR-0001: The Brain Owns Semantics

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

**Decision:** Nebula owns canonical semantic meaning. Docling, Docling-Graph, Label Studio, AGE, pgvector, Temporal, Cytoscape, AJV, Pydantic, and future reasoners are engines around it.

**Use case:** Replace an extraction library without replacing enterprise meaning.

```text
              BRAIN SEMANTIC CORE
             /    |    |    |    \
            /     |    |    |     \
       Docling   AGE  vector Temporal UI
```

## Consequences

- Accepted as a baseline decision on 2026-09-05. Change it only through a superseding ADR that links back here; never edit the decision text in place.
- Implementation features that depend on this decision cite `adr:0001` in their kg-source shards.
- Amended 2026-09-08 by [ADR-0057](ADR-0057-nebula-owns-the-native-evidence-review-panel.md): Label Studio is no longer among the engines around the semantic core. The human evidence review surface is native to Nebula. Every other engine named in the decision text is unaffected.

## References

- `planning-mds/architecture/master-blueprint.md` section 76
