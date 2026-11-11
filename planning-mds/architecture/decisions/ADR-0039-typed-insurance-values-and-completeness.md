# ADR-0039: Typed Insurance Values and Completeness

## Status

- [x] Proposed
- [ ] Accepted
- [ ] Superseded
- [ ] Rejected

**Date:** 2026-09-05 (record created from the master blueprint baseline)
**Decision recorded:** 2026-11-08 by the operator (blueprint requirement-ownership amendment). Features plan against the decision below. The status stays Proposed under the section 106 decision posture until the proof below is recorded.
**Owner:** Architect
**Proving features:** F0007 (state and value carriers), F0011 (schemas), F0013 (GL value types), F0014 (expected package contents), F0023 (display)
**Formal acceptance:** F0011 schema fixtures cover every information state, qualified money and scoped identifiers, including failure cases; F0023 shows the missing-endorsement example as an incomplete package.
**F0007 review disposition (2026-11-10, PR-M1):** retaining Proposed is intentional. F0007 proves decisions 1–5 at the answer carrier and commit boundary; it does not prove decision 6's expected-package behavior or the F0011/F0023 acceptance gates above. F0011 owns schema publication and fixtures, F0014 owns expected package contents, and F0023 owns the incomplete-package display proof. Their architecture closeout must revisit formal acceptance with those proofs. F0007 completion and acceptance of ADR-0077 do not accept this broader ADR.
**Source:** `planning-mds/architecture/master-blueprint.md` sections 107.3, 107.4 and 116

## Context

A single null cannot distinguish "not yet interpreted", "searched and not found", "the source does not state it", and "the source explicitly says no". Insurance amounts need currency and basis, and identifiers are only meaningful inside the scheme that issued them (sections 107.3 and 107.4).

## Decision

1. **Information state is separate from the value.** Every FactSlot answer carries one of: `NOT_PROCESSED`, `NOT_FOUND`, `NOT_STATED`, `ILLEGIBLE`, `AMBIGUOUS`, `CONFLICTING`, `EXPLICIT_NEGATIVE`, `NOT_APPLICABLE`, or a present value. A value-bearing state is the only one with a value.
2. **Scope is mandatory for absence.** `NOT_FOUND` and `NOT_STATED` record the exact interpretation scope (content artifact version, profile release, pages/blocks) and never imply global absence.
3. **Access denial is not an information state.** Authorization decides visibility first. A response must not reveal restricted evidence through a missingness explanation.
4. **Money is qualified.** Exact decimal amount, ISO 4217 currency, and a basis qualifier where the predicate needs one (for example per occurrence, aggregate, per claim, deductible versus retention). Floating-point storage is not allowed.
5. **Identifiers are scoped.** An identifier is the tuple (issuer or scheme, identifier type, value), optionally with an effective interval. Two equal strings from different schemes are different identifiers.
6. **Package completeness is recorded.** A document profile declares the expected forms, pages and attachments. Each package records expected versus received, processing completeness and source freshness. An expected but missing component makes the package `INCOMPLETE`; it does not create a negative fact.

## Consequences

- F0007 defines the state-plus-value carrier on FactSlots; F0008 versions it bitemporally like any value.
- F0011 publishes JSON Schema definitions for the information state, qualified money and scoped identifiers.
- F0013 applies them to GL limits and identifiers; F0014 declares expected package contents; F0016 records the scope searched by each run.
- F0020/F0023 return and display the state, never a bare null; F0065 maps missing required inputs to `UNKNOWN` as already planned.
- Acceptance example: an exclusion endorsement listed in the forms schedule but not supplied gives an incomplete-package answer, not "exclusion absent".

## References

- `planning-mds/architecture/master-blueprint.md` sections 106.3, 107.3, 107.4 and 116
