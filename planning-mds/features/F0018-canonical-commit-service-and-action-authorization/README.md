# F0018 — Canonical commit service + action authorization and policy-version audit

**Status:** Planned
**Phase:** v0.1B
**Roadmap:** Later

## Overview

The canonical commit service is the only write path to truth, with action authorization, source-authority evaluation, policy-version audit, transactional outbox, and projection delivery (sections 66, 107.1, 109).

Source: `planning-mds/architecture/master-blueprint.md` section 95 (epic roadmap) and section 115.3 (sequencing). Governing ADRs: [ADR-0002](../../architecture/decisions/ADR-0002-postgresql-is-the-authoritative-runtime-store.md), [ADR-0028](../../architecture/decisions/ADR-0028-temporal-owns-execution-brain-owns-semantic-state.md), [ADR-0041](../../architecture/decisions/ADR-0041-atomic-semantic-commit-and-projection-delivery.md), [ADR-0050](../../architecture/decisions/ADR-0050-native-policy-evaluation-and-resource-scope.md).

## Requirement-ownership amendment (2026-11-08)

The 2026-11-08 review of the master blueprint against the feature portfolio assigned these requirements to this feature (master blueprint section 106.3). Carry them into the PRD and stories when the feature is planned; the feature status is unchanged.

- **Dependencies:** F0002, F0007, F0008, F0009, F0010, F0011 (previously F0001).
- Own the ADR-0038 SourceAuthorityPolicy - versioned rules keyed by tenant, domain, FactSlot predicate, business context and effective interval; evaluated at commit and recorded in the audit. No applicable rule routes to review. The initial GL policy is operator-approved.
- Phase B settles the ADR-0042 authorization envelope and the PostgreSQL row-security pattern for tenant-owned tables, tested under the real application and worker roles (F0026 proves isolation).
- Carry master blueprint 88 hooks - outbox events reserve AGE projection IDs (F0034 implements) and the commit records derivation dependencies for derived results. Record ADR-0043 deletion and revocation events with tombstones.

## F0008 handoffs (recorded 2026-11-18, remediation run `2026-11-18-bce4909b`)

F0008 closed with two obligations assigned to F0018. Plan them in F0018 Phase A.

1. **SEC-F8-02 — non-superuser application role.** Locally and in CI the API connects as `brain`, a superuser, which can set `session_replication_role = replica` and skip the ADR-0078 D5 immutability triggers. F0018 introduces the application role (with RLS) under which those triggers must hold. Owner: Architect + DevOps. Severity Low, operator-accepted at F0008 G4.
2. **Durable refusal reason codes.** F0008 returns each temporal refusal as a 422 `code` and audits it as a `failed` authorization decision, but the AuthX decision record has no business-reason field. F0018 persists the reason per refusal together with routing refusals to review (ADR-0078 D8 note).

## Documents

The PRD, STATUS, GETTING-STARTED, and story files are authored by the `plan` action (Phase A and Phase B). Until then this folder is a reserved identifier; the feature shard is `planning-mds/kg-source/features/F0018.yaml`.

## Stories

| ID | Title | Status |
|----|-------|--------|

**Total Stories:** 0

## Docling-Graph scope amendment (2026-09-15) — withdrawn 2026-11-08

> **Withdrawn 2026-11-08.** The operator Rejected [ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md). Requirements below that are specific to Docling-Graph (templates, compiled Graph configuration, run-owned extraction graphs, upstream chunk/item provenance, Graph quality gates) no longer apply. Pipeline-neutral requirements (checkpoint before model, zero-reconversion reuse, honest evidence precision, idempotent authorized commit, isolation from canonical tables) still apply to the direct-baseline pipeline. The text is kept as history.

[ADR-0060](../../architecture/decisions/ADR-0060-docling-graph-document-pipeline-orchestration.md) governed this planned work until the operator Rejected it on 2026-11-08; see the withdrawal note above.

- Exercise duplicate upstream outputs and activity/job retries through canonical commit idempotency. Extraction graph writes, local deduplication, and upstream schema validation cannot bypass review, authorization, or bitemporal integrity.
