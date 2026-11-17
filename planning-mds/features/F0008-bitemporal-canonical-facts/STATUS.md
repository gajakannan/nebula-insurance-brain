# F0008 — Bitemporal canonical facts — Status

**Overall Status:** Planned. Phase A was approved by the operator on 2026-11-16 and Phase B on 2026-11-17. Implementation has not started.
**Last Updated:** 2026-11-17
**Plan Run:** `2026-11-16-208a1193` (A+B, new)
**Phase A:** Approved 2026-11-16 (`approve-phase-a`, G3 PASS)
**Phase B:** Approved 2026-11-17 (`approve-phase-b`, G5)
**Implementation:** Not started

## Story Checklist

| Story | Title | Status |
|---|---|---|
| F0008-S0001 | Record valid-time precision and zone | Not Started |
| F0008-S0002 | Distinguish open, bounded and unknown ends | Not Started |
| F0008-S0003 | Split intervals and close recorded time | Not Started |
| F0008-S0004 | Enforce temporal integrity under concurrency | Not Started |
| F0008-S0005 | Guard succession by start basis and state | Not Started |
| F0008-S0006 | Resolve facts at a valid and recorded coordinate | Not Started |
| F0008-S0007 | Preserve pilot versions through migration | Not Started |

## Story × Role Progress

| Story | Backend | Frontend | AI | QA | Code Review | Security | DevOps | Overall |
|---|---|---|---|---|---|---|---|---|
| F0008-S0001 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0008-S0002 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0008-S0003 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0008-S0004 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0008-S0005 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0008-S0006 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |
| F0008-S0007 | not-started | not-in-scope | not-in-scope | not-started | not-started | not-started | not-started | not-started |

Frontend and AI are out of scope because F0008 has no UI and makes no model call. The Architect set the required roles at Phase B (below).

## Required Role Matrix

Set by the Architect at Phase B (G5), 2026-11-16.

| Role | Required | Why Required | Set By | Date |
|---|---|---|---|---|
| Quality Engineer | Yes | 46 ACs need PostgreSQL concurrency-grid, zone/DST, immutability-negative and migration evidence | Architect | 2026-11-16 |
| Code Reviewer | Yes | v1 commit path rewrite, new domain types, migration 0014 with triggers | Architect | 2026-11-16 |
| Security Reviewer | Yes | Attestation-date disclosure (T-08), close-only triggers under application roles, non-disclosing refusals, revoked-grant historical reads | Architect | 2026-11-16 |
| DevOps | Yes | Migration 0014 up/down/up on seeded pilot and F0007 data; revision coordination with F0011 | Architect | 2026-11-16 |
| Architect | Yes | ADR-0078 proof gates and KG reconciliation at feature G7 | Architect | 2026-11-16 |

## Story Signoff Provenance

Append-only history. The PM records the required reviewers' verdicts during the feature action.

| Story | Role | Reviewer | Verdict | Evidence | Date | Notes |
|---|---|---|---|---|---|---|

## Clarifications (G1, 2026-11-16)

1. **Start basis:** each version stores how its start was obtained. A template field or a human-entered date counts as grade `A`. Grade `C` cannot close or split a predecessor (`SUCCESSION_START_UNANCHORED`). Routing the refusal to review belongs to F0018.
2. **State supersession:** a `PRESENT` value can be closed only by `PRESENT` or `EXPLICIT_NEGATIVE`. Any other state against `PRESENT` is refused (`STATE_SUPERSESSION_REFUSED`). Removing a value is an F0010 correction or retraction.
3. **Unknown start:** with no dated evidence the commit is refused (`START_UNATTESTED`). A start is never widened to minus infinity.
4. **Time zone:** the caller supplies the IANA zone of each bound. F0008 validates truncation in that zone and stores it.
