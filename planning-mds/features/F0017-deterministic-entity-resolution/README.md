# F0017 — Deterministic entity resolution

**Status:** Planned
**Phase:** v0.1A
**Roadmap:** Next

## Overview

Deterministic entity resolution with stable, scoped identifiers ships before probabilistic resolution (sections 53, 107.3). Extraction-local deduplication does not replace enterprise identity resolution.

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0025](../../architecture/decisions/ADR-0025-deterministic-er-ships-before-probabilistic-er.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0006, F0007, F0013 (previously F0001).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0017.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Treat upstream graph IDs as run-scoped references. Test that local node merges, synthesized parents, and identical text across tenants cannot merge enterprise identities or increase evidence precision.

## Statements, time, and governance scope amendment (2026-09-25)

[ADR-0066](../../architecture/decisions/ADR-0066-names-are-time-bounded-claims.md) govern this planned work. Carry these requirements into the feature PRD and stories when the feature is planned; the feature status is unchanged. Examples: [statements, time, and governance](../../examples/statements-time-and-governance.md).

- Resolve on identifiers first. An exact name match without an identifier creates a review pair and never merges. A name held by another compatible entity creates a shared-name pair. Roles such as "the named insured" point at entities and are not names (ADR-0066).
- **v0.1 scope guard (validate finding P-2):** this feature's Phase A admits only the storage fields, contract checks, and review/display hooks listed here. Alignment, automated deciders, fingerprint-driven scheduling, and time-mention resolution that replaces template fields stay in v0.2+ unless the operator amends the scope (BLUEPRINT §4.11).

## Account, party and role amendment (2026-10-10)

[ADR-0070](../../architecture/decisions/ADR-0070-account-party-and-role-model.md) (Proposed) governs this planned work. Carry these requirements into the PRD; the feature status is unchanged. Examples: [Cedar Bridge EX-PC-015 to EX-PC-019](../../examples/commercial-pc-account/cases.md).

- Resolve account identity and organization identity separately. Each insured or prospective insured organization has exactly one current account in a tenant, whichever system recorded it; other systems' identifiers are aliases on that account. Brokers, branches, carriers and MGAs have no accounts. A closed account does not block a new one; a merge of organizations or accounts states which survives and how the other's parent-account, ownership and role facts move.
- Broker branches and offices are organizations under a parent organization; resolve them as their own identities, never by matching the parent's name.
- Ownership and account parentage never merge identities. A joint venture remains its own organization and account.
- An account merge keeps every policy with exactly one owning account and carries broker-of-record and contact history across.
