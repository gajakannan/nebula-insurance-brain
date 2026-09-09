# F0001 — Repository and engineering foundation — Status

**Overall Status:** Draft — plan approved 2026-09-06 (Phase A at G3, Phase B at G5, plan run 2026-09-06-cdb5d8cb); ready for the feature action
**Last Updated:** 2026-09-06

## Story Checklist

| Story | Title | Status |
|-------|-------|--------|
| F0001-S0001 | Runtime roots and toolchain skeleton | [ ] Not Started |
| F0001-S0002 | Local runtime containers and dependency matrix | [ ] Not Started |
| F0001-S0003 | Proof: parse once, reinterpret twice, evidence resolves | [ ] Not Started |
| F0001-S0004 | Proof: native review round trip with lineage | [ ] Not Started |
| F0001-S0005 | Proof: bitemporal commit under retroactive and concurrent change | [ ] Not Started |
| F0001-S0006 | Proof: access boundaries, extension build, and restore | [ ] Not Started |
| F0001-S0007 | Record proof outcomes and settle the pre-build contracts | [ ] Not Started |

## Story × Role Progress

Cell states: `⬜` not started · `🔄` in progress · `✅` done · `—` not in scope. Review columns resolve to `PASS` / `FAIL` at signoff.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|-------|---------|----------|----|----|-------------|----------|--------|---------|
| F0001-S0001 | ⬜ | — | ⬜ | ⬜ | ⬜ | — | ⬜ | ⬜ Not Started |
| F0001-S0002 | ⬜ | — | — | ⬜ | ⬜ | — | ⬜ | ⬜ Not Started |
| F0001-S0003 | ⬜ | — | ⬜ | ⬜ | ⬜ | — | — | ⬜ Not Started |
| F0001-S0004 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0001-S0005 | ⬜ | — | — | ⬜ | ⬜ | — | — | ⬜ Not Started |
| F0001-S0006 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0001-S0007 | ⬜ | — | — | ⬜ | ⬜ | — | — | ⬜ Not Started |

## Backend Progress

- [ ] `engine/` uv workspace, FastAPI skeleton, Alembic, health endpoint
- [ ] Bitemporal commit proof harness and exclusion constraints
- [ ] Review round-trip proof harness (ReviewItem, ReviewBatch, ReviewDecision, decision transaction)
- [ ] Credential verifier, principal resolver, Casbin adapter proof
- [ ] Unit tests passing
- [ ] Integration tests passing

## AI Runtime Progress

- [ ] `neuron/` uv workspace and package skeleton
- [ ] Docling parse-once adapter and artifact bundle writer
- [ ] Docling-Graph interpretation adapter producing InterpretationResult
- [ ] Reinterpretation counter proves zero conversion calls

## Frontend Progress

- [ ] `experience/` root and toolchain
- [ ] Proof-scope Review Panel for S0004: artifact rail, rendered viewport with anchored regions, field list, batch submission (ADR-0057)

The full application shell remains F0021.

## Cross-Cutting

- [ ] docker-compose with PostgreSQL (pgvector, AGE), object store, authentik
- [ ] Dependency matrix pinned (`docker/DEPENDENCY-MATRIX.md`)
- [ ] Backup and restore drill executed and timed
- [ ] CI product-gates job runs runtime suites
- [ ] Runtime validation evidence recorded
- [ ] No TODOs remain in code

## Required Signoff Roles (Set in Planning)

Set by the Architect at Phase B (plan run `2026-09-06-cdb5d8cb`).

| Role | Required | Why Required | Set By | Date |
|------|----------|--------------|--------|------|
| Quality Engineer | Yes | Acceptance criteria and proof harness coverage | Architect | 2026-09-06 |
| Code Reviewer | Yes | Independent code quality review | Architect | 2026-09-06 |
| Security Reviewer | Yes | S0004 and S0006 touch identity, authorization, evidence access, and secrets | Architect | 2026-09-06 |
| DevOps | Yes | Containers, dependency matrix, CI, restore drill | Architect | 2026-09-06 |
| Architect | Yes | Proof outcomes settle Proposed ADRs (S0007); G7 binds ten capabilities | Architect | 2026-09-06 |

## Story Signoff Provenance

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|-------|------|----------|---------|----------|------|-------|

## Deferred Non-Blocking Follow-ups

| Follow-up | Why deferred | Tracking link | Owner |
|-----------|--------------|---------------|-------|

## Tracker Sync Checklist

- [x] `planning-mds/features/REGISTRY.md` status/path aligned (Active, compiled from the shard)
- [x] `planning-mds/features/ROADMAP.md` section aligned (Now)
- [x] `planning-mds/features/STORY-INDEX.md` regenerated (7 stories)
- [x] `planning-mds/BLUEPRINT.md` feature/story status links aligned
- [ ] Every required signoff role has story-level `PASS` entries with reviewer, date, and evidence

## Archival Criteria

All items above must be checked before moving this feature folder to `planning-mds/features/archive/`.
