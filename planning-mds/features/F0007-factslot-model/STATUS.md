# F0007 — FactSlot model — Status

**Overall Status:** Planned. Phase A and Phase B approved by operator 2026-11-09; implementation not started.
**Last Updated:** 2026-11-09
**Plan Run:** `2026-11-09-60865e32` (A+B, new)
**Phase A:** Approved 2026-11-09 (`approve-phase-a`, G3 PASS)
**Phase B:** Approved 2026-11-09 (`approve-phase-b`; assembly plan, ADR-0077, three design schemas)
**Implementation:** Not started

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0007-S0001 | Resolve stable FactSlot identity | Not Started |
| F0007-S0002 | Distinguish single, multi-valued and relationship slots | Not Started |
| F0007-S0003 | Carry information state separately from value | Not Started |
| F0007-S0004 | Type money and identifiers | Not Started |
| F0007-S0005 | Define name FactSlots | Not Started |
| F0007-S0006 | Preserve pilot slots and ownership | Not Started |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0007-S0001 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0007-S0002 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0007-S0003 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0007-S0004 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0007-S0005 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0007-S0006 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |

Frontend and AI are out of scope: F0007 has no UI and no model call. The Architect set the required roles at Phase B (below).

## Required Role Matrix

Set by the Architect at Phase B (G5), 2026-11-09.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | 39 ACs need independent PostgreSQL, concurrency and negative-fixture evidence | Architect | 2026-11-09 |
| Code Reviewer | Yes | New application package, migration and commit-path change | Architect | 2026-11-09 |
| Security Reviewer | Yes | Ownership keys, derived restrictions, non-disclosing denial (T-08) and RLS handoff | Architect | 2026-11-09 |
| DevOps | Yes | Additive migration 0012 with up/down/up proof on seeded pilot data | Architect | 2026-11-09 |
| Architect | Yes | Identity, legacy compatibility and ADR-0077 proof gates | Architect | 2026-11-09 |

## Story Signoff Provenance

Append-only history. The PM records the required reviewers' verdicts during the feature action.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Clarifications (G1, 2026-11-09)

1. **Row security:** F0007 binds new rows to tenant/KB ownership with composite keys and immutability triggers. F0018 Phase B designs and enables RLS on all tenant-owned tables, F0007's included.
2. **Predicate identity:** an opaque, versioned predicate key with a minimal F0007 system-predicate set (the four name predicates plus test fixtures). F0012/F0013 register real predicates.
3. **Display name:** F0007 provides the hook only. The order of preference is an open decision owned by F0017/F0023.
