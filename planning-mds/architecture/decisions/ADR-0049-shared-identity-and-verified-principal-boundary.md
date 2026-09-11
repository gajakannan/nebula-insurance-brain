# ADR-0049: Shared Identity and Verified Principal Boundary

## Status

- [ ] Proposed
- [x] Accepted (for the boundary F0001-S0006 proved; see Scope note)
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Settled:** 2026-09-10 (F0001-S0007), from F0001-S0006's live proof run on 2026-09-10
**Deciders:** Architect (record owner); backend-developer executed the proof
**Settled by:** F0001-S0006 (access boundaries, extension build, and restore); results recorded by F0001-S0007
**Source:** `planning-mds/architecture/master-blueprint.md` section 122

## Context

Proposed AuthX decision carried from the CRM reference architecture into the Brain (master blueprint sections 118 to 122). The CRM code establishes the reference contracts; the Brain implements the same contracts in its Python backend behind explicit adapters.

## Decision

**Accepted.** authentik default; verified `(iss, sub)` maps to stable internal principal for all Brain/companion storage access.

## Results (F0001-S0006, measured 2026-09-10)

- **Verify before read, always:** `OidcJwksVerifier` checks signature, issuer,
  audience, expiry, and not-before before `PrincipalResolver` ever runs, which
  itself runs before any route body executes. Missing bearer, malformed
  scheme, an unparseable token, an expired token, and a wrong-audience token
  all return 401 with the stable `unauthenticated` code — the internal reason
  (`expired`, `wrong_audience`, `invalid_signature`, `malformed`) is recorded
  only in the audit event, never in the response body.
  Tests: `engine/tests/security/test_credential_verification.py` (5 tests);
  `engine/packages/brain-security/tests/test_verification.py` (6 tests:
  expired, wrong audience, wrong issuer, wrong signature, not-yet-valid, and
  the valid-token happy path).
- **Stable internal principal, issuer-namespaced:** `(issuer, subject)` maps to
  one internal UUID, created on first sight and reused on every subsequent
  sight; the same `subject` string from two different issuers resolves to two
  different principals — raw-`sub` ownership never leaks across identity
  providers.
  Test: `engine/packages/brain-security/tests/test_principals.py::test_same_subject_from_a_different_issuer_resolves_to_a_different_principal`
  (added at S0006/S0007).
- **Revocation propagation measured, not assumed:** revoking a membership
  (`scripts/dev/revoke_membership.py`) is enforced on the very next request —
  measured **12.41ms** end to end through the HTTP layer — and a revoked grant
  cannot be reinstated by querying an earlier bitemporal coordinate on a fact
  (proposed ADR-0053's business rule).
  Test: `engine/tests/security/test_revocation_propagation.py` (2 tests).
- Two security scopes (tenants) with real principals were already provisioned
  and verified via ROPC at F0001-S0002 (`docker/authentik/blueprints/nebula-brain-dev.yaml`,
  `scripts/dev/seed_principals.py`); S0006 built the boundary proof on top of
  that identity substrate rather than re-proving authentik provisioning itself.

## Scope note

Master blueprint section 121.2's full carryover test matrix (12 categories:
credential verification, principal mapping, scope, parent/classification
conjunction, projection leakage, conversation access, review authority,
session transport, mutation continuity, delegation, policy parity, temporal
separation) is far broader than F0001-S0006's own stated scope, which this
story's own "Out of Scope" section already excludes ("the full permission
catalog and review boundaries" — F0002, F0018) and defers ("browser session
transport and the BFF decision" — F0021/ADR-0051). This ADR is **Accepted for
the boundary F0001-S0006 actually exercised**: credential verification (matrix
item 1, the subset listed above), principal mapping (item 2, including
issuer-namespacing), structural tenant/KB scope (item 3, proven jointly with
ADR-0050 below), and temporal non-reinstatement of a revoked grant (item 12,
partial). Items 4 to 11 remain open, owned by the features already scoped to
them (F0002, F0018, F0021, F0026) — not silently dropped.

## Consequences

- Shared behavior fixtures and schema contracts guard against semantic drift between the CRM reference and the Brain implementation.
- The verify-before-read ordering, issuer-namespaced principal identity, and
  real-time (uncached) revocation enforcement are now locked contracts other
  features build on.
- The broader section 121.2 matrix (see Scope note) remains open and owned by
  F0002/F0018/F0021/F0026 as already scoped in their own stories.

## References

- `planning-mds/architecture/master-blueprint.md` sections 118 to 123
- `engine/packages/brain-security/src/brain_security/verification.py`, `principals.py`
- `engine/tests/security/test_credential_verification.py`, `test_revocation_propagation.py`
- `scripts/dev/revoke_membership.py`, `seed_principals.py`
- `planning-mds/features/F0001-repository-and-engineering-foundation/STATUS.md` (Backend Progress, S0006)
