# F0009 — Provenance + human-correction lineage — Status

**Overall Status:** Planned
**Last Updated:** 2026-11-24
**Plan Run:** `2026-11-24-bfdbbf04`
**Phase A:** Approved 2026-11-24 — operator token `approve-phase-a`
**Phase B:** Approved 2026-11-24 — exact operator token `approve-phase-b`; G5 journal/manifest records post-approval validation/publication
**Phase B rework:** Run `2026-11-24-c32acf46` approved 2026-11-24 (`approve-phase-b`). It resolves plan-review 2026-11-24-2af6f972 PR-H1/PR-H2 and supersedes the Phase B approval of `2026-11-24-bfdbbf04`.
**Implementation:** Not Started; 0/6 stories, 0/41 ACs proven

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0009-S0001 | [Reconstruct source provenance](F0009-S0001-reconstruct-source-provenance.md) | Not Started |
| F0009-S0002 | [Append auditable human corrections](F0009-S0002-append-auditable-human-corrections.md) | Not Started |
| F0009-S0003 | [Trace temporal version lineage](F0009-S0003-trace-temporal-version-lineage.md) | Not Started |
| F0009-S0004 | [Enforce current authority across lineage](F0009-S0004-enforce-current-authority-across-lineage.md) | Not Started |
| F0009-S0005 | [Reserve a learning-candidate reference](F0009-S0005-reserve-learning-candidate-reference.md) | Not Started |
| F0009-S0006 | [Prove compatible lineage delivery](F0009-S0006-prove-compatible-lineage-delivery.md) | Not Started |

## Story × Role Progress

⬜ = not started; — = outside proposed scope. Architect has set required roles; no runtime work has started.

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0009-S0001 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0009-S0002 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0009-S0003 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0009-S0004 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0009-S0005 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |
| F0009-S0006 | ⬜ | — | — | ⬜ | ⬜ | ⬜ | ⬜ | ⬜ Not Started |

## Backend Progress

- [ ] Internal scoped provenance reader with explicit completeness.
- [ ] Durable correction/decision lineage and future-learning reference.
- [ ] Temporal split/change/ending-source traversal without canonical mutation.
- [ ] Current-authority checks and non-disclosing refusal at every boundary.
- [ ] Additive persistence/contract integration and rollback proof.

## Frontend / AI Progress

N/A — no new UI, model calls, parsing, extraction producer or learning behavior.

## Cross-Cutting

- [ ] Real PostgreSQL proof of atomicity, races, ownership and rollback.
- [ ] F0011 consumer/contract inventory and conformance where applicable.
- [ ] At least 80% changed executable-code coverage and exact AC evidence.
- [ ] Required reviews and feature completion approval in a later feature action.

## Required Signoff Roles (Set in Planning)

Architect set the matrix below for the future runtime-bearing, security-sensitive feature. No runtime signoff has occurred.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | All ACs and PostgreSQL/coverage proof | Architect | 2026-11-24 |
| Code Reviewer | Yes | Independent correctness/regression review | Architect | 2026-11-24 |
| Security Reviewer | Yes | Sensitive evidence traversal and current-authority checks | Architect | 2026-11-24 |
| DevOps | Yes | Runtime-bearing persistence and rollback | Architect | 2026-11-24 |
| Architect | Yes | Shared lineage/contract semantics and ADR proof gates | Architect | 2026-11-24 |

## Story Signoff Provenance

Append-only; no implementation or review provenance exists yet. Actual passing evidence must live in the later feature run.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Deferred Scope / Handoffs

These are deliberate feature boundaries, not completed residual findings: F0010 owns retraction/change semantics; F0018 owns complete canonical orchestration and RLS; F0020 owns new public provenance/history APIs; F0022/F0023 own display; F0026 owns benchmark governance; F0041 owns learning. See [PRD](PRD.md#scope--boundaries).

## Closeout Summary

Not eligible for closeout/archive. No feature implementation or completion approval exists.

## Tracker Sync Checklist

- [x] REGISTRY/ROADMAP retained at Planned / Now; generated regions are untouched by PM.
- [x] STORY-INDEX regenerated after adding the six stories.
- [x] BLUEPRINT §3 links the six Not Started stories and approved requirements.
- [x] Story and tracker validators pass before G2.
- [x] Architect removed the reserved KG exclusion, completed source bindings and passed G4 compile/drift validation.
- [x] Explicit G3 and G5 operator approval tokens recorded; G5 automated publication is authoritative in the run journal/manifest.
