# F0062 — Advanced reasoners

**Status:** Planned
**Phase:** v0.4+
**Roadmap:** Later

## Overview

Additional reasoner providers such as OWL-DL, Datalog, and advanced scenario simulation plug in around the semantic core without owning meaning (sections 92 to 94).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0001](../../architecture/decisions/ADR-0001-the-brain-owns-semantics.md). Likely predecessors (inferred, confirm at Phase B): F0055.

## Documents

The [ontology planning handoff](../../architecture/ontology-planning-handoff.md) and proposed [ADR-0045](../../architecture/decisions/ADR-0045-ontology-release-compatibility.md) govern optional release-analysis providers. Report the supported fragment, input scope, bounds and unsupported/undecided results; bounded success does not establish unrestricted conservativity or consumer compatibility. An external reasoner store is a projection; PostgreSQL remains authoritative under ADR-0002. Select external vocabularies by domain need and usage rights. This is deferred planning context, not an engine selection or phase approval.

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0062.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0
