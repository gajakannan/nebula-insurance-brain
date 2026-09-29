# F0002 — Acceptance criteria review

**Review scope:** Phase A requirement quality, not implementation acceptance.
**Date:** 2026-09-25

## Clarity and testability

- [x] Six individually scoped stories use observable Given/When/Then outcomes.
- [x] Tenant-scoped entity identity and explicit KB grants are user-confirmed.
- [x] Existing pilot roles are enumerated exhaustively; principal kind is not a role grant.
- [x] Every story has happy-path, denial/error, data validation and persistence expectations.
- [x] Every mutation story names an entry point, trusted authority, failure behavior, persisted result and audit requirement.
- [x] No UI is explicitly justified; render-only tests cannot establish backend completion.
- [x] Every semantic boundary has synthetic expected examples and owning story links.
- [x] Coverage floor is 80%; zero unauthorized outcomes in the scoped negative suite. No unmeasured production performance claim is made.
- [x] New business roles, transport/UI products and full canonical orchestration have explicit owning features.
- [x] Generated trackers and strict story validation pass at G2 (tracker: zero errors/warnings; two non-blocking INVEST dependency advisories reviewed as intentional sequencing).
- [x] User explicitly approved Phase A at G3 with `approve-phase-a` (2026-09-25).

## Acceptance coverage

| Requirement | Story | Expected cases |
|---|---|---|
| Structural ownership and tenant-scoped entity identity | S0001 | EX-AUTHX-001–003 |
| Verification before lookup and stable typed identity | S0002 | EX-AUTHX-004–006 |
| Current membership and scope intersection | S0003 | EX-AUTHX-002, 007–009 |
| Parent/classification/source/dependency conjunction | S0004 | EX-AUTHX-010–013 |
| Delegated and autonomous service authority | S0005 | EX-AUTHX-014–016 |
| Audit durability and existing consumer integration | S0006 | EX-AUTHX-017–018 and all applicable earlier cases |

## Phase B handoff checks

- [x] Define schema/API versions, migration/reconciliation and audit persistence behavior without relaxing the PRD.
- [x] Reconcile historical F0002 review-to-commit wording with F0018/F0022 ownership in the assembly plan and gate decisions.
- [x] Complete glossary/example coverage links and authored KG shards; compile generated projections.
- [x] Finalize required reviewer roles and validate all exit gates before requesting Phase B approval.

Unchecked boxes above are explicit later-phase work, not missing Phase A business decisions. All runtime acceptance criteria remain unproven until the feature action.

Phase B handoff items above were completed by Architect; G4 and all seven G5 automated checks passed. User architecture approval recorded with `approve-phase-b` on 2026-09-25. The six approved story files are unchanged.
