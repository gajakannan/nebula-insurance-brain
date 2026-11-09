# ADR-0038: Semantic Authority and Source Ownership

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed under the section 106 decision posture until the proof below is recorded.
**Owner:** Architect (record); operator (approves each released source-authority policy)
**Proving features:** F0018 (policy evaluation at commit), F0024 (GL acceptance example)
**Formal acceptance:** the F0024 requested-versus-issued case passes through the F0018 commit path with the policy version recorded in the audit event, and the first GL policy release carries the operator's approval.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 107.1 and 116

## Context

The Brain is the authority for its governed semantic representation. It is not automatically the transactional system of record for issuance, claim payments, billing or broker management. No global rule such as "the newest document wins" or "endorsement always wins" is sufficient (section 107.1). The v0.1B stage in section 115.3 requires a source-resolution minimum, and section 117.1 item 1 requires a named owner.

## Decision

1. **Authority is field- and context-specific.** A versioned `SourceAuthorityPolicy` is keyed by tenant, domain, predicate (FactSlot), business context, effective interval and policy version. Each rule classifies a source family as `AUTHORITATIVE`, `ADVISORY` or `REQUESTED_TERMS` for that key.
2. **Assertions are never discarded by the policy.** The policy decides which assertion may be promoted to the canonical value. Every competing assertion stays in the assertion plane with its lineage.
3. **Confidence never substitutes for authority.** A higher extraction confidence does not promote a source that the policy classifies as advisory or requested terms.
4. **The commit records the basis.** F0018 evaluates the policy at commit and records the policy ID and version in the commit audit. A commit with no applicable rule goes to review; it is not auto-promoted.
5. **v0.1 GL policy (initial release, operator-approved):**

   | Information | Authoritative source family | Other families |
   | --- | --- | --- |
   | Issued limits, coverage terms, attached endorsements | Authenticated issued policy package | Submission and broker correspondence are `REQUESTED_TERMS` |
   | Issuance status and policy transaction identifier | Policy administration observation (none in v0.1; recorded as `NOT_PROCESSED`) | Documents are advisory and are reconciled against it later |
   | Underwriter judgment or exception | Authorized decision record with actor, authority, scope, reason and evidence | Not inferable from documents |

6. **Out of scope for v0.1:** jurisdiction-specific precedence, authenticity scoring, and multi-carrier rules. These come with their own policy releases.

## Consequences

- F0007 FactSlot definitions carry the predicate key that the policy references.
- F0018 owns policy storage, evaluation and audit; F0022 shows reviewers which policy rule applied.
- F0024 proves the acceptance example: a broker requests a $5M limit, the issued policy records $2M, both assertions stay, the answer shows requested versus issued terms, and the request is not promoted.

## References

- `planning-mds/architecture/master-blueprint.md` sections 106.3, 107.1, 115.3, 116 and 117.1
